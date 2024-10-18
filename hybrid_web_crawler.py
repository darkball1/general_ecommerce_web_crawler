import asyncio
import aiohttp
import re
import os
from urllib.parse import urljoin, urlparse, urldefrag
from bs4 import BeautifulSoup
from urllib import robotparser
from collections import defaultdict, deque
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from concurrent.futures import ThreadPoolExecutor
import time
from chunked_file_writer import ChunkedFileWriter  

# Define product URL patterns
PRODUCT_PATTERNS = [
    r'/product/',
    r'/products/',
    r'/item/',
    r'/items/',
    r'/p/',
    r'/[A-Za-z0-9-]+-p-\d+',
]

# Define priority keywords
PRIORITY_KEYWORDS = [
    'sale',
    'new',
    'best',
    'hot',
    'trending',
    'special',
    'limited',
    'collectible',
    'category',
    'categories',
    'collection',
    'shop',
    'store',
    'buy',
    'purchase'
]

# Define ignored file extensions
IGNORED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.pdf', '.css', '.js']

# Define restricted URLs
RESTRICT_LIST = [
    '/about', '/blog', '/news', '/contact', '/faq', '/terms', '/privacy',
    '/account', '/login', '/signup', '/cart', '/checkout', '/order', '/career', '/job'
]

USER_AGENT = 'CustomWebCrawler/1.0'


class HybridWebCrawler:
    def __init__(self, domains, max_workers=10, max_depth=3, product_url_threshold=10000):
        self.domains = domains
        self.max_workers = max_workers
        self.max_depth = max_depth
        self.visited_urls = set()
        self.product_urls = defaultdict(set)
        self.session = None
        self.robots_parsers = {}
        self.url_priorities = defaultdict(float)
        self.parent_child_map = defaultdict(set)
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.lock = asyncio.Lock()
        self.semaphore = asyncio.Semaphore(max_workers * 2)
        self.product_url_threshold = product_url_threshold
        self.product_url_buffer = defaultdict(deque)
        self.product_url_file_count = defaultdict(int)
        self.disallowed_urls = set()
        self.selenium_timeout_urls = set()
        self.initialize_domain_folders()

    # Initialize folders for all domains
    def initialize_domain_folders(self):
        for domain in self.domains:
            parsed_domain = urlparse(domain).netloc
            os.makedirs(f'final/{parsed_domain}', exist_ok=True)
        print("Initialized folders for all domains.")

    # Set up Chrome driver
    def setup_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument(f"user-agent={USER_AGENT}")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.page_load_strategy = 'eager'
        return webdriver.Chrome(options=chrome_options)

    # Assign priority to URLs    
    def assign_priority(self, url, depth=0):
        parsed_url = urlparse(url)
        path = parsed_url.path.lower()

        depth_factor = 1 / (1 + depth)
        
        # Assign higher priority to URLs containing priority keywords
        if any(keyword in path for keyword in PRIORITY_KEYWORDS):
            return 0.5 + depth_factor * 0.5
        
        # Assign highest priority to product URLs
        if self.is_product_url(url):
            return 1.0
        
        # Default priority for other URLs
        return depth_factor

    # Crawl all domains
    async def crawl_all(self):
        self.session = aiohttp.ClientSession(headers={'User-Agent': USER_AGENT})
        try:
            tasks = [self.crawl_domain(domain, depth=0) for domain in self.domains]
            await asyncio.gather(*tasks)
            
            # Save any remaining product URLs and create empty files for domains with no products
            for domain in self.domains:
                await self.save_product_urls(domain)
            
            print("All crawling completed.")
            for domain in self.domains:
                parsed_domain = urlparse(domain).netloc
                print(f"Total product URL files created for {parsed_domain}: {self.product_url_file_count[domain]}")
            
            
            await self.save_results()
        finally:
            await self.session.close()

    # Crawl a single domain
    async def crawl_domain(self, start_url, depth=0):
        self.robots_parsers[start_url] = await self.get_robots_parser(start_url)
        await self.crawl_url(start_url, parent_url=None, depth=depth)

    # Crawl a single URL
    async def crawl_url(self, url, parent_url=None, depth=0):
        if depth > self.max_depth:
            return

        url = urldefrag(url)[0]

        # Check if the URL has already been visited
        async with self.lock:
            if url in self.visited_urls:
                return
            self.visited_urls.add(url)

        print(f"Crawling: {url} (Depth: {depth})")

        if parent_url:
            self.parent_child_map[parent_url].add(url)

        self.url_priorities[url] = self.assign_priority(url)    
        domain = urlparse(url).netloc

        # Check if the URL is a product URL
        if self.is_product_url(url):
            print(f"Product URL: {url} (Depth: {depth})")
            await self.add_product_url(domain, url)
            self.url_priorities[url] = 1.0
            return

        if not await self.can_fetch(url):
            self.disallowed_urls.add(url)
            return
        
        try:
            async with self.semaphore:
                content = await self.get_page_content(url)
            links = self.get_links(url, content)
            product_links = [link for link in links if self.is_product_url(link)]
            
            # Check if any product links were found
            if not product_links:
                print(f"No links found, attempting with Selenium: {url}")
                content = await self.get_page_content_with_selenium(url)
                links = self.get_links(url, content)

            print(f"Found {len(links)} total links on {url}")

            # Sort links by priority
            sorted_links = sorted(links, key=self.assign_priority, reverse=True)

            tasks = [asyncio.create_task(self.crawl_url(link, url, depth + 1)) for link in sorted_links]
            await asyncio.gather(*tasks)

        except Exception as e:
            print(f"Error crawling {url}: {str(e)}")

    # Get page content
    async def get_page_content(self, url):
        async with self.session.get(url, timeout=30) as response:
            return await response.text()

    # Get page content with Selenium asynchronously
    async def get_page_content_with_selenium(self, url):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self.executor, self._get_page_content_with_selenium_sync, url)

    # Get page content with Selenium (synchronous version)
    def _get_page_content_with_selenium_sync(self, url):
        driver = self.setup_driver()
        try:
            driver.set_page_load_timeout(30)
            driver.get(url)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

            # Scroll to load lazy-loaded content
            last_height = driver.execute_script("return document.body.scrollHeight")
            while True:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)  # Wait for potential requests to complete
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

            return driver.page_source
        except TimeoutException:
            print(f"Selenium timeout occurred while loading: {url}")
            self.selenium_timeout_urls.add(url)
            return ""
        except Exception as e:
            print(f"Error loading {url} with Selenium: {str(e)}")
            return ""
        finally:
            driver.quit()

    # Get links from the HTML content
    def get_links(self, base_url, html_content):
        soup = BeautifulSoup(html_content, 'lxml')
        links = []
        for a_tag in soup.find_all('a', href=True):
            link = a_tag['href']
            full_url = urljoin(base_url, link)
            if self.is_valid_url(full_url, base_url) and self.should_crawl(full_url):
                links.append(full_url)
        return links

    # Check if the URL is valid
    def is_valid_url(self, url, base_url):
        parsed = urlparse(url)
        base_parsed = urlparse(base_url)
        return bool(parsed.netloc) and bool(parsed.scheme) and parsed.netloc == base_parsed.netloc

    # Check if the URL should be crawled
    def should_crawl(self, url):
        parsed_url = urlparse(url)
        path = parsed_url.path
        if any(path.startswith(restricted_path) for restricted_path in RESTRICT_LIST):
            return False
        _, ext = os.path.splitext(path)
        return ext.lower() not in IGNORED_EXTENSIONS

    # Check if the URL is a product URL
    def is_product_url(self, url):
        return any(re.search(pattern, url) for pattern in PRODUCT_PATTERNS)

    # Get robots.txt parser
    async def get_robots_parser(self, domain):
        rp = robotparser.RobotFileParser()
        robots_url = urljoin(domain, "/robots.txt")
        rp.set_url(robots_url)
        async with self.session.get(robots_url) as response:
            if response.status == 200:
                content = await response.text()
                rp.parse(content.splitlines())
        return rp

    # Check if url can be fetched using robots.txt
    async def can_fetch(self, url):
        domain = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
        if domain not in self.robots_parsers:
            self.robots_parsers[domain] = await self.get_robots_parser(domain)
        return self.robots_parsers[domain].can_fetch(USER_AGENT, url)

    # Add product URL
    async def add_product_url(self, domain, url):
        self.product_urls[domain].add(url)
        self.product_url_buffer[domain].append(url)
        
        if len(self.product_urls[domain]) >= self.product_url_threshold:
            await self.save_product_urls(domain)

    # Save product URLs to a file
    async def save_product_urls(self, domain):
        parsed_domain = urlparse(domain).netloc
        
        if not self.product_url_buffer[parsed_domain]:
            # Create an empty file to indicate the domain was processed
            with open(f'final/{parsed_domain}/processed.txt', 'w') as f:
                f.write(f"Processed domain: {domain}\nNo product URLs found.\n")
            return

        # Save product URLs to a file
        async with asyncio.Lock():
            writer = ChunkedFileWriter(f'final/{parsed_domain}/product_urls_{self.product_url_file_count[domain]:04d}')
            while self.product_url_buffer[parsed_domain]:
                url = self.product_url_buffer[parsed_domain].popleft()
                writer.write(f"{url}\n")
            writer.close()

        self.product_url_file_count[domain] += 1
        print(f"Saved {len(self.product_urls[parsed_domain])} product URLs for {parsed_domain}. Clearing set for continued processing.")
        self.product_urls[parsed_domain].clear()

    # Create a summary 
    async def save_results(self):
        # Save disallowed URLs
        with open('final/disallowed_urls.txt', 'w') as f:
            for url in self.disallowed_urls:
                f.write(f"{url}\n")

        # Save Selenium timeout URLs
        with open('final/selenium_timeout_urls.txt', 'w') as f:
            for url in self.selenium_timeout_urls:
                f.write(f"{url}\n")

        # Create a summary file
        with open('final/crawl_summary.txt', 'w') as f:
            for domain in self.domains:
                parsed_domain = urlparse(domain).netloc
                f.write(f"Domain: {parsed_domain}\n")
                f.write(f"  Total product URL files: {self.product_url_file_count[domain]}\n")
                f.write(f"  Total URLs crawled: {len([url for url in self.visited_urls if urlparse(url).netloc == parsed_domain])}\n")
                f.write("\n")
            f.write(f"Total unique URLs crawled across all domains: {len(self.visited_urls)}\n")
            f.write(f"Total disallowed URLs: {len(self.disallowed_urls)}\n")
            f.write(f"Total Selenium timeout URLs: {len(self.selenium_timeout_urls)}\n")
