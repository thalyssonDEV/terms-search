import re

class SearchEngine:
    """
    Processa páginas e links para ranquear termos.
    """
    def __init__(self, pages, links):
        self.pages = pages
        self.links = links
        self.incoming = self._compute_incoming_links()

    def _compute_incoming_links(self):
        incoming = {url: set() for url in self.pages}
        for src, outs in self.links.items():
            for dst in outs:
                if dst in incoming:
                    incoming[dst].add(src)
        return incoming

    def _score_page(self, url, term_pattern):
        # self-reference detectada?
        self_ref = url in self.links.get(url, set())
        # Links recebidos total
        incoming_count = len(self.incoming.get(url, []))
        authority_points = incoming_count * 10

        # Frequência de ocorrências
        occurrences = len(term_pattern.findall(self.pages[url]))
        frequency_points = occurrences * 5

        # Penalidade
        penalty_points = -15 if self_ref else 0

        total = authority_points + frequency_points + penalty_points
        return {
            'url': url,
            'occurrences': occurrences,
            'authority_links': incoming_count,
            'self_reference': self_ref,
            'authority_points': authority_points,
            'frequency_points': frequency_points,
            'penalty_points': penalty_points,
            'score': total
        }

    def rank(self, term):
        term_pattern = re.compile(re.escape(term), re.IGNORECASE)
        scored = [self._score_page(url, term_pattern) for url in self.pages]
        # Aplica filtro: somente páginas com ocorrências > 0
        filtered = [s for s in scored if s['occurrences'] > 0]
        # Ordenação por critérios de desempate
        sorted_pages = sorted(
            filtered,
            key=lambda x: (
                -x['score'],
                -x['authority_links'],
                -x['occurrences'],
                x['self_reference']
            )
        )
        return sorted_pages