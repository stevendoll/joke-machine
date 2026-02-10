from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from enum import Enum
from datetime import datetime, timezone
import random
import uuid


class StepRole(str, Enum):
    SETUP = "setup"
    PUNCHLINE = "punchline"
    BRIDGE = "bridge"
    TOPPER = "topper"
    CALLBACK = "callback"


class Step(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="UUID primary key for the step",
    )
    role: StepRole = Field(..., description="Role of the step in the joke structure")
    order: int = Field(
        default=1, ge=1, description="Order of the step in the joke sequence"
    )
    content: str = Field(..., description="Content of the step")
    joke_id: Optional[str] = Field(default=None, description="ID of the parent joke")

    @classmethod
    def get_default(cls):
        return cls(role=StepRole.SETUP, order=1, content="")


class JokeCategory(str, Enum):
    GENERAL = "general"
    SCIENCE = "science"
    PROGRAMMING = "programming"
    FOOD = "food"
    TECH = "tech"


class Joke(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="UUID primary key for joke",
    )
    category: JokeCategory = Field(..., description="The category of the joke")
    rating: Optional[float] = Field(
        None, ge=0, le=5, description="User rating from 0 to 5"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(microsecond=0),
        description="Timestamp when joke was created",
    )
    steps: Optional[List[Step]] = Field(
        default=None, description="List of steps that make up this joke"
    )

    @classmethod
    def get_default(cls):
        return cls(category=JokeCategory.GENERAL, rating=None)


class JokeRequest(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    category: Optional[JokeCategory] = Field(
        default=None, description="Specific category requested"
    )
    count: int = Field(default=1, ge=1, le=10, description="Number of jokes to return")

    @classmethod
    def get_default(cls):
        return cls(category=None, count=1)


class JokeCreateRequest(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    category: JokeCategory = Field(..., description="The category of the joke")
    steps: List[Step] = Field(
        ..., description="List of steps that make up this joke", min_length=1
    )


class JokeResponse(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    jokes: List[Joke] = Field(..., description="List of jokes returned")
    count: int = Field(..., description="Number of jokes returned")


class StepResponse(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    steps: List[Step] = Field(..., description="List of steps returned")
    count: int = Field(..., description="Number of steps returned")


class JokeDatabase:
    """In-memory joke database with sample jokes"""

    def __init__(self):
        self._jokes = []
        # Load jokes from SQLite database
        self._load_from_sqlite()

    def _load_from_sqlite(self):
        """Load jokes from SQLite database"""
        try:
            from database import db as sqlite_db

            sqlite_jokes = sqlite_db.get_all_jokes()
            self._jokes = sqlite_jokes
        except Exception:
            # If SQLite database is not available, use default jokes
            self._jokes = [
                Joke(
                    id=str(uuid.uuid4()),
                    category=JokeCategory.SCIENCE,
                    steps=[
                        Step(
                            id=str(uuid.uuid4()),
                            role=StepRole.SETUP,
                            order=1,
                            content="Why don't scientists trust atoms?",
                        ),
                        Step(
                            id=str(uuid.uuid4()),
                            role=StepRole.PUNCHLINE,
                            order=2,
                            content="Because they make up everything!",
                        ),
                    ],
                )
            ]

    def get_jokes(
        self, category: Optional[JokeCategory] = None, count: int = 1, offset: int = 0
    ) -> List[Joke]:
        """Get jokes filtered by category"""
        # This is a mock implementation for testing
        # In real implementation, this would call the database
        jokes = self._jokes

        # Filter by category if specified
        if category:
            jokes = [j for j in jokes if j.category == category]

        # Return random selection
        if len(jokes) <= count:
            return jokes[offset:]
        return random.sample(jokes, count)

    def get_all_jokes(self) -> List[Joke]:
        """Get all jokes from the database"""
        return self._jokes

    def get_joke_by_id(self, joke_id: str) -> Optional[Joke]:
        """Get a specific joke by ID"""
        for joke in self._jokes:
            if joke.id == joke_id:
                return joke
        return None


# Global instance
joke_db = JokeDatabase()
