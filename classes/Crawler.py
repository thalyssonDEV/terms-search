import logging
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

class Crawler:
    """
    Rastreia páginas recursivamente a partir de URLs iniciais,
    armazenando HTML e grafo de links.
    """
    def __init__(self):
        self.visited = set()
        self.pages = {}
        self.links = {}

    def crawl(self, start_urls):
        if isinstance(start_urls, str):
            start_urls = [start_urls]  # permite aceitar uma string única também

        for url in start_urls:
            self._crawl_page(url)
        return self.pages, self.links

    def _crawl_page(self, url):
        if url in self.visited:
            return
        logging.info(f"Crawling: {url}")
        self.visited.add(url)

        html = self._fetch_page(url)
        if html is None:
            return

        self.pages[url] = html
        outgoing = self._extract_links(html, url)
        self.links[url] = outgoing

        for link in outgoing:
            if link not in self.visited:
                self._crawl_page(link)

    def _fetch_page(self, url):
        try:
            resp = requests.get(url)
            resp.raise_for_status()
            return resp.text
        except requests.RequestException as e:
            logging.warning(f"Falha ao buscar {url}: {e}")
            return None

    def _extract_links(self, html, base_url):
        soup = BeautifulSoup(html, 'html.parser')
        outgoing = set()
        for a in soup.find_all('a', href=True):
            href = a['href'].split('#')[0]
            full = urljoin(base_url, href)
            if urlparse(full).scheme in ('http', 'https'):
                outgoing.add(full)
        return outgoing