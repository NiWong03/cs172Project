import lucene
from org.apache.lucene.store import NIOFSDirectory
from java.nio.file import Paths
from org.apache.lucene.index import DirectoryReader, Term
from org.apache.lucene.search import IndexSearcher, TermQuery

lucene.initVM()

index_dir = "index"  # adjust if needed
searchDir = NIOFSDirectory(Paths.get(index_dir))
searcher = IndexSearcher(DirectoryReader.open(searchDir))

author = "Sich_befinden"
idval = "7gyaks"

from org.apache.lucene.search import BooleanQuery, BooleanClause

query = BooleanQuery.Builder()
query.add(TermQuery(Term("author", author)), BooleanClause.Occur.MUST)
query.add(TermQuery(Term("id", idval)), BooleanClause.Occur.MUST)
final_query = query.build()

topDocs = searcher.search(final_query, 10)
print("Results:", topDocs.totalHits.value)
for hit in topDocs.scoreDocs:
    doc = searcher.doc(hit.doc)
    print("author repr:", repr(doc.get("author")))
    print("id repr:", repr(doc.get("id")))
    print("title:", doc.get("title"))

# reader = searcher.getIndexReader()
# for i in range(reader.maxDoc()):
#     doc = reader.document(i)
#     print(f"author: {repr(doc.get('author'))} | id: {repr(doc.get('id'))}")

