# DeepInsight - AI-Powered Business Intelligence Platform

DeepInsight transforms organizational knowledge capture through intelligent employee questionnaires and automated wiki generation. Drawing inspiration from [Cognition's DeepWiki](https://deepwiki.com/) which creates "up-to-date documentation you can talk to" for codebases, DeepInsight applies this same conversational AI approach to business intelligence and organizational knowledge.

Where DeepWiki revolutionizes technical documentation by making GitHub repositories accessible through AI-powered interfaces, DeepInsight revolutionizes business documentation by making organizational knowledge accessible through intelligent questionnaire systems. The platform enables administrators to create question series distributed via email to employees, who respond through an intelligent omnibox interface supporting text, file uploads, and employee references. AI agents automatically generate contextual follow-up questions and process all responses into comprehensive business wikis that document operational frameworks, processes, and personnel relationships.


## 🤖 AI Implementation & Methodology

### Intelligent Question Generation
- **LLM Integration**: Uses LiteLLM with support for multiple models (GPT, OpenRouter) for generating contextual follow-up questions
- **Conversation Context**: Maintains conversation history to generate relevant 1-2 follow-up questions based on employee responses
- **Response Analysis**: AI analyzes response completeness and automatically determines when additional clarification is needed

### Deep Agent Wiki Processing
The platform employs a sophisticated multi-agent approach for knowledge base generation:

#### Document Planning Agent
- Analyzes employee Q&A data to create structured navigation plans
- Uses prompt engineering to generate optimal documentation hierarchy (max 5 sections, 10 documents)
- Produces JSON navigation structures for MkDocs integration

#### Content Generation Agent  
- Transforms raw employee responses into coherent markdown documentation
- Employs narrative writing prompts for clear, plain English output
- Generates business overviews, team directories, process documentation, and systems maps

#### Wiki Assembly System
- Orchestrates parallel document creation using asyncio for performance
- Integrates with MkDocs Material theme for professional documentation presentation
- Supports Mermaid diagrams for organizational charts and system mapping

## 🏗️ Technical Architecture

### Backend (Python/FastAPI)
- **Framework**: FastAPI with async support for high-performance API endpoints
- **Database**: PostgreSQL with SQLModel ORM for type-safe database operations
- **AI/LLM**: LiteLLM for model-agnostic AI integration (supports GPT-4, OpenRouter, etc.)
- **Documentation**: MkDocs with Material theme for wiki generation
- **Testing**: Pytest with async support for comprehensive test coverage

### Frontend (Next.js/React)
- **Framework**: Next.js 15 with React 19 and TypeScript
- **UI Components**: Radix UI primitives with Shadcn/ui component library
- **Styling**: Tailwind CSS v4 with custom design system
- **Forms**: React Hook Form with Zod validation
- **State Management**: React hooks with server state synchronization

### Data Model
Core entities include:
- **Business**: Organization container with employees and questions
- **Employee**: User profiles with bio and business association  
- **Question**: Base questions and AI-generated follow-ups with ordering
- **Interview**: Session tracking for employee questionnaire completion
- **QuestionResponse**: Employee answers with metadata and relationships

### Infrastructure
- **Containerization**: Docker Compose for local development environment
- **Database Migrations**: Alembic for schema version management
- **Environment Management**: Poetry for Python dependencies, npm for Node.js
- **API Documentation**: OpenAPI/Swagger auto-generation from FastAPI

## 🚀 Getting Started

### Prerequisites
- Python 3.11-3.12
- Node.js 18+
- PostgreSQL 14+
- Poetry
- Docker (optional)

### Development Setup

1. **Clone and setup backend**:
```bash
cd backend
poetry install
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

2. **Setup frontend**:
```bash
cd frontend  
npm install
npm run dev
```

3. **Database setup**:
```bash
cd backend
poetry run alembic upgrade head
```

### Environment Configuration
Create `.env` in backend directory:
```env
INTERVIEW_MODEL=openai/gpt-4
WIKI_MODEL=openai/gpt-4
API_KEYS=your_provider_api_key_here
```

### API Endpoints
- Backend API: http://localhost:8000
- Frontend App: http://localhost:3000  
- API Documentation: http://localhost:8000/docs
- Generated Wikis: http://localhost:9000 (MkDocs)

## 📁 Project Structure

```
deep-insight/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── agents/         # AI agents and prompts
│   │   ├── controllers/    # API route handlers  
│   │   ├── services/       # Business logic
│   │   ├── models/         # Database models
│   │   └── main.py        # FastAPI application
│   ├── alembic/           # Database migrations
│   └── tests/             # Test suites
├── frontend/              # Next.js frontend
│   └── src/
│       ├── app/           # Next.js app router
│       └── components/    # React components
├── docs/                  # Generated documentation
└── docker-compose.yaml   # Development environment
```
