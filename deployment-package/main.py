from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
from typing import Dict, Any, Optional
import json
import logging
import os

# Only initialize AWS Powertools when running in Lambda
if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
    from aws_lambda_powertools import Logger, Tracer, Metrics
    from aws_lambda_powertools.utilities.typing import LambdaContext
    
    # Configure AWS Powertools
    logger = Logger(service="joke-machine-api")
    tracer = Tracer(service="joke-machine-api")
    metrics = Metrics(service="joke-machine-api")
else:
    # Local development - use standard logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Mock decorators for local development
    class MockTracer:
        def capture_method(self, func):
            return func
    
    class MockMetrics:
        def log_metrics(self, func):
            return func
        def add_metric(self, name, value):
            pass
    
    tracer = MockTracer()
    metrics = MockMetrics()

app_logger = logging.getLogger(__name__)

from database import db
from models.joke import JokeRequest, JokeResponse, joke_db, JokeCategory, JokeType, Joke

app = FastAPI(title="Joke Machine API", version="1.0.0")

@app.get("/")
@tracer.capture_method
@metrics.log_metrics
def root():
    logger.info("Root endpoint accessed")
    metrics.add_metric(name="RootAccessCount", value=1)
    return {"message": "Joke Machine API is running"}

@app.get("/health")
@tracer.capture_method
@metrics.log_metrics
def health_check():
    logger.info("Health check accessed")
    metrics.add_metric(name="HealthCheckCount", value=1)
    return {"status": "healthy"}

@app.post("/jokes", response_model=JokeResponse)
@tracer.capture_method
@metrics.log_metrics
def get_jokes(request: JokeRequest = JokeRequest.get_default()):
    """
    Generate jokes based on request parameters.
    
    Args:
        request: JokeRequest containing type and category preferences
        
    Returns:
        JokeResponse with setup, punchline, and category
    """
    try:
        logger.info(f"Received jokes request: type={request.type}, category={request.category}, count={request.count}")
        metrics.add_metric(name="JokesRequestCount", value=1)
        
        # Get jokes from database
        jokes = db.get_jokes(
            joke_type=request.type,
            category=request.category,
            count=request.count
        )
        
        logger.info(f"Returning {len(jokes)} jokes from {request.type} type")
        
        # Add custom metrics
        metrics.add_metric(name="JokesReturned", value=len(jokes))
        
        return JokeResponse(jokes=jokes, total=len(jokes))
        
    except Exception as e:
        logger.error(f"Error processing jokes request: {str(e)}")
        metrics.add_metric(name="JokesRequestError", value=1)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/echo")
@tracer.capture_method
@metrics.log_metrics
def echo_endpoint(data: Dict[str, Any]):
    """
    Generic echo endpoint for testing POST requests.
    
    Args:
        data: Any JSON data
        
    Returns:
        The same data that was received
    """
    logger.info(f"Echo endpoint received: {data}")
    metrics.add_metric(name="EchoRequestCount", value=1)
    return {"received": data, "status": "echoed"}

@app.get("/joke/{joke_id}")
@tracer.capture_method
@metrics.log_metrics
def get_joke_by_id(joke_id: str):
    """
    Get a specific joke by ID
    
    Args:
        joke_id: The unique identifier of the joke
        
    Returns:
        Joke object or 404 if not found
    """
    logger.info(f"Looking for joke with ID: {joke_id}")
    metrics.add_metric(name="JokeByIdRequestCount", value=1)
    
    joke = db.get_joke_by_id(joke_id)
    
    if not joke:
        logger.warning(f"Joke not found: {joke_id}")
        metrics.add_metric(name="JokeNotFoundCount", value=1)
        raise HTTPException(status_code=404, detail="Joke not found")
    
    logger.info(f"Found joke: {joke_id}")
    return joke.model_dump()

@app.get("/jokes")
@tracer.capture_method
@metrics.log_metrics
def get_all_jokes():
    """
    Get all jokes in the database
    
    Returns:
        JokeResponse with all jokes
    """
    logger.info("Retrieving all jokes")
    metrics.add_metric(name="AllJokesRequestCount", value=1)
    
    all_jokes = db.get_all_jokes()
    
    logger.info(f"Returning {len(all_jokes)} jokes")
    metrics.add_metric(name="AllJokesReturned", value=len(all_jokes))
    
    return JokeResponse(jokes=all_jokes, total=len(all_jokes))

@app.post("/jokes", response_model=Joke)
@tracer.capture_method
@metrics.log_metrics
def add_joke(joke: Joke):
    """
    Add a new joke to the database
    
    Args:
        joke: Joke object to add
        
    Returns:
        Created joke object
    """
    try:
        logger.info(f"Adding new joke: {joke.setup[:50]}...")
        metrics.add_metric(name="AddJokeRequestCount", value=1)
        
        success = db.add_joke(joke)
        
        if success:
            logger.info(f"Successfully added joke with ID: {joke.id}")
            metrics.add_metric(name="JokeAddedCount", value=1)
            return joke.model_dump()
        else:
            logger.warning(f"Failed to add joke - duplicate ID: {joke.id}")
            metrics.add_metric(name="JokeAddErrorCount", value=1)
            raise HTTPException(status_code=409, detail="Joke with this ID already exists")
            
    except Exception as e:
        logger.error(f"Error adding joke: {str(e)}")
        metrics.add_metric(name="JokeAddErrorCount", value=1)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.put("/jokes/{joke_id}/rating")
@tracer.capture_method
@metrics.log_metrics
def rate_joke(joke_id: str, rating: float):
    """
    Rate a joke
    
    Args:
        joke_id: ID of the joke to rate
        rating: Rating value (0-5)
        
    Returns:
        Success message
    """
    try:
        if not (0 <= rating <= 5):
            raise HTTPException(status_code=400, detail="Rating must be between 0 and 5")
        
        logger.info(f"Rating joke {joke_id} with {rating}")
        metrics.add_metric(name="RateJokeRequestCount", value=1)
        
        success = db.update_joke_rating(joke_id, rating)
        
        if success:
            logger.info(f"Successfully rated joke {joke_id}")
            metrics.add_metric(name="JokeRatedCount", value=1)
            return {"message": "Joke rated successfully", "joke_id": joke_id, "rating": rating}
        else:
            logger.warning(f"Joke not found: {joke_id}")
            metrics.add_metric(name="JokeNotFoundErrorCount", value=1)
            raise HTTPException(status_code=404, detail="Joke not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rating joke: {str(e)}")
        metrics.add_metric(name="RateJokeErrorCount", value=1)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/jokes/{joke_id}")
@tracer.capture_method
@metrics.log_metrics
def delete_joke(joke_id: str):
    """
    Delete a joke
    
    Args:
        joke_id: ID of the joke to delete
        
    Returns:
        Success message
    """
    try:
        logger.info(f"Deleting joke {joke_id}")
        metrics.add_metric(name="DeleteJokeRequestCount", value=1)
        
        success = db.delete_joke(joke_id)
        
        if success:
            logger.info(f"Successfully deleted joke {joke_id}")
            metrics.add_metric(name="JokeDeletedCount", value=1)
            return {"message": "Joke deleted successfully", "joke_id": joke_id}
        else:
            logger.warning(f"Joke not found: {joke_id}")
            metrics.add_metric(name="JokeNotFoundErrorCount", value=1)
            raise HTTPException(status_code=404, detail="Joke not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting joke: {str(e)}")
        metrics.add_metric(name="DeleteJokeErrorCount", value=1)
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
