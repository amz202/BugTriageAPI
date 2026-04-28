# BugTriageAPI

An issue tracking backend powered by asynchronous Python and a multi-task deep learning pipeline. BugTriageAPI automates the ingestion, classification, and routing of system bug reports to appropriately skilled engineering teams.

## System Overview

Incoming bug reports are processed through a customized CodeBERT model. The system infers the affected technical component, urgency level, and estimated resolution time. Based on the model's confidence threshold, the API dynamically routes the ticket to a verified developer possessing the corresponding expertise label, or flags it for manual human triage.

## Deep Learning Pipeline

The machine learning infrastructure is designed for asynchronous, non-blocking execution within the FastAPI event loop.

* **Model Architecture:** Multi-task CodeBERT.
* **Runtime:** Thread-safe ONNX Runtime (`onnxruntime`) executing via `asyncio.to_thread` to preserve API concurrency.
* **Inference Outputs:**
    * **Component Prediction:** Classifies the issue into specific subsystems (e.g., `browser_core`, `network`, `ui`). Includes dynamic fallback logic to safely default unknown indices to `other`.
    * **Priority Level:** Assesses urgency from `P0` to `P3`.
    * **Resolution Time:** A regression output estimating the required days to fix the bug.
    * **Attention Weights:** Extracts Byte-Pair Encoding (BPE) tokens and their corresponding attention weights to facilitate frontend explainability (e.g., UI heatmaps).
* **Routing Logic:** Predictions with a confidence score $\ge 0.75$ trigger automatic assignment to developers matching the predicted label. Scores below this threshold assign the ticket a `manual_review` status.

## Technology Stack

* **Framework:** FastAPI (Python)
* **Database:** PostgreSQL with `asyncpg`
* **ORM & Migrations:** SQLAlchemy (Asynchronous) and Alembic
* **Machine Learning:** Hugging Face `transformers` (Tokenizer) and `onnxruntime`
* **Security:** Passlib (Bcrypt) and python-jose (JWT)
* **Architecture:** Clean Architecture with strict Pydantic v2 data validation boundaries.

---

## Authentication Protocol

The API utilizes stateless JSON Web Tokens (JWT) for Identity and Access Management. 
* **Global Protection:** With the exception of registration and login, all endpoints require a valid JWT.
* **Header Requirement:** Authenticated requests must include the token in the headers as: `Authorization: Bearer <your_access_token>`.

---

## API Endpoints Reference

### 1. Authentication Identity (`/api/v1/auth`)
* `POST /register`: Provisions a new developer account and hashes the password via bcrypt.
    * **Payload:** `{ "email": "user@example.com", "password": "strongpassword" }`
* `POST /login`: Authenticates credentials and issues a signed access token.
    * **Payload:** `{ "email": "user@example.com", "password": "strongpassword" }`
    * **Returns:** `{ "access_token": "eyJ...", "token_type": "bearer" }`

### 2. Teams & Expertise (`/api/v1/teams` & `/api/v1/labels`)
* `POST /api/v1/teams`: Provisions a new organizational team.
* `GET /api/v1/teams`: Retrieves an array of all organizational teams.
* `GET /api/v1/labels`: Retrieves an array of system labels (e.g., `network`, `ui`) that map directly to ML component predictions.
* `POST /api/v1/users/{user_id}/labels`: Binds an expertise label to a developer to enable automated ML routing.
    * **Payload:** `{ "label_id": "uuid" }`

### 3. Ticket Management (`/api/v1/tickets`)
* `POST /tickets`: Ingests a new ticket, executes CodeBERT inference, and automatically assigns it to a user possessing the matching expertise label based on the confidence threshold.
    * **Payload:** `{ "title": "...", "description": "...", "reported_time": "optional_iso_timestamp" }`
* `GET /tickets`: Retrieves a paginated array of tickets. Deliberately excludes heavy ML JSON payloads (attention weights) to optimize list rendering performance.
    * **Query Params:** `?skip=0&limit=20`
* `GET /tickets/{ticket_id}`: Retrieves full diagnostic data, including CodeBERT attention weights required for frontend visualization.
* `PATCH /tickets/{ticket_id}`: Overrides the ML prediction for manual triage, reassignment, or status updates.

### 4. Collaboration (`/api/v1/tickets`)
* `POST /tickets/{ticket_id}/comments`: Appends a text comment to the ticket thread. The author ID is extracted securely from the Bearer token.
    * **Payload:** `{ "text": "Investigating this stack trace now." }`

### 5. Analytics (`/api/v1/analytics`)
* `GET /analytics/overview`: Retrieves aggregated dashboard metrics including total tickets, pending triage count, average ML confidence, and average predicted resolution days.

---

## Setup and Installation

**1. Environment Initialization**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**2. Artifact Placement**
Ensure the multi-task CodeBERT artifacts are placed in the correct directory. Do not commit these binary files to version control.
```text
app/artifacts/codebert_multitask.onnx
app/artifacts/codebert_multitask.onnx.data
```

**3. Database Configuration**
Define your asynchronous PostgreSQL connection string in your local `.env` file or environment variables:
`DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/bugtriage`

**4. Execute Migrations**
Apply the SQLAlchemy schemas to your PostgreSQL database.
```bash
alembic upgrade head
```

**5. Initialize Server**
```bash
uvicorn app.main:app --reload
```