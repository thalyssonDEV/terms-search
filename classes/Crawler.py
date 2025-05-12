import logging
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

class Crawler:
    """
    Rastreia páginas recursivamente a partir de uma URL inicial,
    armazenando HTML e grafo de links, limitado ao domínio base.
    """
    def __init__(self, base_url): # Adicionado base_url
        self.visited = set()
        self.pages = {}  # Armazena url -> html_content (em minúsculas)
        self.links = {}  # Armazena url_origem -> set(url_destino)
        self.base_url = base_url
        self.base_domain = urlparse(base_url).netloc

    def crawl(self, start_url):
        # O método crawl agora recebe uma única URL inicial
        self._crawl_page(start_url)
        return self.pages, self.links

    def _is_within_domain(self, url):
        # Garante que o crawler não saia do domínio base
        return urlparse(url).netloc == self.base_domain

    def _crawl_page(self, url):
        # Normaliza a URL removendo fragmentos (#) antes de verificar/visitar
        normalized_url = url.split('#')[0]

        if normalized_url in self.visited:
            return
        
        # Verifica se a URL está dentro do domínio permitido ANTES de fazer a requisição
        if not self._is_within_domain(normalized_url):
            logging.info(f"Ignorando link externo ou fora do escopo: {normalized_url}")
            return

        logging.info(f"Crawling: {normalized_url}")
        self.visited.add(normalized_url)

        html_content = self._fetch_page(normalized_url)
        if html_content is None:
            return

        self.pages[normalized_url] = html_content # Conteúdo já em minúsculas
        
        # Extrai links. A extração já lida com urljoin usando o normalized_url como base.
        outgoing_links = self._extract_links(html_content, normalized_url)
        self.links[normalized_url] = outgoing_links

        for link in outgoing_links:
            # A verificação de domínio e visited será feita no início da chamada recursiva _crawl_page
            self._crawl_page(link)


    def _fetch_page(self, url):
        try:
            # Adiciona um user-agent para simular um navegador, algumas páginas podem bloquear requests sem ele
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 terms-search-crawler/1.0'}
            resp = requests.get(url, headers=headers, timeout=10) # Adicionado timeout
            resp.raise_for_status()
            # Converte o conteúdo para minúsculas ANTES de retornar
            return resp.text.lower()
        except requests.RequestException as e:
            logging.warning(f"Falha ao buscar {url}: {e}")
            return None

    def _extract_links(self, html, current_page_url): # html já estará em minúsculas
        soup = BeautifulSoup(html, 'html.parser')
        outgoing = set()
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href'].strip()
            if not href or href.startswith('mailto:'): # Ignora links vazios ou de email
                continue
            
            # Constrói URL absoluta a partir do link encontrado e da URL da página atual
            full_url = urljoin(current_page_url, href)
            # Remove fragmentos (#) da URL antes de adicionar
            full_url_no_fragment = full_url.split('#')[0]

            # Adiciona apenas se estiver no mesmo domínio e for http/https
            if urlparse(full_url_no_fragment).scheme in ('http', 'https') and self._is_within_domain(full_url_no_fragment):
                outgoing.add(full_url_no_fragment)
        return outgoing