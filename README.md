
# Bug Triage Machine Learning API

A high-throughput, asynchronous RESTful API that automatically classifies software bug reports into their respective architectural components using a pre trained machine learning model. Built with FastAPI and PostgreSQL, this system is optimized for low latency inference and non blocking database telemetry.

## Features
* **Stateless Machine Learning:** Artifacts (`.pkl` files) are loaded into memory exactly once during the server lifespan, preventing I/O bottlenecks and memory leaks.
* **Asynchronous Telemetry:** Utilizes connection pooling via `asyncpg` to log inference metrics to a local PostgreSQL database without blocking the API event loop.
* **Robust Data Validation:** Enforces strict payload contracts using Pydantic to protect the inference engine from malformed requests.
* **Load Tested:** Handle concurrent traffic with sub-10ms latency using Locust.

## Prerequisites
* Python 3.14+
* PostgreSQL 14+

## Installation & Setup

**1. Clone and Initialize Environment**
```bash
git clone https://github.com/amz202/BugTriageAPI
cd BugTriageAPI
python -m venv .venv
source .venv/bin/activate
```

**2. Install Dependencies**
```bash
pip install -r requirements.txt
```

**3. Database Configuration**
Initialize your local PostgreSQL instance and create the required user and database.

```bash
sudo -u postgres psql -c "CREATE USER bug_user WITH PASSWORD 'admin';"
sudo -u postgres psql -c "CREATE DATABASE bugtriage OWNER bug_user;"
```

Connect to the new database (`psql -h 127.0.0.1 -U bug_user -d bugtriage`) and execute the schema definition:

```sql
CREATE TABLE prediction_logs (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  created_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL,
  issue_title text NOT NULL,
  description text NOT NULL,
  predicted_component text NOT NULL,
  confidence_score double precision NOT NULL,
  execution_time_ms double precision NOT NULL
);
```

## Execution

Start the ASGI server. The application will automatically load the machine learning artifacts and initialize the database connection pool.

```bash
python -m uvicorn app.main:app --reload
```
The API documentation will be available at: `http://127.0.0.1:8000/docs`

## API Reference

### Predict Component
Evaluates a bug report and returns the predicted system component.

**Endpoint:** `POST /api/v1/predict`

**Request Payload:**
```json
{
  "issue_title": "UI freezes when clicking the submit button",
  "description": "When navigating to the dashboard and clicking submit, the page becomes unresponsive for 5 seconds.",
  "reported_time": "2026-03-29T10:00:00Z"
}
```

**Response:**
```json
{
  "status": "success",
  "predicted_component": "ui",
  "confidence_score": 0.8578,
  "log_id": "a1b2c3d4-e5f6-7890-1234-56789abcdef0",
  "metadata": {
    "execution_time_ms": 2.48
  }
}
```

## Stress Testing

This project includes a Locust configuration to verify system throughput and identify IO bottlenecks.

1. Ensure the FastAPI server is running.
2. Open a new terminal and activate the virtual environment.
3. Execute the load generator:
```bash
locust -f locustfile.py
```
4. Navigate to `http://localhost:8089` to configure and initiate the swarm. 

***

