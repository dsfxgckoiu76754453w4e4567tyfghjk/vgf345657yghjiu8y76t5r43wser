# Phase 2: RAG Pipeline - Complete Guide

## 🎉 Phase 2 Implementation Complete!

Phase 2 adds the complete RAG (Retrieval-Augmented Generation) pipeline with:
- ✅ **Qdrant** vector database integration
- ✅ **Chonkie** intelligent text chunking
- ✅ **Multi-provider embeddings** (Gemini/Cohere)
- ✅ **Semantic search** with filtering
- ✅ **LangGraph** orchestration
- ✅ **Document processing** pipeline

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
poetry install
```

### 2. Start Infrastructure

```bash
# Start PostgreSQL, Redis, and Qdrant
docker-compose up -d postgres redis qdrant

# Wait for services to be ready
sleep 30
```

### 3. Run Database Migrations

```bash
# Create initial migration
poetry run alembic revision --autogenerate -m "Initial schema with Phase 1 and 2 models"

# Run migrations
poetry run alembic upgrade head
```

### 4. Set Up Environment Variables

Ensure your `.env` file has:

```bash
# LLM Providers (at least one required)
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key

# Google for embeddings
GOOGLE_API_KEY=your-google-key

# Or Cohere for embeddings
COHERE_API_KEY=your-cohere-key

# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION_NAME=islamic_knowledge

# Embeddings configuration
EMBEDDING_PROVIDER=gemini  # or cohere
EMBEDDING_MODEL=gemini-embedding-001
EMBEDDING_DIMENSION=3072

# Chunking configuration
CHUNKING_STRATEGY=semantic  # semantic, token, sentence, adaptive
CHUNK_SIZE=768
CHUNK_OVERLAP=150
```

### 5. Start the Application

```bash
poetry run dev
```

The API will be available at `http://localhost:8000`

---

## 📚 What's Been Implemented

### 1. **Qdrant Vector Database** (`src/app/services/qdrant_service.py`)

Full Qdrant integration with:

- ✅ Collection management
- ✅ Binary quantization (40x performance boost)
- ✅ Point insertion/deletion
- ✅ Semantic search with filters
- ✅ Collection info and status

**Key Features:**
```python
# Create collection
await qdrant_service.ensure_collection_exists(
    vector_size=3072,
    distance=Distance.COSINE
)

# Search with filters
results = await qdrant_service.search(
    query_vector=embedding,
    limit=10,
    score_threshold=0.7,
    filter_conditions={"language": "fa"}
)
```

### 2. **Chonkie Chunking Service** (`src/app/services/chonkie_service.py`)

Intelligent text chunking using **Chonkie library** (NOT traditional text splitters):

**Supported Strategies:**
- ✅ **Semantic** - Context-aware, meaning-preserving chunks
- ✅ **Token** - Precise token-based splitting
- ✅ **Sentence** - Sentence boundary preservation
- ✅ **Adaptive** - Automatic strategy selection

**Usage:**
```python
chunks = chonkie_service.chunk_text(
    text=document_content,
    strategy="semantic",
    chunk_size=768,
    overlap=150,
    language="fa"
)
```

**Why Chonkie?**
- 🎯 Semantic awareness - preserves meaning
- 🌍 Multilingual support (56+ languages including Persian & Arabic)
- 📊 Optimized for RAG retrieval
- ⚡ Performance optimized

### 3. **Embeddings Service** (`src/app/services/embeddings_service.py`)

Multi-provider embedding generation:

**Supported Providers:**
- ✅ **Gemini** (Google Generative AI)
  - Model: `gemini-embedding-001`
  - Dimension: 3072
  - Cost: ~$0.00001 per 1K chars

- ✅ **Cohere**
  - Model: `embed-multilingual-v4.0`
  - Dimension: 1536
  - Cost: ~$0.0001 per 1K tokens

**Usage:**
```python
# Single text
embedding = await embeddings_service.embed_text("Your text here")

# Batch processing
embeddings = await embeddings_service.embed_documents([text1, text2, text3])

# Cost estimation
cost = embeddings_service.estimate_cost(len(text))
```

### 4. **Document Processing Service** (`src/app/services/document_service.py`)

Complete document upload and processing pipeline:

**Features:**
- ✅ Document upload
- ✅ Automatic chunking with Chonkie
- ✅ Embedding generation
- ✅ Vector storage in Qdrant
- ✅ Semantic search
- ✅ Chunk approval workflow

**Workflow:**
1. Upload document → Create `Document` record
2. Chunk with Chonkie → Create `DocumentChunk` records
3. Generate embeddings → Create `DocumentEmbedding` records
4. Store in Qdrant → Ready for retrieval

### 5. **LangGraph Orchestration** (`src/app/services/langgraph_service.py`)

RAG workflow orchestration with state management:

**Graph Flow:**
```
User Query
    ↓
[Classify Intent] → Determine query type (general_qa, ahkam, hadith, etc.)
    ↓
[Should Retrieve?] → Check if RAG is needed
    ↓
[Retrieve Chunks] → Semantic search (if needed)
    ↓
[Generate Response] → LLM with context
    ↓
Response + Sources
```

**Features:**
- ✅ Intent classification
- ✅ Conditional RAG retrieval
- ✅ Multi-provider LLM support (OpenAI, Anthropic)
- ✅ State management
- ✅ Streaming support (ready)

---

## 🔌 API Endpoints

### Document Upload

**POST** `/api/v1/documents/upload`

Upload and process a document with automatic chunking.

**Request:**
```json
{
  "title": "Sahih al-Kafi - Volume 1",
  "content": "Full text content here...",
  "document_type": "hadith",
  "primary_category": "fiqh",
  "language": "fa",
  "author": "Sheikh al-Kulayni",
  "chunking_strategy": "semantic",
  "chunk_size": 768,
  "chunk_overlap": 150
}
```

**Response:**
```json
{
  "code": "DOCUMENT_UPLOAD_SUCCESS",
  "message": "Document uploaded successfully. 45 chunks created.",
  "document": {
    "id": "uuid",
    "title": "Sahih al-Kafi - Volume 1",
    "chunk_count": 45,
    "processing_status": "awaiting_chunk_approval"
  }
}
```

### Generate Embeddings

**POST** `/api/v1/documents/embeddings/generate`

Generate vector embeddings for a document.

**Request:**
```json
{
  "document_id": "document-uuid-here"
}
```

**Response:**
```json
{
  "code": "EMBEDDINGS_GENERATION_SUCCESS",
  "message": "Generated 45 embeddings for document",
  "document_id": "document-uuid-here",
  "embeddings_count": 45
}
```

### Semantic Search

**POST** `/api/v1/documents/search`

Search documents using semantic similarity.

**Request:**
```json
{
  "query": "What is the ruling on prayer times?",
  "limit": 10,
  "score_threshold": 0.7,
  "document_type": "fiqh",
  "language": "fa"
}
```

**Response:**
```json
{
  "code": "SEARCH_SUCCESS",
  "message": "Search completed successfully",
  "query": "What is the ruling on prayer times?",
  "results": [
    {
      "chunk_id": "chunk-uuid",
      "document_id": "doc-uuid",
      "text": "Relevant text chunk...",
      "score": 0.89,
      "index": 5
    }
  ],
  "count": 10
}
```

### Qdrant Status

**GET** `/api/v1/documents/qdrant/status`

Get Qdrant collection status.

**Response:**
```json
{
  "code": "QDRANT_STATUS_SUCCESS",
  "message": "Qdrant status retrieved",
  "collection": {
    "name": "islamic_knowledge",
    "points_count": 1250,
    "vectors_count": 1250,
    "status": "green"
  }
}
```

---

## 🧪 Testing the RAG Pipeline

### 1. Test Document Upload

```bash
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Islamic Document",
    "content": "This is a test document about Islamic knowledge. It discusses various topics including prayer, fasting, and zakat. The document contains detailed explanations and references to authentic sources.",
    "document_type": "article",
    "primary_category": "fiqh",
    "language": "en",
    "chunking_strategy": "semantic"
  }'
```

### 2. Generate Embeddings

```bash
curl -X POST http://localhost:8000/api/v1/documents/embeddings/generate \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "DOCUMENT_ID_FROM_STEP_1"
  }'
```

### 3. Semantic Search

```bash
curl -X POST http://localhost:8000/api/v1/documents/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the rules for prayer?",
    "limit": 5,
    "score_threshold": 0.7
  }'
```

### 4. Check Qdrant Status

```bash
curl -X GET http://localhost:8000/api/v1/documents/qdrant/status \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## 🏗️ Architecture Highlights

### Vector DB Abstraction

The system uses a **vector DB abstraction layer** (not tied to Qdrant):

```python
# DocumentEmbedding model
vector_db_type: str  # qdrant, elasticsearch, milvus, etc.
vector_db_collection_name: str
vector_db_point_id: UUID
vector_db_metadata: JSONB
```

**This allows easy migration** to other vector databases in the future.

### Chonkie vs Traditional Chunking

**❌ Traditional (LangChain):**
```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(chunk_size=1000)
chunks = splitter.split_text(text)
```

**✅ Chonkie (Our Implementation):**
```python
from chonkie import SemanticChunker

chunker = SemanticChunker(chunk_size=768)
chunks = chunker.chunk(text)  # Semantic-aware!
```

**Benefits:**
- Preserves semantic meaning
- Better retrieval quality
- Multilingual support
- Context-aware boundaries

---

## 📊 Database Schema Updates

### New Tables (Phase 2)

All Phase 2 tables were already defined in Phase 1:
- ✅ `documents` - Document metadata
- ✅ `document_chunks` - Chonkie-generated chunks
- ✅ `document_embeddings` - Vector embeddings with DB abstraction

### Example Queries

```sql
-- Find all documents with chunks
SELECT d.title, d.chunk_count, d.processing_status
FROM documents d
WHERE d.chunk_count > 0;

-- Get chunks for a document
SELECT dc.chunk_index, dc.chunk_text, dc.char_count
FROM document_chunks dc
WHERE dc.document_id = 'document-uuid'
ORDER BY dc.chunk_index;

-- Check embedding coverage
SELECT
    d.title,
    COUNT(de.id) as embeddings_count,
    de.embedding_model
FROM documents d
LEFT JOIN document_chunks dc ON dc.document_id = d.id
LEFT JOIN document_embeddings de ON de.chunk_id = dc.id
GROUP BY d.id, de.embedding_model;
```

---

## 🔧 Configuration Options

### Chunking Strategies

| Strategy | Best For | Use Case |
|----------|----------|----------|
| `semantic` | Long documents, books | Preserves meaning and context |
| `token` | API limits, precise control | Token-aware splitting |
| `sentence` | Short documents | Maintains readability |
| `adaptive` | Mixed content | Auto-selects best strategy |

### Embedding Providers

| Provider | Model | Dimension | Cost (per 1K) | Best For |
|----------|-------|-----------|---------------|----------|
| Gemini | `gemini-embedding-001` | 3072 | $0.00001 | Multilingual, low cost |
| Cohere | `embed-multilingual-v4.0` | 1536 | $0.0001 | High quality, multilingual |

---

## 🚨 Important Notes

### 1. Chonkie is Required

**CRITICAL:** Use Chonkie for chunking, NOT traditional LangChain text splitters.

```python
# ❌ DON'T DO THIS
from langchain.text_splitter import CharacterTextSplitter

# ✅ DO THIS
from app.services.chonkie_service import chonkie_service
```

### 2. Vector DB Abstraction

Always use the abstraction layer - don't hardcode Qdrant-specific logic:

```python
# ✅ GOOD - Uses abstraction
embedding_record = DocumentEmbedding(
    vector_db_type="qdrant",  # Can be changed
    vector_db_collection_name=collection,
    vector_db_point_id=point_id
)
```

### 3. Batch Processing

For large documents, process in batches:

```python
# Process 100 chunks at a time
for i in range(0, len(chunks), 100):
    batch = chunks[i:i+100]
    await process_batch(batch)
```

---

## ✅ Phase 2 Completion Checklist

- [x] Qdrant client with binary quantization
- [x] Chonkie integration (semantic, token, sentence, adaptive)
- [x] Multi-provider embeddings (Gemini, Cohere)
- [x] Document upload endpoint
- [x] Embedding generation endpoint
- [x] Semantic search endpoint
- [x] LangGraph orchestration basics
- [x] Vector DB abstraction layer
- [x] Comprehensive error handling
- [x] Structured logging

---

## 🎯 Next Steps - Phase 3: Specialized Tools

**Duration:** 3-4 weeks

### Upcoming Features

1. **Ahkam Tool** ⚠️ CRITICAL
   - Fetch from official Marja websites (NOT RAG)
   - Web scraping with rate limiting
   - Admin configuration UI

2. **Hadith Lookup Tool**
   - Search by reference, text, or narrator
   - Chain (sanad) display
   - Reliability analysis

3. **Other Tools**
   - DateTime calculator (prayer times)
   - Math calculator (zakat, khums) with warnings
   - Comparison tool (Marja opinions)

4. **Multi-Tool Orchestration**
   - One query → multiple tools
   - Parallel/sequential execution

See `docs/implementation/20-IMPLEMENTATION-ROADMAP.md` for complete Phase 3 details.

---

## 📞 Support

- **Documentation:** `docs/implementation/`
- **Phase 2 Details:** `docs/implementation/20-IMPLEMENTATION-ROADMAP.md` (lines 97-165)
- **Chonkie Docs:** https://docs.chonkie.ai

---

**Phase 2 Status:** ✅ Complete
**Next Phase:** Phase 3 - Specialized Tools (Ahkam, Hadith, etc.)
**Timeline:** 9-12 weeks remaining

Great progress! The RAG pipeline is fully functional and ready for production use. 🚀
