import feedparser
from datetime import datetime
import os
from dotenv import load_dotenv
from typing import List
import numpy as np 
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_aws import BedrockEmbeddings
from pinecone import Pinecone,ServerlessSpec
import feedparser
load_dotenv()

#Getting data from RSS feed.
def getdata_chunkdata(url):
    try:
        if not url:
            raise ValueError("URL is required")
        page_details=feedparser.parse(url)
        entrie=page_details.entries
        print(f"Retrieved {len(entrie)} articles from {url}")
        data=[]
        for entry in entrie:
            title=entry.get("title","N/A").strip()
            summary=entry.get("summary", "").strip()
            link=entry.get("link", "N/A").strip()
            published=entry.get("published", "N/A").strip()
            date=datetime.strptime(published, "%a, %d %b %Y %H:%M:%S %z").strftime("%Y-%m-%d")
            
            if not title or not link:
                continue
            text=f"""
            Title: {title}
            Link:{link}
            Summary: {summary}
            """
            
            data.append(Document(
                page_content=text,
                metadata={
                    "title":title,
                    "source":link,
                    "Published Date":published,
                    "date":date
                }
            ))

    except Exception as e:
        print(f"Error retrieving data from {url}: {str(e)}")
    #chunk the data
    try: 
    
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size = 500,
            chunk_overlap  = 50,
            length_function = len,
            separators=["\n\n","\n"," ",""]
        )
        chunks=text_splitter.split_documents(data)
        print(f"Chunked data into {len(chunks)} chunks")
        
        return chunks
    except Exception as e:
        print(f"Error chunking data: {str(e)}")

class EmbeddingPipeline:
    def __init__(self):
        self.embeddings=BedrockEmbeddings(model_id="amazon.titan-embed-text-v2:0",region_name="eu-west-1")
        print("Embeddings initialized")
    def embed_data(self, chunks:List[str]):
        try:
            if not chunks:
                raise ValueError("Chunks are required")
            embedder=self.embeddings
            vectors=embedder.embed_documents(chunks)
            print(f"Embedded data into {len(vectors)} vectors")
            return vectors
        except Exception as e:
            print(f"Error embedding data: {str(e)}")
#store the vector in pinecone
class VectorStore:
       def __init__(self,index_name="rte-bot"):
           self.api_key=os.getenv("PINECONE_API_KEY")
           self.index_name=index_name
           self.pc=Pinecone(api_key=self.api_key)
           existing_indexes = self.pc.list_indexes().names()
           if self.index_name not in existing_indexes:
               print(f"Index {index_name} does not exist. Creating new index...")
               self.pc.create_index(
                   name=index_name,
                   dimension=1024,
                   metric="cosine",
                   spec=ServerlessSpec(cloud="aws", region="us-east-1")
               )
               print(f"Created index {index_name}")
           else:
               print(f"Index {index_name} already exists.")
           self.index = self.pc.Index(index_name)

       def store_vector(self,vectors,chunks):
            try:
                if not vectors or not chunks:
                   raise ValueError("Vector and chunk are required")
                records=[]
                for i,(vector,chunk) in enumerate(zip(vectors,chunks)):
                
                    source_id = f"{chunk.metadata['source']}"
                    records.append((
                            source_id,   
                            vector,
                            {
                             "source": chunk.metadata.get("source",""),
                             "title": chunk.metadata.get("title",""),
                             "text": chunk.page_content,
                             "published date": chunk.metadata.get("Published Date",""),
                             "date": chunk.metadata.get("date", "")}
                    ))
                self.index.upsert(vectors=records)
                print(f"Stored {len(vectors)} vectors in index {self.index_name}")
            except Exception as e:
                print(f"Error storing vectors: {str(e)}")    
            

        

#calling the data_injection

chunks = getdata_chunkdata("http://rte.ie/feeds/rss/?index=/news")

texts = [chunk.page_content  for chunk in chunks]

embed = EmbeddingPipeline()

vectors = embed.embed_data(texts)

array_vector = np.array(vectors)#to check the dimension
print(f"Array Dimenssion:{array_vector.shape}")

vector_store = VectorStore()
vector_store.store_vector(vectors, chunks)
print("Data injection completed")

