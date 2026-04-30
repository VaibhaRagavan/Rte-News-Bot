#Deleting the data in the vector store
from pinecone import Pinecone
import os
from datetime import datetime,timedelta
from dotenv import load_dotenv
load_dotenv()
key=os.getenv("PINECONE_API_KEY")
pc=Pinecone(api_key=key)
index=pc.Index("rte-bot")
delete_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
print(f"Deleting all records with date older than: {delete_date}")
try:
    delete_old_news=index.delete(
    filter={"date":{"$eq":delete_date}})
    print("old news Deleted successufully")
except Exception as e:
    print(f"Error deleting old news: {str(e)}")


