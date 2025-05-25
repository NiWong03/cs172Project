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

def create_index(dir):
    os.mkdir(dir)
    store = SimpleFSDirectory(Paths.get(dir))
    analyzer = StandardAnalyzer()
    config = IndexWriterConfig(analyzer)
    config.setOpenMode(IndexWriterConfig.OpenMode.CREATE)
    config.setSimilarity(BM25Similarity())
    searcher.setSimilarity(BM25Similarity())
    writer = IndexWriter(store, config)
    
    metaType = FieldType()
    metaType.setStored(True)
    metaType.setTokenized(False)
    
    textType = FieldType()
    textType.setStored(True)
    textType.setTokenized(True)
    textType.setIndexOptions(IndexOptions.DOCS_AND_FREQS_AND_POSITIONS)

    for filename in os.listdir('collections'):
        if filename.endswith('.json') and filename != 'crawler_checkpoint.json':
            print(f"Processing {filename}...")
            with open(os.path.join('collections', filename), 'r') as f:
                data = [json.loads(line) for line in f if line.strip()]
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

def retrieve(storedir, term_text, field="text"):
    print(f"Searching in directory: {os.path.abspath(storedir)}")
    if not os.path.exists(storedir):
        print(f"Error: Index directory {storedir} does not exist!")
        return
        
    searchDir = NIOFSDirectory(Paths.get(storedir))
    searcher = IndexSearcher(DirectoryReader.open(searchDir))
    query = FuzzyQuery(Term(field, term_text), maxEdits=1)
    topDocs = searcher.search(query, 10).scoreDocs
    topkdocs = []

    for hit in topDocs:
        doc = searcher.doc(hit.doc)
        topkdocs.append({
            "score": hit.score,
            "id": doc.get("id"),
            "title": doc.get("title"),
        })

    print(f"Found {len(topkdocs)} results for query: {term_text}")
    print(topkdocs)

if __name__ == "__main__":
    # Initialize Lucene
    lucene.initVM()
    # create_index('index')
    # test retrieval with query "Literature"
    retrieve('index', 'Literature')

