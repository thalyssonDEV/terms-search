import logging
from urllib.parse import urljoin, urlparse # Manipulação e análise de URLs

import requests # Biblioteca Requisições HTTP
from bs4 import BeautifulSoup # Biblioteca para parsear HTML

class Crawler:
    """
    Responsável por rastrear páginas web a partir de uma URL inicial.
    Coleta o conteúdo HTML e mapeia os links, respeitando o domínio base.
    """
    def __init__(self, base_url):
        """
        Inicializa o Crawler.
        Args:
            base_url (str): A URL base que define o escopo do crawling.
                            O crawler não seguirá links para fora do domínio desta URL.
        """
        self.urls_visitadas = set()  # Armazena URLs já visitadas
        self.conteudo_paginas = {}   # Armazena o conteúdo HTML das páginas visitadas
        self.grafo_de_links = {}     # Armazena o grafo de links entre as páginas visitadas

        # Garantir base_url sem  '/' no final
        self.url_base_crawler = base_url.rstrip('/')
        # Extrai o domínio da URL base 
        self.dominio_base = urlparse(self.url_base_crawler).netloc
        if not self.dominio_base:
            logging.error(f"Não foi possível extrair o domínio da base_url: '{base_url}'. O crawling pode ser afetado.")

    def crawl(self, url_inicial): # Método para iniciar o crawling a partir de uma URL inicial

        url_inicial_normalizada = self._normalizar_url(url_inicial)

        # Verificando se a URL inicial está dentro do escopo permitido que é o domínio base
        if not self._esta_dentro_do_escopo(url_inicial_normalizada):
            logging.warning(
                f"A URL inicial '{url_inicial_normalizada}' está fora do escopo do domínio base '{self.dominio_base}'. "
                "Nenhuma página será rastreada."
            )
            return self.conteudo_paginas, self.grafo_de_links 

        logging.info(f"Iniciando crawling a partir de: {url_inicial_normalizada} (Domínio base: {self.dominio_base})")
        self._rastrear_pagina_recursivamente(url_inicial_normalizada) # Inicia o rastreamento recursivo
        return self.conteudo_paginas, self.grafo_de_links 

    def _normalizar_url(self, url):
        return url.split('#')[0].rstrip('/')

    def _esta_dentro_do_escopo(self, url):
        url_parseada = urlparse(url)
        # Compara o 'netloc' (domínio e porta) e o esquema do protocolo.
        return url_parseada.netloc == self.dominio_base and \
               url_parseada.scheme in ('http', 'https')

    def _rastrear_pagina_recursivamente(self, url_atual): # Ele entra na página e depois vai pra próxima e pega o conteudo e tals

        # A URL já deve estar normalizada ao chegar aqui
        if url_atual in self.urls_visitadas:
            return 

        # Verificação de escopo crucial antes de fazer a requisição
        if not self._esta_dentro_do_escopo(url_atual):
            logging.debug(f"Ignorando link fora do escopo definido: {url_atual}")
            return

        logging.info(f"Rastreando: {url_atual}")
        self.urls_visitadas.add(url_atual)

        html_conteudo_lower = self._buscar_conteudo_da_pagina(url_atual)
        if html_conteudo_lower is None:
            # Se falhou ao buscar marco como visitada pra não tentar de novo
            return

        self.conteudo_paginas[url_atual] = html_conteudo_lower
        self.grafo_de_links[url_atual] = set() # Inicializo o set de links para esta URL

        # Extrai os links da página e o método de extração já resolve URLs relativas
        links_encontrados = self._extrair_hyperlinks(html_conteudo_lower, url_atual)
        for link_url in links_encontrados:
            link_normalizado = self._normalizar_url(link_url) #
            if self._esta_dentro_do_escopo(link_normalizado): 
                self.grafo_de_links[url_atual].add(link_normalizado)
                # Chamada recursiva para os novos links encontrados
                self._rastrear_pagina_recursivamente(link_normalizado)
            else:
                logging.debug(f"Link extraído '{link_normalizado}' está fora do escopo, não será seguido.")
    
    def _buscar_conteudo_da_pagina_simples_demais(self, url):
        try:
            resposta = requests.get(url)
            return resposta.text.lower()
        except Exception as e:
            print(f"Algum erro ao buscar {url}: {e}") 
            return None

    def _extrair_hyperlinks(self, html_conteudo, url_pagina_atual): 
        soup = BeautifulSoup(html_conteudo, 'html.parser')
        links_de_saida = set()
        for tag_a in soup.find_all('a', href=True):
            href_valor = tag_a['href'].strip()

            if not href_valor or href_valor.startswith(('mailto:', '#', 'javascript:')):
                continue
            # Constrói a URL 
            url_completa = urljoin(url_pagina_atual, href_valor)
            url_completa_normalizada = self._normalizar_url(url_completa) 
            # Verifica se a URL está dentro do escopo
            if self._esta_dentro_do_escopo(url_completa_normalizada):
                links_de_saida.add(url_completa_normalizada)
        return links_de_saida