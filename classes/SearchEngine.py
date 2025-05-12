import re # Para trabalhar com expressões regulares na busca do termo.

class SearchEngine:
    """
    Processa o conteúdo das páginas e a estrutura de links para ranquear as páginas
    """
    def __init__(self, mapa_paginas_conteudo, grafo_de_links):
        self.mapa_paginas_conteudo = mapa_paginas_conteudo
        self.grafo_de_links = grafo_de_links
        # Calculo os links de entrada para cada página uma vez
        self.mapa_links_entrada = self._calcular_links_de_entrada()

    def _calcular_links_de_entrada(self):
        links_entrada = {url: set() for url in self.mapa_paginas_conteudo}
        for url_origem, conjunto_urls_destino in self.grafo_de_links.items():
            # Garanto que a página de origem foi de fato rastreada 
            if url_origem not in self.mapa_paginas_conteudo:
                continue
            for url_destino in conjunto_urls_destino:
                if url_destino in links_entrada:
                    links_entrada[url_destino].add(url_origem)
        return links_entrada

    def _calcular_score_da_pagina(self, url_pagina, padrao_regex_termo): # Calculo do score de uma página
        # Verifica se existe uma autorreferência
        tem_autorreferencia = url_pagina in self.grafo_de_links.get(url_pagina, set())
        # Calcula os pontos de autoridade com base nos links recebidos.
        quantidade_links_recebidos = len(self.mapa_links_entrada.get(url_pagina, set()))
        pontos_autoridade = quantidade_links_recebidos * 10 # +10 por link recebido
        # Calcula os pontos de frequência do termo na página.
        ocorrencias_termo = 0
        if self.mapa_paginas_conteudo.get(url_pagina):
             ocorrencias_termo = len(padrao_regex_termo.findall(self.mapa_paginas_conteudo[url_pagina]))
        pontos_frequencia = ocorrencias_termo * 5 # +5 por ocorrência do termo
        # Aplica penalidade por autorreferência.
        pontos_penalidade = -15 if tem_autorreferencia else 0

        score_total = pontos_autoridade + pontos_frequencia + pontos_penalidade # Score total

        return {
            'url': url_pagina,
            'ocorrencias_termo': ocorrencias_termo,
            'links_recebidos': quantidade_links_recebidos,
            'tem_autorreferencia': tem_autorreferencia,
            'pontos_autoridade': pontos_autoridade,
            'pontos_frequencia': pontos_frequencia,
            'pontos_penalidade': pontos_penalidade,
            'score_final': score_total
        }

    def rank_pages(self, termo_busca): # Método para ranquear as páginas com base no termo de busca

        termo_busca_lower = termo_busca.lower()
        # Compila a expressão regular para buscar o termo.
        padrao_regex_termo = re.compile(re.escape(termo_busca_lower))
        paginas_com_score = []
        for url_pagina in self.mapa_paginas_conteudo: # Se não houver conteúdo, ignora a página.
            if url_pagina in self.mapa_paginas_conteudo and self.mapa_paginas_conteudo[url_pagina]:
                score_info = self._calcular_score_da_pagina(url_pagina, padrao_regex_termo)
                paginas_com_score.append(score_info)

        # mantenho apenas páginas onde o termo de busca ocorre pelo menos uma vez
        paginas_filtradas = [p for p in paginas_com_score if p['ocorrencias_termo'] > 0]

        # Ordenação das páginas.
        paginas_ordenadas = sorted(
            paginas_filtradas,
            key=lambda x: (
                -x['score_final'],         
                -x['links_recebidos'],     
                -x['ocorrencias_termo'],   
                x['tem_autorreferencia']   
            )
        )
        return paginas_ordenadas