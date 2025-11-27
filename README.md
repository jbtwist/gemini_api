# Agile Monkeys Assessment - Gemini API Integration

A FastAPI application that integrates with Google's Gemini API to provide document upload, validation, and intelligent search capabilities across user files.

## 📋 Table of Contents

- [Requirements](#requirements)
- [Installation](#installation)
  - [macOS](#macos)
  - [Linux](#linux)
- [Architecture](#architecture)
- [Configuration](#configuration)
- [How to Use](#how-to-use)
- [API Endpoints](#api-endpoints)
- [Testing](#testing)
- [Production Deployment](#production-deployment)
- [Future Improvements](#future-improvements)

## 🔧 Requirements

- **Python 3.12+**
- **libmagic** - For MIME type detection
- **uv** - Fast Python package installer and resolver
- **Google Gemini API Key**

## 📦 Installation

### Clone the Repository

```bash
git clone <repository-url>
cd gemini_api
```

### macOS

1. **Install Homebrew** (if not already installed):
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **Install Python 3.12+**:
   ```bash
   brew install python@3.12
   ```

3. **Install libmagic**:
   ```bash
   brew install libmagic
   ```

4. **Install uv**:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
   Or via Homebrew:
   ```bash
   brew install uv
   ```

5. **Set up the project**:
   ```bash
   uv venv
   source .venv/bin/activate 
   uv sync
   ```

### Linux (Ubuntu/Debian)

1. **Update package list**:
   ```bash
   sudo apt update
   ```

2. **Install Python 3.12+**:
   ```bash
   sudo apt install python3.12 python3.12-venv python3-pip
   ```

3. **Install libmagic**:
   ```bash
   sudo apt install libmagic1
   ```

4. **Install uv**:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
   Or via pip:
   ```bash
   pip install uv
   ```

5. **Set up the project**:
   ```bash
   uv venv
   source .venv/bin/activate 
   uv sync
   ```

### Linux (RHEL/Fedora/CentOS)

1. **Install Python 3.12+**:
   ```bash
   sudo dnf install python3.12
   ```

2. **Install libmagic**:
   ```bash
   sudo dnf install file-libs
   ```

3. **Install uv and set up project** (same as above)

## 🏗️ Architecture

This project follows a clean, layered architecture designed for clarity and maintainability:

```
gemini_api/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── common/
│   │   ├── constants.py        # Global constants and in-memory stores
│   │   └── settings.py         # Environment configuration
│   └── routers/
│       └── documents_router.py # Document upload/search endpoints
├── services/
│   ├── chat_services.py        # Chat business logic
│   └── documents_services.py   # Document processing logic
├── tests/                      # Unit and integration tests
├── pyproject.toml             # Project dependencies and configuration
└── README.md
```

### Design Decisions

- **Simple Architecture**: Focus on API functionality over complex infrastructure
- **Service Layer Pattern**: Business logic separated from routing
- **In-Memory Storage**: Uses global variables to simulate database + cache (development only)

> ⚠️ **Note**: The use of global variables (`PROJECT_FILE_STORE`, `CONVERSATION_HISTORY`) is intentional for development. In production, these should be replaced with a proper database (PostgreSQL) and cache (Redis).

## ⚙️ Configuration

Create a `.env` file in the project root:

```env
# Required
GEMINI_API_KEY=your_gemini_api_key_here

# Optional - File Upload Settings
MAX_FILE_SIZE=10485760  # 10MB in bytes
ALLOWED_EXTENSIONS=pdf,txt,doc,docx,md
ALLOWED_MIME_TYPES=application/pdf,text/plain,application/msword
```

Get your Gemini API key from: [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)

## 🚀 How to Use

### Start the Server

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Interactive API Documentation

Open your browser and navigate to:
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## 📡 API Endpoints

#### Send a Message
```bash
curl -X POST "http://127.0.0.1:8000/chat/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the capital of France?"
  }'
```

#### Get Conversation History
```bash
curl -X GET "http://127.0.0.1:8000/chat/history"
```

#### Clear Conversation
```bash
curl -X DELETE "http://127.0.0.1:8000/chat/clear"
```

### Document Endpoints

#### Upload Documents
```bash
curl -X POST "http://127.0.0.1:8000/documents/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "files=@/path/to/document1.pdf" \
  -F "files=@/path/to/document2.txt"
```

#### Search Documents
```bash
curl -X POST "http://127.0.0.1:8000/documents/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the main topics discussed?"
  }'
```

#### List Uploaded Documents
```bash
curl -X GET "http://127.0.0.1:8000/documents/list"
```

#### Health Check
```bash
curl -X GET "http://127.0.0.1:8000/health"
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov=services --cov-report=html

# Run specific test file
pytest tests/test_documents.py -v
```

View coverage report:
```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## 🚢 Production Deployment

### Prerequisites for Production

1. **Database Setup** (PostgreSQL)
2. **Cache Setup** (Redis)
3. **Object Storage** (AWS S3, Google Cloud Storage, or MinIO)


## 🔮 Future Improvements

### Critical for Production

1. **Database Integration**
   - Replace in-memory stores with PostgreSQL
   - Implement proper schema migrations (Alembic)
   - Store file metadata and conversation history

2. **Caching Strategy**
   - Implement Redis for:
     - API rate limiting
     - Conversation history caching
     - File metadata caching
   - Reduce Gemini API calls with smart caching

3. **Blob Storage**
   - Migrate from in-memory storage to S3/GCS
   - Store only metadata in database
   - Implement signed URLs for secure file access

4. **CORS Configuration**
   - Configure proper CORS policies
   - Whitelist specific origins
   - Set appropriate headers

5. **Authentication & Authorization**
   - JWT-based authentication
   - User management
   - Role-based access control

### Nice to Have

6. **Containerization & Orchestration**
   - **Docker Image**: Create optimized multi-stage Dockerfile for smaller images
   - **Docker Compose**: Complete stack with API, PostgreSQ and Redis
   - **Kubernetes Deployment**: 
     - Helm charts for easy deployment
     - Horizontal Pod Autoscaling (HPA)
     - ConfigMaps and Secrets management
     - Ingress configuration with TLS
     - Resource limits and health checks
     - StatefulSets for database
     - Persistent Volume Claims for file storage

7. **Monitoring & Logging**
   - Structured logging (JSON format)
   - Application Performance Monitoring (APM)
   - Error tracking (Sentry)

8. **API Improvements**
   - Rate limiting per user
   - Pagination for large result sets
   - Webhook support for async operations
   - GraphQL alternative endpoint

