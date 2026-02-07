from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Literal
from enum import Enum
import random
import uuid


class JokeCategory(str, Enum):
    GENERAL = "general"
    SCIENCE = "science"
    PROGRAMMING = "programming"
    FOOD = "food"
    TECH = "tech"


class JokeType(str, Enum):
    GENERAL = "general"
    TECH = "tech"


class Joke(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid"
    )
    
    uuid: Optional[str] = Field(None, description="UUID primary key for the joke")
    id: Optional[str] = Field(None, description="Unique identifier for the joke")
    setup: str = Field(..., description="The setup part of the joke")
    punchline: str = Field(..., description="The punchline of the joke")
    category: JokeCategory = Field(..., description="The category of the joke")
    rating: Optional[float] = Field(None, ge=0, le=5, description="User rating from 0 to 5")
    
    @classmethod
    def get_default(cls):
        return cls(
            uuid=str(uuid.uuid4()),
            id=None,
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
    
    type: JokeType = Field(default=JokeType.GENERAL, description="Type of joke requested")
    category: Optional[JokeCategory] = Field(default=None, description="Specific category requested")
    count: int = Field(default=1, ge=1, le=10, description="Number of jokes to return")
    
    @classmethod
    def get_default(cls):
        return cls(type=JokeType.GENERAL, category=None, count=1)


class JokeResponse(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid"
    )
    
    jokes: List[Joke] = Field(..., description="List of jokes returned")
    total: int = Field(..., description="Total number of jokes returned")


class JokeDatabase:
    """In-memory joke database with sample jokes"""
    
    def __init__(self):
        self._jokes = {
            JokeType.GENERAL: [
                Joke(
                    uuid=str(uuid.uuid4()),
                    setup="Why don't scientists trust atoms?",
                    punchline="Because they make up everything!",
                    category=JokeCategory.SCIENCE,
                    id="gen_001"
                ),
                Joke(
                    uuid=str(uuid.uuid4()),
                    setup="Why did the scarecrow win an award?",
                    punchline="He was outstanding in his field!",
                    category=JokeCategory.GENERAL,
                    id="gen_002"
                ),
                Joke(
                    uuid=str(uuid.uuid4()),
                    setup="Why don't eggs tell jokes?",
                    punchline="They'd crack each other up!",
                    category=JokeCategory.FOOD,
                    id="gen_003"
                ),
                Joke(
                    uuid=str(uuid.uuid4()),
                    setup="What do you call a bear with no teeth?",
                    punchline="A gummy bear!",
                    category=JokeCategory.GENERAL,
                    id="gen_004"
                ),
            ],
            JokeType.TECH: [
                Joke(
                    uuid=str(uuid.uuid4()),
                    setup="Why do programmers prefer dark mode?",
                    punchline="Because light attracts bugs!",
                    category=JokeCategory.PROGRAMMING,
                    id="tech_001"
                ),
                Joke(
                    uuid=str(uuid.uuid4()),
                    setup="Why do Java developers wear glasses?",
                    punchline="Because they don't C#!",
                    category=JokeCategory.PROGRAMMING,
                    id="tech_002"
                ),
                Joke(
                    uuid=str(uuid.uuid4()),
                    setup="What's a programmer's favorite hangout spot?",
                    punchline="The foo bar!",
                    category=JokeCategory.PROGRAMMING,
                    id="tech_003"
                ),
                Joke(
                    uuid=str(uuid.uuid4()),
                    setup="Why do programmers always mix up Halloween and Christmas?",
                    punchline="Because Oct 31 equals Dec 25!",
                    category=JokeCategory.TECH,
                    id="tech_004"
                ),
            ]
        }
    
    def get_jokes(self, joke_type: JokeType, category: Optional[JokeCategory] = None, count: int = 1) -> List[Joke]:
        """Get jokes filtered by type and category"""
        jokes = self._jokes.get(joke_type, [])
        
        # Filter by category if specified
        if category:
            jokes = [j for j in jokes if j.category == category]
        
        # If no jokes found with the specified type and category, 
        # search across all types for the category
        if category and not jokes:
            all_jokes = []
            for jokes_list in self._jokes.values():
                all_jokes.extend([j for j in jokes_list if j.category == category])
            jokes = all_jokes
        
        # Return random selection
        if len(jokes) <= count:
            return jokes
        
        return random.sample(jokes, count)
    
    def get_all_jokes(self) -> List[Joke]:
        """Get all jokes from the database"""
        all_jokes = []
        for jokes_list in self._jokes.values():
            all_jokes.extend(jokes_list)
        return all_jokes
    
    def get_joke_by_id(self, joke_id: str) -> Optional[Joke]:
        """Get a specific joke by ID"""
        for jokes_list in self._jokes.values():
            for joke in jokes_list:
                if joke.id == joke_id:
                    return joke
        return None


# Global instance
joke_db = JokeDatabase()
