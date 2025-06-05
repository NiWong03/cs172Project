import lucene
import os
from datetime import datetime
from org.apache.lucene.store import NIOFSDirectory
from java.nio.file import Paths
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.queryparser.classic import QueryParser
from org.apache.lucene.index import DirectoryReader
from org.apache.lucene.search import IndexSearcher
from flask import request, Flask, render_template, redirect, url_for
from org.apache.lucene.search import BooleanQuery, BooleanClause, TermQuery
from org.apache.lucene.index import Term

app = Flask(__name__)
def retrieve(storedir, query, author='', docid='', page=1, page_size=10):
    from org.apache.lucene.search import BooleanQuery, BooleanClause, TermQuery
    from org.apache.lucene.index import Term
    from org.apache.lucene.queryparser.classic import QueryParser
    from org.apache.lucene.analysis.standard import StandardAnalyzer

    searchDir = NIOFSDirectory(Paths.get(storedir))
    searcher = IndexSearcher(DirectoryReader.open(searchDir))

    parser = QueryParser('text', StandardAnalyzer())
    boolean_query = BooleanQuery.Builder()
    num_should = 0

    # Free-text
    if query:
        main_query = parser.parse(query)
        boolean_query.add(main_query, BooleanClause.Occur.SHOULD)
        num_should += 1

    # Author
    if author:
        boolean_query.add(TermQuery(Term("author", author)), BooleanClause.Occur.SHOULD)
        num_should += 1

    # ID
    if docid:
        boolean_query.add(TermQuery(Term("id", docid)), BooleanClause.Occur.SHOULD)
        num_should += 1

    if num_should > 0:
        final_query = boolean_query.build()
    else:
        final_query = parser.parse("*:*")  # match all

    # Get enough docs to know the total count
    topDocs = searcher.search(final_query, page * page_size + 1000)
    total_hits = topDocs.totalHits.value
    scoreDocs = topDocs.scoreDocs
    start = (page - 1) * page_size
    end = start + page_size
    hits = []
    for hit in scoreDocs[start:end]:
        doc = searcher.doc(hit.doc)
        created_raw = doc.get("created_utc")
        if created_raw:
            try:
                from datetime import datetime
                dt = datetime.utcfromtimestamp(float(created_raw))
                created_str = dt.strftime('%Y-%m-%d %H:%M:%S UTC')
            except Exception:
                created_str = created_raw
        else:
            created_str = ""
        hits.append({
            "score": hit.score,
            "text": doc.get("text"),
            "title": doc.get("title"),
            "author": doc.get("author"),
            "id": doc.get("id"),
            "created_utc": created_str,
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
@app.route('/output', methods=['GET', 'POST'])
def output():
    query = ""
    author = ""
    docid = ""
    page = 1
    results = []
    error = None
    page_size = 10
    total_hits = 0

    if request.method == 'POST':
        query = request.form.get('query', '')
        author = request.form.get('author', '')
        docid = request.form.get('id', '')
    elif request.method == 'GET':
        query = request.args.get('query', '')
        author = request.args.get('author', '')
        docid = request.args.get('id', '')
        page = int(request.args.get('page', '1'))

    if query or author or docid:
        try:
            lucene.getVMEnv().attachCurrentThread()
            results, total_hits = retrieve('./index', query, author, docid, page=page, page_size=page_size)
        except Exception as e:
            error = f"Error searching index: {e}"
    else:
        error = "Empty query."

    total_pages = (total_hits + page_size - 1) // page_size

    return render_template(
        'output.html',
        lucene_output=results,
        query=query,
        author=author,
        id=docid,
        error=error,
        page=page,
        page_size=page_size,
        total_hits=total_hits,
        total_pages=total_pages
    )



lucene.initVM(vmargs=['-Djava.awt.headless=true'])

if __name__ == "__main__":
    app.run(debug=True)
