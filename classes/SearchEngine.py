import re

class SearchEngine:
    """
    Processa páginas e links para ranquear termos.
    """
    def __init__(self, pages, links):
        self.pages = pages # Espera-se que o HTML aqui já esteja em minúsculas
        self.links = links # url_origem -> set(url_destino)
        self.incoming = self._compute_incoming_links()

    def _compute_incoming_links(self):
        incoming = {url: set() for url in self.pages}
        for src_url, outgoing_links_set in self.links.items():
            if src_url not in self.pages: # Garante que a página de origem foi rastreada
                continue
            for dest_url in outgoing_links_set:
                if dest_url in incoming: # Garante que a página de destino também foi rastreada
                    incoming[dest_url].add(src_url)
        return incoming

    def _score_page(self, url, term_pattern): # term_pattern já foi compilado com o termo em minúsculas
        # self-reference detectada?
        # Um link de 'url' para 'url' no conjunto de links de saída de 'url'
        self_ref = url in self.links.get(url, set())

        # Links recebidos total
        # O conjunto self.incoming[url] contém as URLs das páginas que linkam para 'url'
        # A tabela do exercício implica que a autoreferência CONTA para os links recebidos
        # e depois é penalizada. Se blade_runner.html tem um link para si mesmo,
        # e esse link é extraído, então blade_runner.html estará em self.incoming.get(url, set()).
        incoming_count = len(self.incoming.get(url, set()))
        authority_points = incoming_count * 10 # +10 por link recebido

        # Frequência de ocorrências no HTML (que já está em minúsculas)
        occurrences = len(term_pattern.findall(self.pages[url]))
        frequency_points = occurrences * 5 # +5 por ocorrência (conforme clarificação)

        # Penalidade
        penalty_points = -15 if self_ref else 0

        total = authority_points + frequency_points + penalty_points
        return {
            'url': url,
            'occurrences': occurrences,
            'authority_links': incoming_count, # Este é o N da tabela "Quantidade de Links que apontam"
            'self_reference': self_ref,
            'authority_points': authority_points,
            'frequency_points': frequency_points,
            'penalty_points': penalty_points,
            'score': total
        }

    def rank(self, term):
        # Converte o termo de busca para minúsculas
        term_lower = term.lower()
        # Compila a regex para o termo em minúsculas.
        # re.IGNORECASE não é mais estritamente necessário se o conteúdo já é minúsculo
        # e o termo também, mas não prejudica. Para garantir, pode-se usar sem IGNORECASE.
        term_pattern = re.compile(re.escape(term_lower))

        scored = []
        for url in self.pages:
            # Adiciona apenas se a página tiver sido efetivamente rastreada e tiver conteúdo
            if url in self.pages and self.pages[url]:
                scored.append(self._score_page(url, term_pattern))
        
        # Aplica filtro: somente páginas com ocorrências > 0
        filtered = [s for s in scored if s['occurrences'] > 0]
        
        # Ordenação por critérios de desempate (já estava correto)
        sorted_pages = sorted(
            filtered,
            key=lambda x: (
                -x['score'],
                -x['authority_links'], # Maior número de links recebidos
                -x['occurrences'],    # Maior quantidade de termos
                x['self_reference']   # False (0) vem antes de True (1), então sem autoref é melhor
            )
        )
        return sorted_pages