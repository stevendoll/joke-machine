import pytest
from models.joke import Joke, JokeRequest, JokeResponse, JokeCategory, JokeType, joke_db


class TestJokeModel:
    """Test the Joke model and related classes"""
    
    def test_joke_creation(self):
        """Test creating a valid joke"""
        joke = Joke(
            setup="Why don't scientists trust atoms?",
            punchline="Because they make up everything!",
            category=JokeCategory.SCIENCE,
            id="test_001"
        )
        
        assert joke.setup == "Why don't scientists trust atoms?"
        assert joke.punchline == "Because they make up everything!"
        assert joke.category == JokeCategory.SCIENCE
        assert joke.id == "test_001"
        assert joke.rating is None
    
    def test_joke_with_rating(self):
        """Test creating a joke with rating"""
        joke = Joke(
            setup="Test setup",
            punchline="Test punchline",
            category=JokeCategory.GENERAL,
            rating=4.5,
            id="test_002"
        )
        
        assert joke.rating == 4.5
    
    def test_joke_invalid_rating(self):
        """Test that invalid ratings raise validation errors"""
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            Joke(
                setup="Test setup",
                punchline="Test punchline",
                category=JokeCategory.GENERAL,
                rating=6.0,  # Invalid: > 5
                id="test_003"
            )
        
        with pytest.raises(ValidationError):
            Joke(
                setup="Test setup",
                punchline="Test punchline",
                category=JokeCategory.GENERAL,
                rating=-1.0,  # Invalid: < 0
                id="test_004"
            )
    
    def test_joke_request_defaults(self):
        """Test joke request with default values"""
        request = JokeRequest()
        
        assert request.type == JokeType.GENERAL
        assert request.category is None
        assert request.count == 1
    
    def test_joke_request_custom_values(self):
        """Test joke request with custom values"""
        request = JokeRequest(
            type=JokeType.TECH,
            category=JokeCategory.PROGRAMMING,
            count=3
        )
        
        assert request.type == JokeType.TECH
        assert request.category == JokeCategory.PROGRAMMING
        assert request.count == 3
    
    def test_joke_request_invalid_count(self):
        """Test that invalid count values raise validation errors"""
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            JokeRequest(count=0)  # Invalid: < 1
        
        with pytest.raises(ValidationError):
            JokeRequest(count=11)  # Invalid: > 10
    
    def test_joke_response(self):
        """Test joke response creation"""
        jokes = [
            Joke(
                setup="Setup 1",
                punchline="Punchline 1",
                category=JokeCategory.GENERAL,
                id="test_005"
            ),
            Joke(
                setup="Setup 2",
                punchline="Punchline 2",
                category=JokeCategory.TECH,
                id="test_006"
            )
        ]
        
        response = JokeResponse(jokes=jokes, total=2)
        
        assert len(response.jokes) == 2
        assert response.total == 2
        assert response.jokes[0].setup == "Setup 1"
        assert response.jokes[1].setup == "Setup 2"


class TestJokeDatabase:
    """Test the joke database functionality"""
    
    def test_get_jokes_by_type(self):
        """Test getting jokes by type"""
        jokes = joke_db.get_jokes(JokeType.GENERAL)
        
        assert len(jokes) > 0
        assert all(joke.category in [JokeCategory.GENERAL, JokeCategory.SCIENCE, JokeCategory.FOOD] for joke in jokes)
    
    def test_get_jokes_by_type_and_category(self):
        """Test getting jokes by type and category"""
        jokes = joke_db.get_jokes(JokeType.TECH, JokeCategory.PROGRAMMING)
        
        assert len(jokes) > 0
        assert all(joke.category == JokeCategory.PROGRAMMING for joke in jokes)
    
    def test_get_jokes_with_count(self):
        """Test getting a specific number of jokes"""
        jokes = joke_db.get_jokes(JokeType.GENERAL, count=2)
        
        assert len(jokes) <= 2
    
    def test_get_all_jokes(self):
        """Test getting all jokes"""
        all_jokes = joke_db.get_all_jokes()
        
        assert len(all_jokes) > 0
        assert len(all_jokes) >= 8  # We know we have at least 8 jokes
    
    def test_get_joke_by_id(self):
        """Test getting a joke by ID"""
        joke = joke_db.get_joke_by_id("gen_001")
        
        assert joke is not None
        assert joke.id == "gen_001"
        assert joke.setup == "Why don't scientists trust atoms?"
    
    def test_get_joke_by_invalid_id(self):
        """Test getting a joke by invalid ID"""
        joke = joke_db.get_joke_by_id("invalid_id")
        
        assert joke is None
    
    def test_get_jokes_nonexistent_category(self):
        """Test getting jokes with a category that doesn't exist for the type"""
        jokes = joke_db.get_jokes(JokeType.GENERAL, JokeCategory.PROGRAMMING)
        
        # Should return programming jokes from other types (improved behavior)
        assert len(jokes) > 0
        assert all(joke.category == JokeCategory.PROGRAMMING for joke in jokes)


class TestJokeEnums:
    """Test the enum classes"""
    
    def test_joke_category_values(self):
        """Test joke category enum values"""
        assert JokeCategory.GENERAL == "general"
        assert JokeCategory.SCIENCE == "science"
        assert JokeCategory.PROGRAMMING == "programming"
        assert JokeCategory.FOOD == "food"
        assert JokeCategory.TECH == "tech"
    
    def test_joke_type_values(self):
        """Test joke type enum values"""
        assert JokeType.GENERAL == "general"
        assert JokeType.TECH == "tech"
