import logging, sys
logging.disable(sys.maxsize)
import lucene
import os
import json
from org.apache.lucene.store import MMapDirectory, SimpleFSDirectory, NIOFSDirectory
from java.nio.file import Paths
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.document import Document, Field, FieldType
from org.apache.lucene.queryparser.classic import QueryParser
from org.apache.lucene.index import FieldInfo, IndexWriter, IndexWriterConfig, IndexOptions, DirectoryReader
from org.apache.lucene.search import IndexSearcher, BoostQuery, Query
from org.apache.lucene.search.similarities import BM25Similarity
from org.apache.lucene.search import FuzzyQuery
from org.apache.lucene.index import Term
from org.apache.lucene.index import IndexOptions

def create_index(dir):
    os.mkdir(dir)
    store = SimpleFSDirectory(Paths.get(dir))
    analyzer = StandardAnalyzer()
    config = IndexWriterConfig(analyzer)
    config.setOpenMode(IndexWriterConfig.OpenMode.CREATE)
    config.setSimilarity(BM25Similarity())
    #searcher.setSimilarity(BM25Similarity())
    writer = IndexWriter(store, config)
    
    metaType = FieldType()
    metaType.setStored(True)
    metaType.setTokenized(False)
    metaType.setIndexOptions(IndexOptions.DOCS)  # for advanded search with ID and author
    
    textType = FieldType()
    textType.setStored(True)
    textType.setTokenized(True)
    textType.setIndexOptions(IndexOptions.DOCS_AND_FREQS_AND_POSITIONS)

    for filename in os.listdir('collections'):
        if filename.endswith('.json') and filename != 'crawler_checkpoint.json':
            print(f"Processing {filename}...")
            with open(os.path.join('collections', filename), 'r') as f:
                #data = [json.loads(line) for line in f if line.strip()]
                data = json.load(f) # for advanced search, we assume each file is a valid JSON array
                for post in data:
                    if not isinstance(post, dict):
                        print(f"Warning: Post is not a dictionary in {filename}")
                        continue
                    try:
                        doc = Document()
                        doc.add(Field('id', str(post.get('id', '')), metaType))
                        doc.add(Field('title', str(post.get('title', '')), textType))
                        doc.add(Field('author', str(post.get('author', '')), metaType))
                        doc.add(Field('created_utc', str(post.get('created_utc', '')), metaType))
                        doc.add(Field('score', str(post.get('score', '')), metaType))
                        doc.add(Field('url', str(post.get('url', '')), metaType))
                        doc.add(Field('num_comments', str(post.get('num_comments', '')), metaType))
                        doc.add(Field('text', str(post.get('text', '')), textType))
                        
                        # combine all comments 
                        all_comments = []
                        comments = post.get('comments', [])
                        for comment in comments:
                            if isinstance(comment, dict):
                                all_comments.append(comment.get('body', ''))
                                replies = comment.get('replies', [])
                                if isinstance(replies, list):
                                    for reply in replies:
                                        if isinstance(reply, dict):
                                            all_comments.append(reply.get('body', ''))
                        
                        comments_text = ' '.join(all_comments)
                        doc.add(Field('comments', str(comments_text), textType))
                        
                        writer.addDocument(doc)
                    except Exception as e:
                        print(f"Error processing post in {filename}: {str(e)}")
                        continue
                        
    writer.close()
    print("Indexing completed!")

def retrieve(storedir, query, author='', docid='', page=1, page_size=10):
    from org.apache.lucene.search import BooleanQuery, BooleanClause, TermQuery, WildcardQuery
    from org.apache.lucene.index import Term

    searchDir = NIOFSDirectory(Paths.get(storedir))
    searcher = IndexSearcher(DirectoryReader.open(searchDir))

    parser = QueryParser('text', StandardAnalyzer())
    main_query = parser.parse(query) if query else None

    boolean_query = BooleanQuery.Builder()
    if main_query:
        boolean_query.add(main_query, BooleanClause.Occur.MUST)
    if author:
        # For robustness, use WildcardQuery for now (for demo, not for speed)
        boolean_query.add(WildcardQuery(Term("author", f"*{author}*")), BooleanClause.Occur.MUST)
        # For strict match, use this:
        # boolean_query.add(TermQuery(Term("author", author)), BooleanClause.Occur.MUST)
    if docid:
        boolean_query.add(WildcardQuery(Term("id", f"*{docid}*")), BooleanClause.Occur.MUST)
        # For strict match, use this:
        # boolean_query.add(TermQuery(Term("id", docid)), BooleanClause.Occur.MUST)

    # If no fields are filled, match all
    final_query = boolean_query.build() if (main_query or author or docid) else parser.parse("*:*")

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


if __name__ == "__main__":
    # Initialize Lucene
    lucene.initVM()
    create_index('index')
    # test retrieval with query "Literature"
    # retrieve('index', 'Literature')

