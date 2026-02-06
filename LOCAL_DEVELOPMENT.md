# Local Development Guide

## 🚀 Running the Joke Machine API Locally

### Prerequisites
- Python 3.13+
- pipenv (recommended) or pip

---

## Method 1: Using Pipenv Scripts (Easiest)

### 1. Install Dependencies
```bash
pipenv install
```

### 2. Run API with Script
```bash
pipenv run local
```

### 3. Run Tests
```bash
pipenv run test
```

### 4. Run Tests with Coverage
```bash
pipenv run test-cov
```

---

## Method 2: Using Pipenv (Manual)

### 1. Install Dependencies
```bash
pipenv install
```

### 2. Activate Virtual Environment
```bash
pipenv shell
```

### 3. Run the API
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

## Method 2: Using pip

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the API
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

## Method 3: Using Docker

### 1. Build Docker Image
```bash
docker build -t joke-machine .
```

### 2. Run Container
```bash
docker run -p 8000:8000 joke-machine
```

---

## 🌐 Accessing the API

Once running, the API will be available at:
- **API Base URL**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **OpenAPI Schema**: http://localhost:8000/openapi.json

---

## 🧪 Testing

### Run All Tests
```bash
# With pipenv
pipenv run pytest

# With pip
pytest
```

### Run Specific Tests
```bash
# API tests only
pipenv run pytest tests/test_api.py -v

# Model tests only
pipenv run pytest tests/test_joke_model.py -v

# Run with coverage
pipenv run pytest --cov=. --cov-report=html
```

---

## 📊 Database

The SQLite database (`jokes.db`) will be created automatically on first run with sample data.

### View Database Contents
```bash
pipenv run python -c "
from database import db
jokes = db.get_all_jokes()
print(f'Total jokes: {len(jokes)}')
for joke in jokes[:3]:
    print(f'ID: {joke.id}, UUID: {joke.uuid[:8]}..., Category: {joke.category}')
"
```

---

## 🔧 API Examples

### Get All Jokes
```bash
curl http://localhost:8000/jokes
```

### Get Random Joke
```bash
curl -X POST http://localhost:8000/jokes
```

### Get Programming Jokes
```bash
curl -X POST http://localhost:8000/jokes \
  -H "Content-Type: application/json" \
  -d '{"category": "programming"}'
```

### Add New Joke
```bash
curl -X POST http://localhost:8000/jokes \
  -H "Content-Type: application/json" \
  -d '{
    "setup": "Why do programmers prefer dark mode?",
    "punchline": "Because light attracts bugs!",
    "category": "programming",
    "id": "my_joke_001"
  }'
```

### Rate a Joke
```bash
curl -X PUT http://localhost:8000/jokes/gen_001/rating \
  -H "Content-Type: application/json" \
  -d '{"rating": 4.5}'
```

### Delete a Joke
```bash
curl -X DELETE http://localhost:8000/jokes/gen_001
```

---

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Kill process using port 8000
lsof -ti:8000 | xargs kill -9

# Or use different port
uvicorn main:app --port 8001
```

### Database Issues
```bash
# Remove database to reset
rm jokes.db
# Restart API to recreate with sample data
```

### Import Errors
```bash
# Ensure you're in the project directory
cd /path/to/joke-machine

# Reinstall dependencies
pipenv install --dev
```

---

## 📝 Development Tips

### Hot Reload
The `--reload` flag automatically restarts the server when you change code files.

### Environment Variables
```bash
# Disable AWS Powertools for local development
export AWS_LAMBDA_FUNCTION_NAME=""

# Enable debug logging
export LOG_LEVEL=DEBUG
```

### Code Formatting
```bash
# Install development dependencies
pipenv install --dev black flake8

# Format code
pipenv run black .

# Lint code
pipenv run flake8 .
```

---

## 🎯 Quick Start Commands

```bash
# One-command setup and run
pipenv install && pipenv run local

# Or with Docker
docker build -t joke-machine . && docker run -p 8000:8000 joke-machine

# Run tests
pipenv run test

# Run tests with coverage report
pipenv run test-cov
```

## 📋 Available Pipenv Scripts

| Command | Description |
|---------|-------------|
| `pipenv run local` | Start API server with hot reload |
| `pipenv run test` | Run all tests |
| `pipenv run test-cov` | Run tests with HTML coverage report |

Happy coding! 🚀
