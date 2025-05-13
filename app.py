import os
import logging
from urllib.parse import urljoin
from flask import Flask, request, render_template
from classes.Crawler import Crawler
from classes.SearchEngine import SearchEngine

# Ajudou a identificar os problemas que estavam acontencendo antes das alterações do thalysson
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# --- Configurações da Aplicação ---

# Aqui onde a gente coloca o endereço da página que ele vai começar a procurar.
CONFIG_BASE_URL = os.getenv("BASE_URL")
if CONFIG_BASE_URL:
    logging.info(f"BASE_URL encontrada: '{CONFIG_BASE_URL}'")
else:
    logging.info("BASE_URL não definida. Será usado um valor padrão para desenvolvimento.")

# Nome do arquivo HTML que vai servir como ponto de partida pro nosso crawler
START_PAGE_FILENAME = "mochileiro.html"

# Inicialização da aplicação Flask.
app = Flask(__name__)

# --- Rotas da aplicação ---
@app.route('/', methods=['GET', 'POST'])
def pagina_principal():
    """
    Rota principal da aplicação.
    GET: Exibe o formulário de busca.
    POST: Processa o termo buscado, executa o crawler e o motor de busca,
          e exibe os resultados ou mensagens de erro.
    """
    resultados_busca = []
    termo_digitado = ""
    mensagem_erro = None

    # Define a URL base pra requisição
    url_base_da_requisicao = CONFIG_BASE_URL

    if request.method == 'POST':
        termo_digitado = request.form.get('term', "").strip() # Pega o termo e remove espaços extras.

        if not url_base_da_requisicao:
            logging.error("BASE_URL não está configurada para esta requisição.")
            mensagem_erro = "Erro crítico: A URL base do sistema não está configurada. Contate o administrador."
            # Sem URL base, não há como prosseguir com a busca.
            return render_template('index.html',term=termo_digitado,results=resultados_busca,error_message=mensagem_erro)

        if not termo_digitado:
            mensagem_erro = "Por favor, digite um termo para a busca."
        else:
            logging.info(f"Termo buscado pelo usuário: '{termo_digitado}'")
            logging.info(f"Utilizando BASE_URL para crawling: '{url_base_da_requisicao}'")

            # Constrói a URL completa de início para o crawler.
            url_inicial_crawler = urljoin(url_base_da_requisicao, START_PAGE_FILENAME)
            logging.info(f"Crawler iniciando a partir de: {url_inicial_crawler}")

            # Instancia e executa o Crawler.
            meu_crawler = Crawler(base_url=url_base_da_requisicao)
            # O crawler retorna o conteúdo das páginas e o grafo de links entre elas.
            paginas_conteudo, grafo_links = meu_crawler.crawl(url_inicial_crawler)

            if not paginas_conteudo:
                logging.warning("Nenhuma página foi rastreada. Verificar BASE_URL e START_PAGE_FILENAME.")
                mensagem_erro = "Não foi possível encontrar páginas para realizar a busca. Verifique a configuração."
            else:
                # Com os dados coletados, instancio o SearchEngine.
                meu_search_engine = SearchEngine(paginas_conteudo, grafo_links)
                # Realizo a busca e obtenho os resultados ranqueados.
                resultados_busca = meu_search_engine.rank_pages(termo_digitado)
                if not resultados_busca:
                    mensagem_erro = f"Nenhum resultado encontrado para '{termo_digitado}'."

    return render_template('index.html',term=termo_digitado,results=resultados_busca,error_message=mensagem_erro)

# --- A.P.L.I.C.A.Ç.Â.O ---
if __name__ == "__main__":

    # Define uma URL base padrão para desenvolvimento se CONFIG_BASE_URL não foi definida via var. de ambiente. è bom pra tipo, fazer testes locais kkkk
    url_final_para_execucao = CONFIG_BASE_URL
    if not url_final_para_execucao:
        url_dev_padrao = "http://localhost:8000/"
        logging.warning(f"BASE_URL não definida. Usando URL padrão para desenvolvimento: {url_dev_padrao}")
        logging.warning("Certifique-se de que os arquivos HTML de teste estão sendo servidos nesta URL (ex: python -m http.server 8000).")
        url_final_para_execucao = url_dev_padrao
        CONFIG_BASE_URL = url_final_para_execucao # Atualizo a variável global para que a rota use este fallback.

    logging.info(f"Aplicação Flask iniciará com BASE_URL: '{url_final_para_execucao}'")

    # Inicia o servidor
    app.run(debug=True, host='0.0.0.0', port=5000)
