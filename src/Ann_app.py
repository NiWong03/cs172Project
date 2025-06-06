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
def retrieve(
        storedir: str,
        query: str,
        author: str = "",
        docid: str = "",
        *,
        page: int = 1,
        page_size: int = 10,
        fuzzy: bool = False
    ):
    """
    Search the Lucene index in *storedir*.
    A document is returned if it matches   query  OR  author  OR  id.

    Parameters
    ----------
    storedir   : path to index directory
    query      : free-text query (can be empty)
    author     : exact author string   (optional)
    docid      : exact post-id string  (optional)
    page       : 1-based page number
    page_size  : hits per page
    fuzzy      : if True → each token in *query* is matched with FuzzyQuery(edit≤1)

    Returns
    -------
    hits         : list[dict]  (only for the requested page)
    total_hits   : int         (matching docs overall)
    """
    # ---------------- Lucene boiler-plate ----------------
    from org.apache.lucene.store import NIOFSDirectory
    from java.nio.file import Paths
    from org.apache.lucene.index import DirectoryReader, Term
    from org.apache.lucene.search import (
        IndexSearcher, BooleanQuery, BooleanClause,
        TermQuery, FuzzyQuery
    )
    from org.apache.lucene.queryparser.classic import QueryParser
    from org.apache.lucene.analysis.standard import StandardAnalyzer

    searchDir = NIOFSDirectory(Paths.get(storedir))
    searcher  = IndexSearcher(DirectoryReader.open(searchDir))

    # -------------- build BooleanQuery (OR) --------------
    builder      = BooleanQuery.Builder()
    should_count = 0

    # free-text part
    if query:
        if fuzzy:
            # one FuzzyQuery per token
            for tok in query.split():
                builder.add(
                    FuzzyQuery(Term("text", tok), maxEdits=1),
                    BooleanClause.Occur.SHOULD
                )
                should_count += 1
        else:
            parser = QueryParser("text", StandardAnalyzer())
            builder.add(parser.parse(query), BooleanClause.Occur.SHOULD)
            should_count += 1

    # author / id (exact)
    if author:
        builder.add(TermQuery(Term("author", author)), BooleanClause.Occur.SHOULD)
        should_count += 1
    if docid:
        builder.add(TermQuery(Term("id", docid)),     BooleanClause.Occur.SHOULD)
        should_count += 1

    # default to match-all if no criteria supplied
    if should_count:
        final_query = builder.build()
    else:
        parser = QueryParser("text", StandardAnalyzer())
        final_query = parser.parse("*:*")

    # ---------------- execute search ---------------------
    topDocs    = searcher.search(final_query, page * page_size + 1000)
    total_hits = topDocs.totalHits.value
    scoreDocs  = topDocs.scoreDocs

    start = (page - 1) * page_size
    end   = start + page_size

    # -------------- collect hits for this page ----------
    from datetime import datetime
    hits = []
    for hit in scoreDocs[start:end]:
        doc = searcher.doc(hit.doc)

        raw_time = doc.get("created_utc")
        if raw_time:
            try:
                dt   = datetime.utcfromtimestamp(float(raw_time))
                cstr = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
            except Exception:
                cstr = raw_time
        else:
            cstr = ""

        hits.append({
            "score"        : hit.score,
            "title"        : doc.get("title"),
            "text"         : doc.get("text"),
            "author"       : doc.get("author"),
            "id"           : doc.get("id"),
            "created_utc"  : cstr,
            "url"          : doc.get("url"),
            "num_comments" : doc.get("num_comments")
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
                query,
                author,
                docid,
                page        = page,
                page_size   = page_size,
                fuzzy       = (rank == 'fuzzy')    # <- toggle
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
