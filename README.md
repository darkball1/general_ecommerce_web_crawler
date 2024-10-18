# General E-Commerce Web Crawler

## Overview
This Web Crawler is a powerful, asynchronous web scraping tool designed to efficiently crawl e-commerce websites. It combines the speed of asynchronous programming with the robustness of Selenium for JavaScript-heavy pages, making it ideal for extracting product URLs and other relevant information from online stores.

## Key Features
- **Asynchronous Crawling**: Utilizes `asyncio` and `aiohttp` for fast, concurrent crawling.
- **Selenium Integration**: Falls back to Selenium for JavaScript-rendered content.
- **Intelligent URL Prioritization**: Prioritizes URLs based on keywords, depth, and likelihood of leading to product pages.
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
