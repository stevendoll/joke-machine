from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import json
import logging
import os

# Simple logging for both local and Lambda
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from database import db
from models.joke import JokeRequest, JokeResponse, joke_db, JokeCategory, JokeType, Joke

# Pydantic model for rating requests
class RatingRequest(BaseModel):
    rating: float = Field(..., description="Rating value")

app = FastAPI(title="Joke Machine API", version="1.0.0")

@app.get("/")
def root():
    logger.info("Root endpoint accessed")
    return {"message": "Joke Machine API is running"}

@app.get("/health")
def health_check():
    logger.info("Health endpoint accessed")
    return {"status": "healthy"}

@app.post("/jokes", response_model=JokeResponse)
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
        
        # Get jokes from database
        jokes = db.get_jokes(
            joke_type=request.type,
            category=request.category,
            count=request.count
        )
        
        logger.info(f"Returning {len(jokes)} jokes from {request.type} type")
        
        return JokeResponse(jokes=jokes, total=len(jokes))
        
    except Exception as e:
        logger.error(f"Error processing jokes request: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/echo")
def echo_endpoint(data: Dict[str, Any]):
    """Echo endpoint for testing"""
    logger.info(f"Echo endpoint called with: {data}")
    return {"received": data, "status": "echoed"}

@app.get("/joke/{joke_id}")
def get_joke_by_id(joke_id: str):
    """Get a specific joke by ID"""
    try:
        logger.info(f"Getting joke by ID: {joke_id}")
        
        joke = db.get_joke_by_id(joke_id)
        
        if not joke:
            logger.warning(f"Joke not found: {joke_id}")
            raise HTTPException(status_code=404, detail="Joke not found")
        
        logger.info(f"Found joke: {joke_id}")
        return joke.model_dump()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting joke: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/jokes")
def get_all_jokes():
    """Get all jokes from database"""
    try:
        logger.info("Retrieving all jokes")
        
        all_jokes = db.get_all_jokes()
        
        logger.info(f"Returning {len(all_jokes)} jokes")
        
        return JokeResponse(jokes=all_jokes, total=len(all_jokes))
        
    except Exception as e:
        logger.error(f"Error getting all jokes: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/jokes/add", response_model=Joke)
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
        
        success = db.add_joke(joke)
        
        if success:
            logger.info(f"Successfully added joke with ID: {joke.id}")
            return joke.model_dump()
        else:
            logger.warning(f"Failed to add joke - duplicate ID: {joke.id}")
            raise HTTPException(status_code=409, detail="Joke with this ID already exists")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding joke: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.put("/jokes/{joke_id}/rating")
def rate_joke(joke_id: str, rating_request: RatingRequest):
    """
    Rate a joke
    
    Args:
        joke_id: ID of the joke to rate
        rating_request: Rating request with rating value
        
    Returns:
        Success message
    """
    try:
        rating = rating_request.rating
        
        # Manual validation for better error messages
        if not (0 <= rating <= 5):
            raise HTTPException(status_code=400, detail="Rating must be between 0 and 5")
        
        logger.info(f"Rating joke {joke_id} with {rating}")
        
        success = db.update_joke_rating(joke_id, rating)
        
        if success:
            logger.info(f"Successfully rated joke {joke_id}")
            return {"message": "Joke rated successfully", "joke_id": joke_id, "rating": rating}
        else:
            logger.warning(f"Joke not found: {joke_id}")
            raise HTTPException(status_code=404, detail="Joke not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rating joke: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/jokes/{joke_id}")
def delete_joke(joke_id: str):
    """
    Delete a joke
    
    Args:
        joke_id: ID of the joke to delete
        
    Returns:
        Success message
    """
    try:
        logger.info(f"Deleting joke: {joke_id}")
        
        success = db.delete_joke(joke_id)
        
        if success:
            logger.info(f"Successfully deleted joke: {joke_id}")
            return {"message": "Joke deleted successfully", "joke_id": joke_id}
        else:
            logger.warning(f"Joke not found: {joke_id}")
            raise HTTPException(status_code=404, detail="Joke not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting joke: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
