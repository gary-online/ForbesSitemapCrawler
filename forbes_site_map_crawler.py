from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import json
from bs4 import BeautifulSoup
import datetime


class Crawler:
    def __init__(self, base_url, max_depth=2, max_threads=10, timeout=30):
        self.base_url = base_url
        self.max_depth = max_depth
        self.max_threads = max_threads
        self.timeout = timeout
        self.visited_urls = []
        self.sitemap = {}

    def visit_url(self, url, depth):
        if depth >= self.max_depth or url in self.visited_urls:
            return
        self.visited_urls.append(url)
        self.sitemap[url] = []

        # Send a GET request to the URL
        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
        except (requests.RequestException, ValueError):
            return

        # Use BeautifulSoup to parse the page source
        soup = BeautifulSoup(response.text, 'html.parser')
        self.sitemap[url] = [link.get('href') for link in soup.find_all(
            'a') if link.get('href') and link.get('href').startswith('http')]

        for link in self.sitemap[url]:
            self.visit_url(link, depth + 1)

    def crawl(self):
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            future_to_url = {executor.submit(self.visit_url, url, 0): url for url in [
                self.base_url]}
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    future.result()
                except Exception as exc:
                    print(f"{url} generated an exception: {str(exc)}")
                else:
                    print(f"{url} page is {len(self.sitemap[url])} links long")

    def save_sitemap(self, filepath):
        with open(filepath, 'w') as file:
            file.write(json.dumps(self.sitemap, indent=2))


current_time = datetime.datetime.now()
current_time_string = current_time.strftime("%Y-%m-%d %H-%M-%S")
crawler = Crawler('https://www.forbes.com', max_depth=2,
                  max_threads=10, timeout=20)
crawler.crawl()
crawler.save_sitemap(current_time_string + '_sitemap.json')
