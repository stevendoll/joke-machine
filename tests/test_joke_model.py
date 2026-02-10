import pytest
from models.joke import (
    Joke,
    Step,
    StepRole,
    JokeCategory,
    JokeResponse,
    StepResponse,
    JokeRequest,
    joke_db,
)
from pydantic import ValidationError


class TestJokeModel:
    """Test the Joke model and related classes"""

    def test_joke_creation(self):
        """Test creating a valid joke"""
        joke = Joke(
            category=JokeCategory.SCIENCE,
            steps=[
                Step(role=StepRole.SETUP, order=1, content="Why don't scientists trust atoms?"),
                Step(role=StepRole.PUNCHLINE, order=2, content="Because they make up everything!")
            ]
        )

        assert joke.category == JokeCategory.SCIENCE
        assert joke.id is not None
        assert joke.rating is None
        assert joke.created_at is not None

    def test_joke_with_rating(self):
        """Test creating a joke with rating"""
        joke = Joke(
            category=JokeCategory.GENERAL, 
            rating=4.5,
            steps=[
                Step(role=StepRole.SETUP, order=1, content="Test setup"),
                Step(role=StepRole.PUNCHLINE, order=2, content="Test punchline")
            ]
        )

        assert joke.category == JokeCategory.GENERAL
        assert joke.rating == 4.5
        assert joke.id is not None
        assert joke.created_at is not None

        with pytest.raises(ValidationError):
            Joke(
                category=JokeCategory.GENERAL,
                rating=6.0,  # Invalid: > 5
            )

        with pytest.raises(ValidationError):
            Joke(
                category=JokeCategory.GENERAL,
                rating=-1.0,  # Invalid: < 0
            )

    def test_joke_request_default_values(self):
        """Test joke request with default values"""
        request = JokeRequest()

        assert request.category is None
        assert request.count == 1

    def test_joke_request_custom_values(self):
        """Test joke request with custom values"""
        request = JokeRequest(category=JokeCategory.PROGRAMMING, count=3)

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
                category=JokeCategory.GENERAL,
                steps=[Step(role=StepRole.SETUP, order=1, content="Test setup 1")]
            ),
            Joke(
                category=JokeCategory.TECH,
                steps=[Step(role=StepRole.SETUP, order=1, content="Test setup 2")]
            )
        ]

        response = JokeResponse(jokes=jokes, count=2)

        assert len(response.jokes) == 2
        assert response.count == 2
        assert response.jokes[0].category == JokeCategory.GENERAL
        assert response.jokes[1].category == JokeCategory.TECH

    def test_joke_created_at_required(self):
        """Test that created_at is required and cannot be None"""
        # This should fail because created_at is required
        with pytest.raises(ValidationError) as exc_info:
            Joke(
                id="test-id",
                category=JokeCategory.TECH,
                rating=None,
                created_at=None,  # This should cause validation error
                steps=[
                    Step(role=StepRole.SETUP, order=1, content="Test setup"),
                    Step(role=StepRole.PUNCHLINE, order=2, content="Test punchline"),
                ],
            )
        
        # Check that the error message mentions datetime validation
        assert "created_at" in str(exc_info.value)
        assert "Input should be a valid datetime" in str(exc_info.value)

    def test_joke_invalid_datetime_format(self):
        """Test that invalid datetime format raises validation error"""
        # This should fail because created_at is invalid datetime
        with pytest.raises(ValidationError) as exc_info:
            Joke(
                id="test-id",
                category=JokeCategory.TECH,
                rating=None,
                created_at="invalid-datetime",  # Invalid datetime string
                steps=[
                    Step(role=StepRole.SETUP, order=1, content="Test setup"),
                    Step(role=StepRole.PUNCHLINE, order=2, content="Test punchline"),
                ],
            )
        
        # Check that the error message mentions datetime validation
        error_str = str(exc_info.value)
        assert "created_at" in error_str
        assert "Input should be a valid datetime" in error_str


class TestJokeDatabase:
    """Test the joke database functionality"""

    def test_get_jokes_by_category(self):
        """Test getting jokes by category"""
        jokes = joke_db.get_jokes(JokeCategory.GENERAL, offset=0)

        # Should return general jokes (may be empty if no general jokes exist)
        assert isinstance(jokes, list)
        # If there are jokes, they should all be general category
        for joke in jokes:
            assert joke.category == JokeCategory.GENERAL

    def test_get_jokes_by_category_and_count(self):
        """Test getting jokes by category with count"""
        jokes = joke_db.get_jokes(JokeCategory.PROGRAMMING, count=2, offset=0)

        assert len(jokes) <= 2
        assert all(joke.category == JokeCategory.PROGRAMMING for joke in jokes)

    def test_get_jokes_with_count(self):
        """Test getting a specific number of jokes"""
        jokes = joke_db.get_jokes(count=2, offset=0)

        assert len(jokes) <= 2

    def test_get_all_jokes(self):
        """Test getting all jokes"""
        all_jokes = joke_db.get_all_jokes()

        assert isinstance(all_jokes, list)
        # If there are jokes, they should have valid properties
        for joke in all_jokes:
            assert hasattr(joke, "id")
            assert hasattr(joke, "category")
            assert hasattr(joke, "rating")
            assert hasattr(joke, "created_at")

    def test_get_joke_by_id(self):
        """Test getting a joke by ID"""
        # Get all jokes to find a valid ID
        all_jokes = joke_db.get_all_jokes()
        if all_jokes:
            joke_id = all_jokes[0].id
            joke = joke_db.get_joke_by_id(joke_id)

            assert joke is not None
            assert joke.id == joke_id

    def test_get_joke_by_invalid_id(self):
        """Test getting a joke by invalid ID"""
        joke = joke_db.get_joke_by_id("invalid_id")

        assert joke is None

    def test_get_jokes_nonexistent_category(self):
        """Test getting jokes with a category that doesn't exist"""
        jokes = joke_db.get_jokes(JokeCategory.PROGRAMMING, offset=0)

        # Should return programming jokes (may be empty if no programming jokes exist)
        assert isinstance(jokes, list)
        # If there are jokes, they should all be programming category
        for joke in jokes:
            assert joke.category == JokeCategory.PROGRAMMING


class TestJokeEnums:
    """Test the enum classes"""

    def test_joke_category_values(self):
        """Test joke category enum values"""
        assert JokeCategory.GENERAL == "general"
        assert JokeCategory.SCIENCE == "science"
        assert JokeCategory.PROGRAMMING == "programming"
        assert JokeCategory.FOOD == "food"
        assert JokeCategory.TECH == "tech"

    def test_step_role_values(self):
        """Test step role enum values"""
        assert StepRole.SETUP == "setup"
        assert StepRole.PUNCHLINE == "punchline"
        assert StepRole.BRIDGE == "bridge"
        assert StepRole.TOPPER == "topper"
        assert StepRole.CALLBACK == "callback"


class TestStepModel:
    """Test the Step model"""

    def test_step_creation(self):
        """Test creating a valid step"""
        step = Step(
            role=StepRole.SETUP, order=1, content="Why don't scientists trust atoms?"
        )

        assert step.role == StepRole.SETUP
        assert step.order == 1
        assert step.content == "Why don't scientists trust atoms?"
        assert step.id is not None
        assert step.joke_id is None

    def test_step_with_all_fields(self):
        """Test creating a step with all fields"""
        step = Step(
            role=StepRole.PUNCHLINE,
            order=2,
            content="Because they make up everything!",
            joke_id="test-joke-id",
        )

        assert step.role == StepRole.PUNCHLINE
        assert step.order == 2
        assert step.content == "Because they make up everything!"
        assert step.joke_id == "test-joke-id"
        assert step.id is not None

    def test_step_default_values(self):
        """Test step default values"""
        step = Step.get_default()

        assert step.role == StepRole.SETUP
        assert step.order == 1
        assert step.content == ""
        assert step.id is not None
        assert step.joke_id is None

    def test_step_invalid_order(self):
        """Test step with invalid order"""
        with pytest.raises(ValidationError):
            Step(
                role=StepRole.SETUP,
                order=0,  # Invalid: must be >= 1
                content="Test content",
            )

    def test_step_response(self):
        """Test step response creation"""
        steps = [
            Step(role=StepRole.SETUP, order=1, content="Setup 1"),
            Step(role=StepRole.PUNCHLINE, order=2, content="Punchline 2"),
        ]

        response = StepResponse(steps=steps, count=2)

        assert len(response.steps) == 2
        assert response.count == 2
