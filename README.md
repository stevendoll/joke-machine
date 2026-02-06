# Joke Machine API

A FastAPI application with POST endpoints for deployment on AWS Lambda using AWS SAM.

## Features

- **POST /joke** - Generate jokes based on type and category
- **POST /echo** - Generic echo endpoint for testing
- **GET /health** - Health check endpoint
- **GET /** - Root endpoint

## Local Development

### Prerequisites
- Python 3.11+
- Docker (optional)

### Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run locally:
```bash
python main.py
```

Or using uvicorn directly:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Testing the API

#### POST /joke
```bash
curl -X POST "http://localhost:8000/joke" \
     -H "Content-Type: application/json" \
     -d '{"type": "tech", "category": "programming"}'
```

#### POST /echo
```bash
curl -X POST "http://localhost:8000/echo" \
     -H "Content-Type: application/json" \
     -d '{"message": "Hello World", "data": {"key": "value"}}'
```

## AWS Deployment

### Prerequisites
- AWS CLI configured
- AWS SAM CLI installed
- Docker installed

### Deployment Steps

1. Build the application:
```bash
sam build --use-container
```

2. Deploy to AWS:
```bash
sam deploy --guided
```

This will prompt you for:
- Stack name
- AWS region
- Parameter values
- Confirmation before deployment

### Alternative: Docker Deployment

1. Build Docker image:
```bash
docker build -t joke-machine-api .
```

2. Run container:
```bash
docker run -p 8000:8000 joke-machine-api
```

## API Endpoints

### POST /joke
Generate a joke based on request parameters.

**Request Body:**
```json
{
  "type": "general|tech",
  "category": "any|science|programming|food|general"
}
```

**Response:**
```json
{
  "setup": "Why don't scientists trust atoms?",
  "punchline": "Because they make up everything!",
  "category": "science"
}
```

### POST /echo
Echo endpoint for testing POST requests.

**Request Body:** Any valid JSON

**Response:**
```json
{
  "received": <your_input_data>,
  "status": "echoed"
}
```

## Monitoring

- CloudWatch logs are automatically configured
- Health check available at `/health`
- Application logs include request/response information

## Security

- Input validation using Pydantic models
- Error handling with appropriate HTTP status codes
- CORS can be added as needed for frontend integration
