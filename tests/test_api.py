import pytest
import uuid
from fastapi.testclient import TestClient
from main import app
from models.joke import JokeCategory, JokeType


client = TestClient(app)


class TestAPI:
    """Test the API endpoints"""
    
    def test_root_endpoint(self):
        """Test the root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Joke Machine API is running"}
    
    def test_health_endpoint(self):
        """Test the health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}
    
    def test_joke_endpoint_default(self):
        """Test the jokes endpoint with default parameters"""
        response = client.post("/jokes")
        assert response.status_code == 200
        
        data = response.json()
        assert "jokes" in data
        assert "total" in data
        assert data["total"] == 1
        assert len(data["jokes"]) == 1
        
        joke = data["jokes"][0]
        assert "setup" in joke
        assert "punchline" in joke
        assert "category" in joke
        assert "id" in joke
    
    def test_joke_endpoint_with_type(self):
        """Test the jokes endpoint with specific type"""
        response = client.post("/jokes", json={"type": JokeType.TECH.value})
        assert response.status_code == 200
        
        data = response.json()
        joke = data["jokes"][0]
        # Tech jokes should have programming or tech category
        assert joke["category"] in ["programming", "tech"]
    
    def test_joke_endpoint_with_category(self):
        """Test the jokes endpoint with specific category"""
        response = client.post("/jokes", json={"category": JokeCategory.PROGRAMMING.value})
        assert response.status_code == 200
        
        data = response.json()
        joke = data["jokes"][0]
        assert joke["category"] == "programming"
    
    def test_joke_endpoint_with_count(self):
        """Test the jokes endpoint with multiple jokes"""
        response = client.post("/jokes", json={"count": 3})
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] == 3
        assert len(data["jokes"]) == 3
    
    def test_joke_endpoint_invalid_count(self):
        """Test the jokes endpoint with invalid count"""
        response = client.post("/jokes", json={"count": 0})
        assert response.status_code == 422  # Validation error
        
        response = client.post("/jokes", json={"count": 11})
        assert response.status_code == 422  # Validation error
    
    def test_joke_endpoint_invalid_type(self):
        """Test the jokes endpoint with invalid type"""
        response = client.post("/jokes", json={"type": "invalid"})
        assert response.status_code == 422  # Validation error
    
    def test_joke_endpoint_invalid_category(self):
        """Test the jokes endpoint with invalid category"""
        response = client.post("/jokes", json={"category": "invalid"})
        assert response.status_code == 422  # Validation error
    
    def test_echo_endpoint(self):
        """Test the echo endpoint"""
        test_data = {"message": "Hello World", "data": {"key": "value"}}
        response = client.post("/echo", json=test_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["received"] == test_data
        assert data["status"] == "echoed"
    
    def test_echo_endpoint_empty(self):
        """Test the echo endpoint with empty data"""
        response = client.post("/echo", json={})
        assert response.status_code == 200
        
        data = response.json()
        assert data["received"] == {}
        assert data["status"] == "echoed"
    
    def test_joke_endpoint_no_json(self):
        """Test the jokes endpoint without JSON data"""
        response = client.post("/jokes")
        assert response.status_code == 200  # Should use defaults
    
    def test_joke_endpoint_malformed_json(self):
        """Test the jokes endpoint with malformed JSON"""
        response = client.post(
            "/jokes",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    def test_get_joke_by_id(self):
        """Test getting a specific joke by ID"""
        response = client.get("/joke/gen_001")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == "gen_001"
        assert "setup" in data
        assert "punchline" in data
    
    def test_get_joke_by_invalid_id(self):
        """Test getting a joke by invalid ID"""
        response = client.get("/joke/invalid_id")
        assert response.status_code == 404
    
    def test_get_all_jokes(self):
        """Test getting all jokes"""
        response = client.get("/jokes")
        assert response.status_code == 200
        
        data = response.json()
        assert "jokes" in data
        assert "total" in data
        assert data["total"] > 0
        assert len(data["jokes"]) == data["total"]
    
    def test_add_joke(self):
        """Test adding a new joke"""
        new_joke = {
            "setup": "Why did the developer go broke?",
            "punchline": "Because he used up all his cache!",
            "category": JokeCategory.PROGRAMMING.value,
            "id": f"test_new_{uuid.uuid4().hex[:8]}"  # Use unique ID
        }
        
        response = client.post("/jokes/add", json=new_joke)
        assert response.status_code == 200
        
        data = response.json()
        assert data["setup"] == new_joke["setup"]
        assert data["punchline"] == new_joke["punchline"]
        assert data["category"] == new_joke["category"]
        assert data["id"] == new_joke["id"]
        assert "uuid" in data  # Check UUID is returned
    
    def test_add_joke_duplicate(self):
        """Test adding a duplicate joke"""
        new_joke = {
            "setup": "Test setup",
            "punchline": "Test punchline",
            "category": JokeCategory.GENERAL.value,
            "id": "gen_001"  # Existing ID
        }
        
        response = client.post("/jokes/add", json=new_joke)
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]
    
    def test_rate_joke(self):
        """Test rating a joke"""
        rating_data = {"rating": 4.5}
        
        response = client.put("/jokes/gen_001/rating", json=rating_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "Joke rated successfully"
        assert data["joke_id"] == "gen_001"
        assert data["rating"] == 4.5
    
    def test_rate_joke_invalid_rating(self):
        """Test rating with invalid rating value"""
        rating_data = {"rating": 6.0}  # Invalid: > 5
        
        response = client.put("/jokes/gen_001/rating", json=rating_data)
        assert response.status_code == 400
        assert "between 0 and 5" in response.json()["detail"]
    
    def test_rate_joke_not_found(self):
        """Test rating a non-existent joke"""
        rating_data = {"rating": 3.0}
        
        response = client.put("/jokes/nonexistent/rating", json=rating_data)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_delete_joke(self):
        """Test deleting a joke"""
        response = client.delete("/jokes/test_delete_001")
        assert response.status_code == 404  # Should not exist initially
        
        # First add a joke to delete
        new_joke = {
            "setup": "Test joke for deletion",
            "punchline": "This will be deleted",
            "category": "general",
            "id": "test_delete_001"
        }
        client.post("/jokes/add", json=new_joke)
        
        # Now delete it
        response = client.delete("/jokes/test_delete_001")
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "Joke deleted successfully"
        assert data["joke_id"] == "test_delete_001"
    
    def test_delete_joke_not_found(self):
        """Test deleting a non-existent joke"""
        response = client.delete("/jokes/nonexistent")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
