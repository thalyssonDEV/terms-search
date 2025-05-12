from classes.Crawler import Crawler
from classes.SearchEngine import SearchEngine
from flask import Flask, request, render_template
import os
import logging
from urllib.parse import urljoin

# Teste imediato de os.getenv
retrieved_base_url = os.getenv("BASE_URL") # CORRIGIDO: Deve ser o NOME da variável de ambiente
print(f"DEBUG: os.getenv('BASE_URL') retornou: '{retrieved_base_url}'") # LINHA DE DEBUG ADICIONADA

# Configurações fixas
BASE_URL = retrieved_base_url # Use o valor recuperado do ambiente

# Configuração de logging (deve vir depois da tentativa de ler BASE_URL para que BASE_URL possa ser usada no logging se necessário)
# No entanto, a configuração básica do logging pode vir antes.
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Verifica BASE_URL após a tentativa de leitura e ANTES de instanciar o Flask app
# para que a mensagem de erro apareça cedo se a variável não estiver definida
# e nenhum fallback imediato for desejado aqui.
if not BASE_URL:
    logging.error("Variável de ambiente BASE_URL não definida (verificado no topo do script)!")
    # Neste ponto, BASE_URL é None. O fallback ocorrerá no bloco if __name__ == "__main__".

app = Flask(__name__)

# START_PAGE_FILENAME deve ser definido independentemente de BASE_URL
START_PAGE_FILENAME = "mochileiro.html" # Ou outra das 5 páginas

@app.route('/', methods=['GET', 'POST'])
def index():
    results = []
    term_input = None
    current_base_url = BASE_URL # Usa a BASE_URL definida no escopo global (que pode ter sido atualizada no bloco main)

    if request.method == 'POST':
        term_input = request.form['term']

        if not current_base_url: # Verifica a BASE_URL que será usada pela rota
            logging.error("BASE_URL não está configurada para esta requisição.")
            return render_template('index.html', error_message="Configuração BASE_URL ausente.")

        # Para garantir que o Crawler use a BASE_URL potencialmente atualizada pelo bloco main
        # (embora em um servidor de produção, as variáveis de ambiente sejam mais estáticas)
        crawler = Crawler(base_url=current_base_url)

        start_url = urljoin(current_base_url, START_PAGE_FILENAME)
        logging.info(f"Iniciando crawling a partir de: {start_url} (usando BASE_URL: {current_base_url})")

        pages_map, links_map = crawler.crawl(start_url)

        if not pages_map:
            logging.warning("Nenhuma página foi rastreada. Verifique o BASE_URL e a START_PAGE_FILENAME.")
            return render_template('index.html', term=term_input, results=results,
                                   error_message="Nenhuma página foi rastreada. Verifique as configurações e a página inicial.")

        searcher = SearchEngine(pages_map, links_map)
        results = searcher.rank(term_input)

    return render_template('index.html', term=term_input, results=results)

if __name__ == "__main__":
    # A variável BASE_URL aqui é a global definida no topo.
    # Se retrieved_base_url foi None, então BASE_URL também é None aqui.
    final_base_url_for_run = BASE_URL

    if not final_base_url_for_run:
        print("AVISO: BASE_URL não definida (verificado no bloco main). Usando http://localhost:8000/ para desenvolvimento.")
        print("Certifique-se de servir os arquivos HTML de teste nesta URL.")
        final_base_url_for_run = "http://localhost:8000/"
        # Atualiza a variável global BASE_URL para que as rotas usem o fallback se estiverem no mesmo processo
        # (importante para o servidor de desenvolvimento Flask com reloader desligado ou primeira execução)
        # No entanto, com o reloader, o escopo global é reiniciado.
        # A melhor prática é que as rotas dependam de app.config ou de uma forma mais robusta de obter a config.
        # Para este exemplo, vamos reatribuir a global, mas ciente das limitações com o reloader.
        BASE_URL = final_base_url_for_run

    print(f"DEBUG: Flask (bloco main) usará BASE_URL: '{final_base_url_for_run}'") # LINHA DE DEBUG ADICIONADA

    # O app Flask usará a variável global BASE_URL.
    # Se o reloader estiver ativo, ele irá recarregar o script, e `os.getenv("BASE_URL")` será chamado novamente.
    # Se `use_reloader=False`, ele usará o valor de BASE_URL como está neste ponto.
    app.run(debug=True, host='0.0.0.0', port=5000)