# 🗞️ RTE News Bot

A production-style serverless RAG (Retrieval-Augmented Generation) pipeline that ingests live Irish news from RTE, stores it as semantic vectors, and answers natural language queries using AWS Bedrock.

Built with **AWS Lambda · Bedrock · Pinecone · EventBridge · SAM · Python 3.10**

---

## 🏗️ Architecture

Three independent Lambda functions, each with a single responsibility:

| Lambda | File | Trigger | Responsibility |
|---|---|---|---|
| Ingestion | `news_update.py` | EventBridge (every 4 hrs) | Fetch RTE RSS → chunk → embed → store in Pinecone |
| Query | `app.py` | API Gateway POST `/query` | Retrieve relevant vectors → generate answer via Bedrock LLM |
| Cleanup | `delete_news.py` | EventBridge (daily) | Delete vectors older than 24 hrs to keep index fresh |

```
EventBridge (4hr)
      │
      ▼
  Ingestion Lambda
      │  RSS → chunk → embed
      ▼
  Pinecone Vector DB ◄────── Query Lambda ◄── API Gateway ◄── User
                                  │
                                  ▼
                            Bedrock LLM
                                  │
                                  ▼
                          Structured JSON Response

EventBridge (daily)
      │
      ▼
  Cleanup Lambda
      │  delete vectors > 24hrs
      ▼
  Pinecone Vector DB
```

---

## ✨ Features

- **Live news ingestion** — RTE RSS feed auto-refreshed every 4 hours
- **Semantic search** — Pinecone vector DB with Bedrock Titan embeddings
- **Contextual answers** — AWS Bedrock LLM with retrieved news as context
- **Auto-cleanup** — old vectors deleted daily, keeping the index lean and current
- **Two deployment modes** — fully serverless (AWS) or hybrid (local cron + Lambda)
- **Structured responses** — returns JSON with headline, date, points, summary, and source links

---

## 🔄 Deployment Modes

### ☁️ Fully Serverless (Recommended)
Everything runs on AWS. EventBridge schedules ingestion and cleanup automatically.

```
EventBridge → Ingestion Lambda → Pinecone → Bedrock
EventBridge → Cleanup Lambda  → Pinecone
API Gateway → Query Lambda    → Pinecone + Bedrock → Response
```

### 🖥️ Hybrid (Local + Cloud)
Run ingestion and cleanup locally via cron. Use Lambda only for query handling. Good for development and testing.

```
Local Cron → news_update.py → Pinecone
Local Cron → delete_news.py → Pinecone
API Gateway → Query Lambda  → Pinecone + Bedrock → Response
```

Example cron (runs ingestion every 4 hours):
```
0 */4 * * * python hello_world/ingestion/news_update.py
```

---

## 📁 Project Structure

```
Rte-News-Bot/
│
├── hello_world/
│   ├── ingestion/
│   │   ├── news_update.py      # Ingestion Lambda — RSS → chunk → embed → Pinecone
│   │   └── requirements.txt
│   ├── query/
│   │   ├── app.py              # Query Lambda — RAG retrieval + Bedrock LLM
│   │   └── requirements.txt
│   └── cleanup/
│       ├── delete_news.py      # Cleanup Lambda — delete vectors older than 24hr
│       └── requirements.txt
│
├── template.yaml               # AWS SAM template (all 3 Lambdas + EventBridge)
├── samconfig.toml              # SAM deployment config
├── event.json                  # Test event for local Lambda invocation
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- AWS CLI configured (`aws configure`)
- AWS SAM CLI installed
- Docker (required for `sam build --use-container`)
- Pinecone account + API key
- AWS Bedrock access enabled in your region


### 1. Set up environment variables
Create a `.env` file in the root:
```
PINECONE_API_KEY=your_pinecone_api_key
MODEL_ID=your_bedrock_model_id
AWS_REGION= region
INDEX_NAME=pincone index name
```
> ⚠️ Never commit your `.env` file. Make sure it is in `.gitignore`.

### 2. Build with SAM
```bash
sam build --use-container
```
> Using `--use-container` ensures dependencies are built for the correct Lambda runtime (Amazon Linux), avoiding platform compatibility issues.

### 3. Deploy
```bash
sam deploy --guided
```
SAM will prompt you for stack name, region, and confirmation. After deploy, the API Gateway URL is printed in the outputs — save this as your query endpoint.

### 4. Test locally
```bash
# Test query Lambda locally
sam local invoke QueryFunction --event event.json

# Test ingestion Lambda locally
sam local invoke IngestionFunction 

# Test cleanup Lambda locally
sam local invoke CleanupFunction ```

---

## 📬 API Usage

**Endpoint:** `POST /query`

**Request body:**
```json
{
  "query": "What is the latest news about Ireland?",
}
```

**Response:**
```json
{
  "statusCode": 200,
  "body": {
    "response": {
      "headline": "Top Global News for 2026-05-02",
      "date": "2026-05-02",
      "points": [
        "Key news point 1...",
        "Key news point 2..."
      ],
      "articles": [
        {
          "title": "Article title",
          "url": "https://www.rte.ie/news/..."
        }
      ],
      "summary": "Today's top stories include..."
    }
  }
}
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Cloud & Serverless | AWS Lambda, EventBridge, API Gateway, SAM |
| Embeddings | AWS Bedrock — Titan Embed Text v2 |
| LLM | AWS Bedrock (configurable via `MODEL_ID`) |
| Vector DB | Pinecone (Serverless, cosine similarity, 1024 dims) |
| News Source | RTE RSS Feed via feedparser |
| Text Splitting | LangChain Text Splitters |
| Language | Python 3.10 |

---

## ⚠️ Known Limitations

- **Chat memory is in-memory only** — conversation history resets on Lambda cold start. DynamoDB integration planned.
- **Single news source** — currently ingests RTE only. Multi-source support on the roadmap.

---

## 🗺️ Future Improvments

- [ ] Store chat history in DynamoDB for persistent sessions
- [ ] Add React or Streamlit chat UI
- [ ] Expand to multiple news sources (BBC, Irish Times)
- [ ] Add multilingual support

---

## 👩‍💻 Author

**Vaibha Ragavan** — AI/ML Engineer  
[GitHub](https://github.com/VaibhaRagavan) · [LinkedIn](https://www.linkedin.com/in/vaibha-ragavan)
