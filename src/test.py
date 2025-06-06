import lucene
from org.apache.lucene.store import NIOFSDirectory
from java.nio.file import Paths
from org.apache.lucene.index import DirectoryReader, Term
from org.apache.lucene.search import IndexSearcher, TermQuery, BooleanQuery, BooleanClause
from org.apache.lucene.queryparser.classic import QueryParser
from org.apache.lucene.analysis.standard import StandardAnalyzer

# ----- Setup -----
lucene.initVM()
index_dir = "index"  # adjust as needed

searchDir = NIOFSDirectory(Paths.get(index_dir))
searcher = IndexSearcher(DirectoryReader.open(searchDir))

# ----- Inputs -----
author = "Sich_befinden"
docid = "7gyaks"
text_query = ""  # example: "reading"

# ----- Build BooleanQuery with SHOULD (OR/UNION) -----
parser = QueryParser("text", StandardAnalyzer())
boolean_query = BooleanQuery.Builder()

num_should = 0

# Free-text
if text_query:
    main_query = parser.parse(text_query)
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

# ----- Search -----
topDocs = searcher.search(final_query, 10)
print("Results:", topDocs.totalHits.value)
for hit in topDocs.scoreDocs:
    doc = searcher.doc(hit.doc)
    print("author repr:", repr(doc.get("author")))
    print("id repr:", repr(doc.get("id")))
    print("title:", doc.get("title"))
    print("---")

# ----- Example for "AND" (intersection) search -----
print("\n--- Now show AND (intersection, MUST) results for comparison ---")
boolean_and = BooleanQuery.Builder()
num_must = 0

if author:
    boolean_and.add(TermQuery(Term("author", author)), BooleanClause.Occur.MUST)
    num_must += 1
if docid:
    boolean_and.add(TermQuery(Term("id", docid)), BooleanClause.Occur.MUST)
    num_must += 1
if text_query:
    main_query = parser.parse(text_query)
    boolean_and.add(main_query, BooleanClause.Occur.MUST)
    num_must += 1

if num_must > 0:
    final_query_and = boolean_and.build()
else:
    final_query_and = parser.parse("*:*")

topDocs_and = searcher.search(final_query_and, 10)
print("Results (AND):", topDocs_and.totalHits.value)
for hit in topDocs_and.scoreDocs:
    doc = searcher.doc(hit.doc)
    print("author repr:", repr(doc.get("author")))
    print("id repr:", repr(doc.get("id")))
    print("title:", doc.get("title"))
    print("---")
