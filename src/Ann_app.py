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
from org.apache.lucene.search import BooleanQuery, BooleanClause, TermQuery, FuzzyQuery
from org.apache.lucene.index import Term
from org.apache.lucene.queryparser.classic import QueryParser
from org.apache.lucene.analysis.standard import StandardAnalyzer

app = Flask(__name__)
def retrieve(storedir, query, author='', docid='',
             *, page=1, page_size=10, rank_mode='default'):
    """
    rank_mode = 'default'  ->  BM25, exact text match
               = 'custom'   ->  fuzzy tokens OR-ed on title/text,
                                title hits get boost 3.0
    """
    from org.apache.lucene.store import NIOFSDirectory
    from java.nio.file import Paths
    from org.apache.lucene.index import DirectoryReader, Term
    from org.apache.lucene.search import (
        IndexSearcher, BooleanQuery, BooleanClause,
        TermQuery, FuzzyQuery, BoostQuery
    )
    from org.apache.lucene.queryparser.classic import QueryParser
    from org.apache.lucene.analysis.standard import StandardAnalyzer
    from datetime import datetime

    searchDir = NIOFSDirectory(Paths.get(storedir))
    searcher  = IndexSearcher(DirectoryReader.open(searchDir))

    builder      = BooleanQuery.Builder()
    should_cnt   = 0

    # ───────────────────────────────────────── text part
    if query:
        if rank_mode == 'custom':                           # fuzzy + boosting
            for tok in query.split():
                # fuzzy on title (boost ×3)
                builder.add(
                    BoostQuery(FuzzyQuery(Term("title", tok), maxEdits=1), 3.0),
                    BooleanClause.Occur.SHOULD)
                should_cnt += 1
                # fuzzy on text (no extra boost)
                builder.add(
                    FuzzyQuery(Term("text", tok), maxEdits=1),
                    BooleanClause.Occur.SHOULD)
                should_cnt += 1
        else:                                               # default BM25
            parser = QueryParser("text", StandardAnalyzer())
            builder.add(parser.parse(query), BooleanClause.Occur.SHOULD)
            should_cnt += 1

    # ───────────────────────────────────────── author / id
    if author:
        builder.add(TermQuery(Term("author", author)), BooleanClause.Occur.SHOULD)
        should_cnt += 1
    if docid:
        builder.add(TermQuery(Term("id", docid)),     BooleanClause.Occur.SHOULD)
        should_cnt += 1

    # fall-back match-all if user left everything blank
    if should_cnt:
        final_q = builder.build()
    else:
        final_q = QueryParser("text", StandardAnalyzer()).parse("*:*")

    # ───────────────────────────────────────── search + paging
    topDocs    = searcher.search(final_q, page * page_size + 1000)
    total_hits = topDocs.totalHits.value
    scoreDocs  = topDocs.scoreDocs
    start, end = (page-1)*page_size, (page-1)*page_size + page_size

    hits = []
    for hit in scoreDocs[start:end]:
        doc = searcher.doc(hit.doc)
        # prettify timestamp
        raw = doc.get("created_utc")
        if raw:
            try:
                raw = datetime.utcfromtimestamp(float(raw)).strftime('%Y-%m-%d %H:%M:%S UTC')
            except Exception:
                pass
        hits.append({
            "score"       : hit.score,
            "title"       : doc.get("title"),
            "text"        : doc.get("text"),
            "author"      : doc.get("author"),
            "id"          : doc.get("id"),
            "created_utc" : raw or "",
            "url"         : doc.get("url"),
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
@app.route('/output', methods=['GET', 'POST'])
def output():
    # ---------------------  defaults  ---------------------
    query      = ""
    author     = ""
    docid      = ""
    rank       = "default"     #  "default"  or  "fuzzy"
    page       = 1
    page_size  = 10

    results    = []
    error      = None
    total_hits = 0

    # ---------------------  read form / args  --------------
    if request.method == 'POST':
        query  = request.form.get('query',  '')
        author = request.form.get('author', '')
        docid  = request.form.get('id',     '')
        rank   = request.form.get('rank',   'default')
    else:                                       # GET
        query  = request.args.get('query',  '')
        author = request.args.get('author', '')
        docid  = request.args.get('id',     '')
        rank   = request.args.get('rank',   'default')
        page   = int(request.args.get('page',  '1'))

    # ---------------------  run search  --------------------
    if query or author or docid:               # at least one criterion
        try:
            lucene.getVMEnv().attachCurrentThread()

            results, total_hits = retrieve(
                './index',
                query, author, docid,
                page       = page,
                page_size  = page_size,
                rank_mode  = rank           # <── pass through
            )
        except Exception as e:
            error = f"Error searching index: {e}"
    else:
        error = "Please enter a query, author, or id."

    total_pages = (total_hits + page_size - 1) // page_size

    # ---------------------  render  ------------------------
    return render_template(
        'output.html',
        # search results
        lucene_output = results,
        total_hits    = total_hits,

        # search / paging state
        query  = query,
        author = author,
        id     = docid,
        rank   = rank,
        page   = page,
        page_size = page_size,
        total_pages = total_pages,

        # error (if any)
        error = error
    )


lucene.initVM(vmargs=['-Djava.awt.headless=true'])

if __name__ == "__main__":
    app.run(debug=True)
