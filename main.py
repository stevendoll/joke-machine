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
from models.joke import JokeResponse, joke_db, JokeCategory, Joke

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

@app.post("/echo")
def echo_endpoint(data: Dict[str, Any]):
    """Echo endpoint for testing"""
    logger.info(f"Echo endpoint called with: {data}")
    return {"received": data, "status": "echoed"}

@app.get("/jokes/{joke_id}")
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
def get_jokes(category: Optional[str] = None, limit: Optional[int] = None, offset: int = 0):
    """Get jokes from database with optional category filter and pagination"""
    try:
        # Validate offset first
        if offset < 0:
            raise HTTPException(status_code=400, detail="Offset must be 0 or greater")
        
        logger.info(f"Retrieving jokes with category: {category}, limit: {limit}, offset: {offset}")
        
        # If no limit specified, get all jokes
        if limit is None:
            all_jokes = db.get_all_jokes()
            # Filter by category if specified
            if category:
                try:
                    category_enum = JokeCategory(category)
                    filtered_jokes = [j for j in all_jokes if j.category == category_enum]
                    logger.info(f"Returning {len(filtered_jokes)} filtered jokes")
                    # Apply offset
                    paginated_jokes = filtered_jokes[offset:] if offset > 0 else filtered_jokes
                    return JokeResponse(jokes=paginated_jokes, count=len(paginated_jokes))
                except ValueError:
                    raise HTTPException(status_code=400, detail=f"Invalid category: {category}")
            else:
                logger.info(f"Returning all {len(all_jokes)} jokes")
                # Apply offset
                paginated_jokes = all_jokes[offset:] if offset > 0 else all_jokes
                return JokeResponse(jokes=paginated_jokes, count=len(paginated_jokes))
        
        # Validate limit if specified
        if limit < 1 or limit > 50:
            raise HTTPException(status_code=400, detail="Limit must be between 1 and 50")
        
        # Convert category string to enum if provided
        category_enum = None
        if category:
            try:
                category_enum = JokeCategory(category)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid category: {category}")
        
        # Get jokes from database
        jokes = db.get_jokes(category=category_enum, count=limit)
        
        # Apply offset (get more jokes to account for offset)
        if offset > 0:
            # Get additional jokes to account for offset
            additional_jokes = db.get_jokes(category=category_enum, count=offset)
            all_jokes = additional_jokes + jokes
            # Apply offset
            final_jokes = all_jokes[offset:offset + limit]
        else:
            final_jokes = jokes
        
        logger.info(f"Returning {len(final_jokes)} jokes")
        
        return JokeResponse(jokes=final_jokes, count=len(final_jokes))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting jokes: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/jokes", response_model=Joke)
def add_joke(joke: Joke):
    """
    Add a new joke to the database
    
    Args:
        joke: Joke object to add
        
    Returns:
        Created joke object
    """
    try:
        logger.info(f"Adding new joke with category: {joke.category}...")
        
        success = db.add_joke(joke)
        
        if success:
            logger.info(f"Successfully added joke with UUID: {joke.uuid}")
            return joke.model_dump()
        else:
            logger.warning(f"Failed to add joke - duplicate UUID: {joke.uuid}")
            raise HTTPException(status_code=409, detail="Joke with this UUID already exists")
            
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
