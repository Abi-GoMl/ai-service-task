# AI Service Desk

An AI-powered Service Desk API built using **FastAPI**, **PostgreSQL**, **SQLAlchemy**, and **Amazon Bedrock**. This project provides CRUD operations for support tickets, AI-assisted ticket analysis, Docker containerization, testing, and performance profiling.

---

## Features

- Create, Read, Update and Delete support tickets
- RESTful API using FastAPI
- PostgreSQL database
- SQLAlchemy Async ORM
- Pydantic Validation
- Docker Support
- Unit Testing
- Integration Testing
- Performance Profiling (cProfile)
- Load Testing (Locust)
- AI integration using Amazon Bedrock

---

## Tech Stack

- Python 3.12
- FastAPI
- PostgreSQL
- SQLAlchemy
- Pydantic
- Docker
- Pytest
- Locust
- Amazon Bedrock
- Uvicorn

---

## Project Structure

```
ai-service-desk/
│
├── app/
│   ├── api/
│   ├── core/
│   ├── db/
│   ├── models/
│   ├── repositories/
│   ├── schemas/
│   └── services/
│
├── test/
├── cprofile_results/
├── Dockerfile
├── requirements.txt
├── .env.example
├── main.py
└── README.md
```

---

## Installation

Clone the repository

```bash
git clone https://github.com/Abi-GoMl/ai-service-task.git
cd ai-service-task
```

Create a virtual environment

```bash
python -m venv .venv
```

Activate it

Windows

```bash
.venv\Scripts\activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

---

## Environment Variables

Create a `.env` file.

Example:

```env
APP_NAME=AI Service Desk
API_VERSION=v1
DEBUG=True

DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/ai_service_desk

SECRET_KEY=your_secret_key

ACCESS_TOKEN_EXPIRE_MINUTES=30

AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=ap-south-1
BEDROCK_MODEL_ID=amazon.titan-text-express-v1
```

> **Do NOT commit your real `.env` file to GitHub.**

---

## Run the Application

```bash
uvicorn main:app --reload
```

Application

```
http://localhost:8000
```

Swagger Documentation

```
http://localhost:8000/docs
```

ReDoc

```
http://localhost:8000/redoc
```

---

## Docker

Build the image

```bash
docker build -t ai-service-desk .
```

Run the container

```bash
docker run --env-file .env -p 8000:8000 ai-service-desk
```

---

## Running Tests

Unit Tests

```bash
pytest test/unit_test
```

Integration Tests

```bash
pytest test/integration_test
```

Run all tests

```bash
pytest
```

---

## Load Testing

```bash
locust
```

Open

```
http://localhost:8089
```

---

## Performance Profiling

Run

```bash
python cprofile_runner.py
```

Results are stored in

```
cprofile_results/
```

---

## API Endpoints

| Method | Endpoint | Description |
|---------|----------|-------------|
| GET | / | Home |
| POST | /tickets | Create Ticket |
| GET | /tickets | Get All Tickets |
| GET | /tickets/{id} | Get Ticket |
| PUT | /tickets/{id} | Update Ticket |
| DELETE | /tickets/{id} | Delete Ticket |

---

## Future Improvements

- JWT Authentication
- Role-Based Access Control
- CI/CD Pipeline
- Kubernetes Deployment
- Monitoring with Prometheus & Grafana
- API Rate Limiting

---

## Author

**Abinaya Kannan**

CSBS Student | FastAPI Developer | AI & Cloud Enthusiast