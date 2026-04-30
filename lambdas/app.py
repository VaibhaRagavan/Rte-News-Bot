import json
import os
from langchain_aws import BedrockEmbeddings
from langchain.memory import ConversationBufferMemory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain.prompts import ChatPromptTemplate 

from pinecone import Pinecone
from dotenv import load_dotenv
import boto3
import uuid
load_dotenv()
bedrock=boto3.client("bedrock-runtime",region_name="eu-west-1")
key=os.getenv("PINECONE_API_KEY")
model_id=os.getenv("MODEL_ID")
pc=Pinecone(api_key=key)
print(f"pinecone intialized{pc}")
class EmbeddingPipeline:
    def __init__(self):
        self.embeddings=BedrockEmbeddings(model_id="amazon.titan-embed-text-v2:0",region_name="eu-west-1")
        print("Embeddings initialized")
embedder=EmbeddingPipeline()
index=pc.Index("rte-bot")

#Retrieve the data from pinecone
def Retrieve(query):
    query_vector=embedder.embeddings.embed_query(query)
    results=index.query(vector=query_vector,top_k=5,include_metadata=True)
    retrieved_data=[]
    for match in results.matches:
        metadata = match.metadata or {}
        item_str=f"""
            Source: {metadata.get("source", "N/A")}
            Date: {metadata.get("date", "N/A")}
            Summary: {metadata.get("text", "N/A")}
            """
        retrieved_data.append(item_str)
      
    formatted="\n---\n".join(retrieved_data)
    return formatted
##calling bedrock
def call_bedrock(message,system_prompt):
    response=bedrock.converse(
        modelId=model_id,
        messages=message,
        system=[{"text": system_prompt}],
        )
    response_body=response["output"]["message"]["content"][0]["text"]
    return response_body
##storing the chat memory
store={}
def get_chat_history(session_id):
    if session_id not in store:
        store[session_id]=ChatMessageHistory()
    return store[session_id]
## build the prompt message 
def build_prompt(history,query,context):
    messages=[]
    #current user input and context
    instruction=f"""
          User Query:{query}
          Context:{context}
         INSTRUCTIONS:
- "headline": a concise title summarizing the main news
- "date": use the most recent article date (YYYY-MM-DD)
- "points": 3–5 short bullet points highlighting key news
- "articles": include 3–5 relevant articles with title and URL
- "summary": short explanatory sentences for each key story
IMPORTANT RULES:
- Return ONLY valid JSON
- Do NOT include markdown, explanations, or extra text
- Do NOT wrap the JSON in backticks
- Do NOT include any text before or after the JSON
- Ensure the JSON is syntactically correct
- Use double quotes for all keys and strings
- Do not include trailing commas
Return:
- A valid JSON array of objects where each object has: "headline", "date", "source_link", and "summary".
- Do not include any other text, markdown, or headers outside of the JSON block.
-If information is missing, return cant find the source.
         """
    
    messages.append(
        { "role":"user",
          "content":[{"text":instruction}]
        })
    #past chat history
    for msg in history.messages[-5:]:
        messages.append({
            "role":"user" if msg.type == "human" else "assistant",
            "content":[{"text": msg.content}]
        })
    return messages

##generating the result
def lambda_handler(event, lambda_context):
    query = event.get("query")
    session_id=event.get("session_id") or str(uuid.uuid4())
    print(f"Query received: {query}")

    retrieved_context = Retrieve(query)
    memory=get_chat_history(session_id)
    message=build_prompt(memory, query, retrieved_context)
    system_prompt="You are a professional global news assistant"
    response=call_bedrock(message,system_prompt)
    #save the current chat
    memory.add_user_message(query)
    memory.add_ai_message(response)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "response": response
        })
    }
