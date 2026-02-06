# Joke Machine API

A FastAPI application with SQLite database, UUID primary keys, and comprehensive CRUD operations for jokes.

## Features

- **POST /jokes** - Get filtered jokes (replaces /joke)
- **GET /jokes** - Get all jokes from database
- **GET /jokes/{joke_id}** - Get specific joke by ID
- **POST /jokes** - Add new joke to database
- **PUT /jokes/{joke_id}/rating** - Rate a joke (0-5)
- **DELETE /jokes/{joke_id}** - Delete a joke
- **POST /echo** - Generic echo endpoint for testing
- **GET /health** - Health check endpoint
- **GET /** - Root endpoint
- **UUID Primary Keys** - Global uniqueness for jokes
- **SQLite Database** - Persistent storage with auto-seeding
- **AWS Powertools** - Logging, tracing, metrics
- **Docker Support** - Container deployment ready

## Local Development

### Prerequisites
- Python 3.13+
- pipenv (recommended) or pip
- Docker (optional)

### Quick Start with Pipenv Scripts

1. Install dependencies:
```bash
pipenv install
```

2. Run API:
```bash
pipenv run local
```

3. Run tests:
```bash
pipenv run test
```

### Available Pipenv Scripts

| Command | Description |
|---------|-------------|
| `pipenv run local` | Start API server with hot reload |
| `pipenv run test` | Run all tests |
| `pipenv run test-cov` | Run tests with HTML coverage report |

### Testing the API

#### Get All Jokes
```bash
curl http://localhost:8000/jokes
```

#### Get Random Joke
```bash
curl -X POST "http://localhost:8000/jokes"
```

#### Get Programming Jokes
```bash
curl -X POST "http://localhost:8000/jokes" \
     -H "Content-Type: application/json" \
     -d '{"category": "programming"}'
```

#### Add New Joke
```bash
curl -X POST "http://localhost:8000/jokes" \
     -H "Content-Type: application/json" \
     -d '{
       "setup": "Why do programmers prefer dark mode?",
       "punchline": "Because light attracts bugs!",
       "category": "programming",
       "id": "my_joke_001"
     }'
```

#### Rate a Joke
```bash
curl -X PUT "http://localhost:8000/jokes/gen_001/rating" \
     -H "Content-Type: application/json" \
     -d '{"rating": 4.5}'
```

#### Echo Endpoint
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
