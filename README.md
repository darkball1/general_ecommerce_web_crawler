# General E-Commerce Web Crawler

## Overview
The General E-Commerce Web Crawler is a powerful, asynchronous web scraping tool designed to efficiently crawl e-commerce websites. It combines the speed of asynchronous programming with the robustness of Selenium for JavaScript-heavy pages, making it ideal for extracting product URLs and other relevant information from online stores.

## Key Features
- **Asynchronous Crawling**: Utilizes `asyncio` and `aiohttp` for fast, concurrent crawling.
- **Selenium Integration**: Falls back to Selenium for JavaScript-rendered content.
- **Intelligent URL Prioritization**: Prioritizes URLs based on keywords and depth.
- **Robots.txt Compliance**: Respects robots.txt rules for ethical crawling.
- **Chunked File Writing**: Efficiently writes large amounts of data to disk.
- **Multi-domain Support**: Can crawl multiple domains simultaneously.
- **Depth Control**: Allows setting a maximum crawl depth.
- **Product URL Detection**: Identifies and saves product URLs.

## Requirements
- Python 3.7+
- `aiohttp`
- `beautifulsoup4`
- `selenium`
- `lxml`
- `chromedriver` (for Selenium)

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/darkball1/general_ecommerce_web_scroller.git
   cd general_ecommerce_web_scroller
   ```

2. Install the required packages:
   ```bash
   pip install aiohttp beautifulsoup4 selenium lxml
   ```

3. Install ChromeDriver:
   - Download the appropriate version of ChromeDriver for your Chrome browser from: https://sites.google.com/a/chromium.org/chromedriver/downloads
   - Extract the executable and add its location to your system's PATH.

## Usage
1. Open the `main.py` file and modify the `DOMAINS` list to include the e-commerce websites you want to crawl.

2. Run the crawler:
   ```bash
   python main.py
   ```

## Configuration
You can adjust the following parameters in the `main_crawler.py` file:
- `max_workers`: Number of concurrent workers (default: 10)
- `max_depth`: Maximum crawl depth (default: 300) - high value to handle pagination
- `product_url_threshold`: Number of product URLs to accumulate before saving (default: 10000)

## Output
- Product URLs are saved in chunked text files in the `final/` directory, organized by domain.
- A summary file `crawl_summary.txt` is generated with statistics for each crawled domain.
- Disallowed URLs are saved in `final/disallowed_urls.txt`.
- URLs that timed out with Selenium are saved in `final/selenium_timeout_urls.txt`.

## Customization
- Modify `PRODUCT_PATTERNS` in the script to adjust product URL detection.
- Edit `IGNORED_EXTENSIONS` to change which file types are skipped.
- Adjust `RESTRICT_LIST` to avoid crawling specific URL patterns.
- Modify `priority_keywords` in the `HybridWebCrawler` class to change URL prioritization.

## Ethical Considerations
- This crawler respects robots.txt files and includes rate limiting to avoid overloading servers.
- Ensure you have permission to crawl websites before using this tool.
- Be mindful of the load your crawler places on web servers and adjust the crawling speed if necessary.

## Suggested Improvements
- Implement Playwright as an alternative when Selenium encounters timeouts, providing a more robust solution for JavaScript-heavy pages.
- Enhance the URL prioritization mechanism to use backpropagation, allowing for dynamic updates based on the crawling results and success rates.
- Assign the same priority to elements located similarly in the DOM, improving the crawler’s efficiency in identifying potential product links.

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## Disclaimer
This tool is for educational and research purposes only. Use responsibly and in accordance with the terms of service of the websites you are crawling. The authors are not responsible for any misuse or damage caused by this tool.
