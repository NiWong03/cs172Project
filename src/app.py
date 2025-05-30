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

def retrieve(storedir, query):
    searchDir = NIOFSDirectory(Paths.get(storedir))
    searcher = IndexSearcher(DirectoryReader.open(searchDir))
    parser = QueryParser('text', StandardAnalyzer())  # use the real field name
    parsed_query = parser.parse(query)
    topDocs = searcher.search(parsed_query, 10).scoreDocs
    topkdocs = []
    for hit in topDocs:
        doc = searcher.doc(hit.doc)
        topkdocs.append({
            "score": hit.score,
            "text": doc.get("text"),
            "title": doc.get("title"),
            "author": doc.get("author"),
            "created_utc": doc.get("created_utc"),
            "url": doc.get("url"),
            "num_comments": doc.get("num_comments")
        })
    return topkdocs


@app.route("/")
def home():
    return redirect(url_for('input'))

@app.route('/input', methods=['GET'])
def input():
    return render_template('input.html')

@app.route('/output', methods=['POST'])
def output():
    form_data = request.form
    query = form_data.get('query', '')
    results = []
    error = None
    if query:
        try:
            lucene.getVMEnv().attachCurrentThread()
            results = retrieve('./index', query)  # Use your real index path here
        except Exception as e:
            error = f"Error searching index: {e}"
    else:
        error = "Empty query."
    return render_template('output.html', lucene_output=results, query=query, error=error)

lucene.initVM(vmargs=['-Djava.awt.headless=true'])

if __name__ == "__main__":
    app.run(debug=True)
