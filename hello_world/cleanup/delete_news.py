from pinecone import Pinecone
import os
from datetime import datetime, timedelta

# Initialize once (better performance in Lambda)
pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
index = pc.Index("rte-bot")

def lambda_handler(event, context):
    delete_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    print(f"Deleting all records with date: {delete_date}")

    try:
        response = index.delete(
            filter={"date": {"$eq": delete_date}}
        )

        print("Old news deleted successfully")
        return {
            "statusCode": 200,
            "body": f"Deleted records for date {delete_date}"
        }


    except Exception as e:
        print(f"Error deleting old news: {str(e)}")

        return {
            "statusCode": 500,
            "body": str(e)
        }