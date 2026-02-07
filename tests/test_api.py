import pytest
import uuid
from fastapi.testclient import TestClient
from main import app


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
        """Test the jokes endpoint with default parameters (no count specified)"""
        response = client.get("/jokes")
        assert response.status_code == 200
        
        data = response.json()
        assert "jokes" in data
        assert "total" in data
        assert data["total"] > 0  # Should return all jokes when no count specified
        assert len(data["jokes"]) == data["total"]
        
        joke = data["jokes"][0]
        assert "setup" in joke
        assert "punchline" in joke
        assert "category" in joke
        assert "uuid" in joke
    
    def test_joke_endpoint_with_category(self):
        """Test the jokes endpoint with specific category"""
        response = client.get("/jokes?category=programming")
        assert response.status_code == 200
        
        data = response.json()
        joke = data["jokes"][0]
        # Programming jokes should have programming category
        assert joke["category"] == "programming"
    
    def test_joke_endpoint_with_count(self):
        """Test the jokes endpoint with multiple jokes"""
        response = client.get("/jokes?count=3")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] == 3
        assert len(data["jokes"]) == 3
    
    def test_joke_endpoint_invalid_count(self):
        """Test the jokes endpoint with invalid count"""
        response = client.get("/jokes?count=0")
        assert response.status_code == 400  # Validation error
        
        response = client.get("/jokes?count=11")
        assert response.status_code == 400  # Validation error
    
    def test_joke_endpoint_invalid_category(self):
        """Test the jokes endpoint with invalid category"""
        response = client.get("/jokes?category=invalid")
        assert response.status_code == 400  # Validation error
    
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
        """Test the jokes endpoint without parameters (should use defaults)"""
        response = client.get("/jokes")
        assert response.status_code == 200  # Should use defaults
    
    def test_joke_endpoint_malformed_json(self):
        """Test the jokes endpoint with malformed JSON (not applicable to GET)"""
        # This test is not applicable to GET requests, so we skip it
        pass
    
    def test_get_joke_by_id(self):
        """Test getting a specific joke by ID"""
        # First get a joke to test with
        response = client.get("/jokes?count=1")
        assert response.status_code == 200
        joke_uuid = response.json()["jokes"][0]["uuid"]
        
        response = client.get(f"/jokes/{joke_uuid}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["uuid"] == joke_uuid
        assert "setup" in data
        assert "punchline" in data
    
    def test_get_joke_by_invalid_id(self):
        """Test getting a joke by invalid ID"""
        response = client.get("/jokes/invalid_id")
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
    
    def test_get_jokes_with_query_params(self):
        """Test getting jokes with query parameters"""
        # Test without category and without count (should return all jokes)
        response = client.get("/jokes")
        assert response.status_code == 200
        
        data = response.json()
        assert "jokes" in data
        assert "total" in data
        assert len(data["jokes"]) == data["total"]  # All jokes
        
        # Test with category only (should return all jokes in that category)
        response = client.get("/jokes?category=programming")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["jokes"]) > 0
        assert all(joke["category"] == "programming" for joke in data["jokes"])
        
        # Test with count only (should return specified number of random jokes)
        response = client.get("/jokes?count=3")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["jokes"]) <= 3
        
        # Test with category and count
        response = client.get("/jokes?category=general&count=2")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["jokes"]) <= 2
        assert all(joke["category"] == "general" for joke in data["jokes"])
    
    def test_get_jokes_invalid_category(self):
        """Test getting jokes with invalid category"""
        response = client.get("/jokes?category=invalid")
        assert response.status_code == 400
        assert "Invalid category" in response.json()["detail"]
    
    def test_get_jokes_invalid_count(self):
        """Test getting jokes with invalid count"""
        response = client.get("/jokes?count=0")
        assert response.status_code == 400
        assert "Count must be between 1 and 10" in response.json()["detail"]
        
        response = client.get("/jokes?count=11")
        assert response.status_code == 400
        assert "Count must be between 1 and 10" in response.json()["detail"]
    
    def test_add_joke(self):
        """Test adding a new joke"""
        new_joke = {
            "setup": "Why did the developer go broke?",
            "punchline": "Because he used up all his cache!",
            "category": "programming"
        }
        
        response = client.post("/jokes", json=new_joke)
        assert response.status_code == 200
        
        data = response.json()
        assert data["setup"] == new_joke["setup"]
        assert data["punchline"] == new_joke["punchline"]
        assert data["category"] == new_joke["category"]
        assert "uuid" in data  # Check UUID is returned
    
    def test_add_joke_duplicate(self):
        """Test adding a duplicate joke (same setup and punchline)"""
        new_joke = {
            "setup": "Test setup",
            "punchline": "Test punchline",
            "category": "general"
        }
        
        # Add the joke first
        response1 = client.post("/jokes", json=new_joke)
        assert response1.status_code == 200
        
        # Try to add the same joke again - should succeed with different UUID
        response2 = client.post("/jokes", json=new_joke)
        assert response2.status_code == 200
        
        # Verify they have different UUIDs but same content
        joke1 = response1.json()
        joke2 = response2.json()
        assert joke1["uuid"] != joke2["uuid"]
        assert joke1["setup"] == joke2["setup"]
        assert joke1["punchline"] == joke2["punchline"]
    
    def test_rate_joke(self):
        """Test rating a joke"""
        # First get a joke to rate
        response = client.get("/jokes?count=1")
        assert response.status_code == 200
        joke_uuid = response.json()["jokes"][0]["uuid"]
        
        rating_data = {"rating": 4.5}
        response = client.put(f"/jokes/{joke_uuid}/rating", json=rating_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "Joke rated successfully"
        assert data["joke_id"] == joke_uuid
        assert data["rating"] == 4.5
    
    def test_rate_joke_invalid_rating(self):
        """Test rating with invalid rating value"""
        # First get a joke to test with
        response = client.get("/jokes?count=1")
        assert response.status_code == 200
        joke_uuid = response.json()["jokes"][0]["uuid"]
        
        rating_data = {"rating": 6.0}  # Invalid: > 5
        response = client.put(f"/jokes/{joke_uuid}/rating", json=rating_data)
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
        # First add a joke to delete
        new_joke = {
            "setup": "Test joke for deletion",
            "punchline": "This will be deleted",
            "category": "general"
        }
        response = client.post("/jokes", json=new_joke)
        assert response.status_code == 200
        joke_uuid = response.json()["uuid"]
        
        # Now delete it
        response = client.delete(f"/jokes/{joke_uuid}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "Joke deleted successfully"
        assert data["joke_id"] == joke_uuid
    
    def test_delete_joke_not_found(self):
        """Test deleting a non-existent joke"""
        response = client.delete("/jokes/nonexistent")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
