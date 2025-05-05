from classes.Crawler import Crawler
from classes.SearchEngine import SearchEngine
from flask import Flask, request, render_template
import os
import logging
from urllib.parse import urljoin

# Configurações fixas - editar conforme necessário
BASE_URL = os.getenv("BASE_URL")
PAGES = os.getenv("PAGES", "").split(",")

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def print_results(term, results):
    """Exibe resultados no formato tabular desejado."""
    print(f"\n=== Busca pelo termo: {term} ===")
    header = f"{'Pos':<3} {'Página':<20} {'Ocorrências (+5)':<20} {'Links(+10)':<12} {'Autoref(-15)':<14} {'Total':<6}"
    print(header)
    print('-' * len(header))
    for i, res in enumerate(results, start=1):
        occ = f"{res['occurrences']}×5={res['frequency_points']}"
        links = f"{res['authority_links']}×10={res['authority_points']}"
        auto = f"{-15 if res['self_reference'] else 0:>3}"
        total = f"{res['score']:>5}"
        page = res['url'].split('/')[-1]
        print(f"{i:<3} {page:<20} {occ:<20} {links:<12} {auto:<14} {total:<6}")

 
app = Flask(__name__)

# Configuração
BASE_URL = os.getenv("BASE_URL")
PAGES = os.getenv("PAGES", "").split(",")

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
    results = []
    term = None

    if request.method == 'POST':
        term = request.form['term']
        crawler = Crawler()

        urls = [urljoin(BASE_URL, page) for page in PAGES]
        for url in urls:
            crawler._crawl_page(url)

        pages_map, links_map = crawler.pages, crawler.links

        searcher = SearchEngine(pages_map, links_map)
        results = searcher.rank(term)

    return render_template('index.html', term=term, results=results)


if __name__ == "__main__":
    app.run(debug=True)