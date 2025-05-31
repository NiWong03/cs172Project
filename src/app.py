import lucene
import os
from org.apache.lucene.store import NIOFSDirectory
from java.nio.file import Paths
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.queryparser.classic import QueryParser
from org.apache.lucene.index import DirectoryReader
from org.apache.lucene.search import IndexSearcher
from flask import request, Flask, render_template, redirect, url_for

app = Flask(__name__)

def retrieve(storedir, query, page=1, page_size=10):
    searchDir = NIOFSDirectory(Paths.get(storedir))
    searcher = IndexSearcher(DirectoryReader.open(searchDir))
    parser = QueryParser('text', StandardAnalyzer())
    parsed_query = parser.parse(query)
    # Get enough docs to know the total count
    topDocs = searcher.search(parsed_query, page * page_size + 1000)  # Fetch a big enough window
    total_hits = topDocs.totalHits.value
    scoreDocs = topDocs.scoreDocs
    start = (page - 1) * page_size
    end = start + page_size
    hits = []
    for hit in scoreDocs[start:end]:
        doc = searcher.doc(hit.doc)
        hits.append({
            "score": hit.score,
            "text": doc.get("text"),
            "title": doc.get("title"),
            "author": doc.get("author"),
            "id": doc.get("id"),
            "created_utc": doc.get("created_utc"),
            "url": doc.get("url"),
            "num_comments": doc.get("num_comments")
        })
    return hits, total_hits

@app.route("/")
def home():
    return redirect(url_for('input'))

@app.route('/input', methods=['GET'])
def input():
    return render_template('input.html')

@app.route('/output', methods=['GET', 'POST'])
def output():
    query = ""
    page = 1
    results = []
    error = None
    page_size = 10
    total_hits = 0

    if request.method == 'POST':
        query = request.form.get('query', '')
    elif request.method == 'GET':
        query = request.args.get('query', '')
        page = int(request.args.get('page', '1'))

    if query:
        try:
            lucene.getVMEnv().attachCurrentThread()
            results, total_hits = retrieve('./index', query, page=page, page_size=page_size)
        except Exception as e:
            error = f"Error searching index: {e}"
    else:
        error = "Empty query."

    total_pages = (total_hits + page_size - 1) // page_size  # round up

    return render_template(
        'output.html',
        lucene_output=results,
        query=query,
        error=error,
        page=page,
        page_size=page_size,
        total_hits=total_hits,
        total_pages=total_pages
    )


lucene.initVM(vmargs=['-Djava.awt.headless=true'])

if __name__ == "__main__":
    app.run(debug=True)
