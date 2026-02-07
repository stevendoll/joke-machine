from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Literal
from enum import Enum
import random
import uuid
from datetime import datetime, timezone


class JokeCategory(str, Enum):
    GENERAL = "general"
    SCIENCE = "science"
    PROGRAMMING = "programming"
    FOOD = "food"
    TECH = "tech"


class Joke(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid"
    )
    
    uuid: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), description="UUID primary key for the joke")
    setup: str = Field(..., description="The setup part of the joke")
    punchline: str = Field(..., description="The punchline of the joke")
    category: JokeCategory = Field(..., description="The category of the joke")
    rating: Optional[float] = Field(None, ge=0, le=5, description="User rating from 0 to 5")
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp when joke was created")
    
    @classmethod
    def get_default(cls):
        return cls(
            setup="",
            punchline="",
            category=JokeCategory.GENERAL,
            rating=None
        )


class JokeRequest(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid"
    )
    
    category: Optional[JokeCategory] = Field(default=None, description="Specific category requested")
    count: int = Field(default=1, ge=1, le=10, description="Number of jokes to return")
    
    @classmethod
    def get_default(cls):
        return cls(category=None, count=1)


class JokeResponse(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid"
    )
    
    jokes: List[Joke] = Field(..., description="List of jokes returned")
    count: int = Field(..., description="Number of jokes returned")


class JokeDatabase:
    """In-memory joke database with sample jokes"""
    
    def __init__(self):
        self._jokes = [
            Joke(
                uuid=str(uuid.uuid4()),
                setup="Why don't scientists trust atoms?",
                punchline="Because they make up everything!",
                category=JokeCategory.SCIENCE
            ),
            Joke(
                uuid=str(uuid.uuid4()),
                setup="Why did the scarecrow win an award?",
                punchline="He was outstanding in his field!",
                category=JokeCategory.GENERAL
            ),
            Joke(
                uuid=str(uuid.uuid4()),
                setup="Why don't eggs tell jokes?",
                punchline="They'd crack each other up!",
                category=JokeCategory.FOOD
            ),
            Joke(
                uuid=str(uuid.uuid4()),
                setup="What do you call a bear with no teeth?",
                punchline="A gummy bear!",
                category=JokeCategory.GENERAL
            ),
            Joke(
                uuid=str(uuid.uuid4()),
                setup="Why do programmers prefer dark mode?",
                punchline="Because light attracts bugs!",
                category=JokeCategory.PROGRAMMING
            ),
            Joke(
                uuid=str(uuid.uuid4()),
                setup="Why do Java developers wear glasses?",
                punchline="Because they don't C#!",
                category=JokeCategory.PROGRAMMING
            ),
            Joke(
                uuid=str(uuid.uuid4()),
                setup="Why do programmers always mix up Halloween and Christmas?",
                punchline="Because Oct 31 equals Dec 25!",
                category=JokeCategory.TECH
            ),
        ]
    
    def get_jokes(self, category: Optional[JokeCategory] = None, count: int = 1) -> List[Joke]:
        """Get jokes filtered by category"""
        jokes = self._jokes
        
        # Filter by category if specified
        if category:
            jokes = [j for j in jokes if j.category == category]
        
        # Return random selection
        if len(jokes) <= count:
            return jokes
        
        return random.sample(jokes, count)
    
    def get_all_jokes(self) -> List[Joke]:
        """Get all jokes from the database"""
        return self._jokes
    
    def get_joke_by_id(self, joke_id: str) -> Optional[Joke]:
        """Get a specific joke by ID"""
        for joke in self._jokes:
            if joke.uuid == joke_id:
                return joke
        return None


# Global instance
joke_db = JokeDatabase()
