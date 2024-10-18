import asyncio
from hybrid_web_crawler import HybridWebCrawler

# List of domains to be crawled
DOMAINS = [
    "https://www.blueapron.com",
    "https://www.casper.com",
    "https://www.dollarshaveclub.com",
    "https://www.brewedcoffee.com",
    "https://www.grove.co",
    "https://www.fabletics.com",
    "https://www.cuyana.com",
    "https://www.bakedbymelissa.com",
    "https://www.thesill.com",
    "https://www.puravidabracelets.com"
]

async def main():
    # Initialize the HybridWebCrawler with key parameters like max_depth and max_workers
    crawler = HybridWebCrawler(DOMAINS, max_workers=10, max_depth=300, product_url_threshold=10000)
    
    # Start crawling the provided domains
    await crawler.crawl_all()

if __name__ == "__main__":
    # Execute the main function asynchronously
    asyncio.run(main())
