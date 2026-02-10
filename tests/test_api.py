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
        assert "count" in data
        assert data["count"] > 0  # Should return all jokes when no count specified
        assert len(data["jokes"]) == data["count"]

        joke = data["jokes"][0]
        assert "category" in joke
        assert "id" in joke
        assert "steps" in joke

    def test_joke_endpoint_with_category(self):
        """Test the jokes endpoint with specific category"""
        response = client.get("/jokes?category=programming")
        assert response.status_code == 200

        data = response.json()
        joke = data["jokes"][0]
        # Programming jokes should have programming category
        assert joke["category"] == "programming"

    def test_joke_endpoint_with_limit(self):
        """Test the jokes endpoint with limit parameter"""
        response = client.get("/jokes?limit=3")
        assert response.status_code == 200

        data = response.json()
        assert data["count"] == 3
        assert len(data["jokes"]) == 3

    def test_joke_endpoint_invalid_limit(self):
        """Test the jokes endpoint with invalid limit"""
        response = client.get("/jokes?limit=0")
        assert response.status_code == 400  # Validation error

        response = client.get("/jokes?limit=51")
        assert response.status_code == 400  # Validation error

    def test_joke_endpoint_offset(self):
        """Test the jokes endpoint with offset parameter"""
        # Get first page
        response1 = client.get("/jokes?limit=2&offset=0")
        assert response1.status_code == 200

        # Get second page
        response2 = client.get("/jokes?limit=2&offset=2")
        assert response2.status_code == 200

        # Verify different jokes (if enough jokes exist)
        jokes1 = response1.json()["jokes"]
        jokes2 = response2.json()["jokes"]

        # If we have enough jokes, they should be different
        if len(jokes1) == 2 and len(jokes2) == 2:
            # Check if we actually have different jokes (not the same joke repeated)
            if len(set(j["id"] for j in jokes1 + jokes2)) > 2:
                assert jokes1[0]["id"] != jokes2[0]["id"]

    def test_joke_endpoint_invalid_offset(self):
        """Test the jokes endpoint with invalid offset"""
        response = client.get("/jokes?offset=-1")
        assert response.status_code == 400
        assert "Offset must be 0 or greater" in response.json()["detail"]

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
        response = client.get("/jokes?limit=1")
        assert response.status_code == 200
        joke_id = response.json()["jokes"][0]["id"]

        response = client.get(f"/jokes/{joke_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == joke_id
        assert "category" in data
        assert "steps" in data

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
        assert "count" in data
        assert data["count"] > 0
        assert len(data["jokes"]) == data["count"]

    def test_get_jokes_with_query_params(self):
        """Test getting jokes with query parameters"""
        # Test without category and without count (should return all jokes)
        response = client.get("/jokes")
        assert response.status_code == 200

        data = response.json()
        assert "jokes" in data
        assert "count" in data
        assert len(data["jokes"]) == data["count"]  # All jokes

        # Test with category only (should return all jokes in that category)
        response = client.get("/jokes?category=programming")
        assert response.status_code == 200

        data = response.json()
        assert len(data["jokes"]) > 0
        assert all(joke["category"] == "programming" for joke in data["jokes"])

        # Test with limit only (should return specified number of random jokes)
        response = client.get("/jokes?limit=3")
        assert response.status_code == 200

        data = response.json()
        assert len(data["jokes"]) <= 3

        # Test with category and limit
        response = client.get("/jokes?category=general&limit=2")
        assert response.status_code == 200

        data = response.json()
        assert len(data["jokes"]) <= 2
        assert all(joke["category"] == "general" for joke in data["jokes"])

        # Test with limit and offset
        response = client.get("/jokes?limit=2&offset=1")
        assert response.status_code == 200

        data = response.json()
        assert len(data["jokes"]) <= 2

    def test_get_jokes_invalid_category(self):
        """Test getting jokes with invalid category"""
        response = client.get("/jokes?category=invalid")
        assert response.status_code == 400
        assert "Invalid category" in response.json()["detail"]

    def test_get_jokes_invalid_limit(self):
        """Test getting jokes with invalid limit"""
        response = client.get("/jokes?limit=0")
        assert response.status_code == 400
        assert "Limit must be between 1 and 50" in response.json()["detail"]

        response = client.get("/jokes?limit=51")
        assert response.status_code == 400
        assert "Limit must be between 1 and 50" in response.json()["detail"]

    def test_add_joke(self):
        """Test adding a new joke"""
        new_joke = {
            "category": "programming",
            "steps": [
                {
                    "role": "setup",
                    "content": "Why do programmers prefer dark mode?"
                },
                {
                    "role": "punchline",
                    "content": "Because light attracts bugs!"
                }
            ]
        }

        response = client.post("/jokes", json=new_joke)
        assert response.status_code == 200

        data = response.json()
        assert data["category"] == new_joke["category"]
        assert "id" in data  # Check ID is returned

    def test_add_joke_duplicate(self):
        """Test adding a duplicate joke (same category)"""
        new_joke = {
            "category": "general",
            "steps": [
                {
                    "role": "setup",
                    "content": "Why did the scarecrow win an award?"
                },
                {
                    "role": "punchline",
                    "content": "He was outstanding in his field!"
                }
            ]
        }

        # Add the joke first
        response1 = client.post("/jokes", json=new_joke)
        assert response1.status_code == 200

        # Try to add the same joke again - should succeed with different ID
        response2 = client.post("/jokes", json=new_joke)
        assert response2.status_code == 200

        # Verify they have different IDs but same content
        joke1 = response1.json()
        joke2 = response2.json()
        assert joke1["id"] != joke2["id"]
        assert joke1["category"] == joke2["category"]

    def test_add_joke_no_steps(self):
        """Test adding a joke with no steps should fail"""
        new_joke = {"category": "programming", "steps": []}
        
        response = client.post("/jokes", json=new_joke)
        assert response.status_code == 422  # Validation error
        
        # Check the validation error details
        error_detail = response.json()["detail"]
        if isinstance(error_detail, list):
            # Pydantic returns a list of validation errors
            error_messages = [str(err.get("msg", "")) for err in error_detail]
            error_text = " ".join(error_messages).lower()
        else:
            error_text = str(error_detail).lower()
        
        assert "at least 1 item" in error_text or "min_length" in error_text

    def test_add_joke_with_steps(self):
        """Test adding a new joke with steps"""
        new_joke = {
            "category": "science",
            "steps": [
                {
                    "role": "setup",
                    "content": "Why don't scientists trust atoms?"
                },
                {
                    "role": "punchline", 
                    "content": "Because they make up everything!"
                }
            ]
        }

        response = client.post("/jokes", json=new_joke)
        assert response.status_code == 200

        data = response.json()
        assert data["category"] == new_joke["category"]
        assert "id" in data
        assert len(data["steps"]) == 2
        assert data["steps"][0]["content"] == "Why don't scientists trust atoms?"
        assert data["steps"][1]["content"] == "Because they make up everything!"

    def test_rate_joke(self):
        """Test rating a joke"""
        # First get a joke to rate
        response = client.get("/jokes?count=1")
        assert response.status_code == 200
        joke_id = response.json()["jokes"][0]["id"]

        rating_data = {"rating": 4.5}
        response = client.put(f"/jokes/{joke_id}/rating", json=rating_data)
        assert response.status_code == 200

        data = response.json()
        assert data["message"] == "Joke rated successfully"
        assert data["joke_id"] == joke_id
        assert data["rating"] == 4.5

    def test_rate_joke_invalid_rating(self):
        """Test rating with invalid rating value"""
        # First get a joke to test with
        response = client.get("/jokes?limit=1")
        assert response.status_code == 200
        joke_id = response.json()["jokes"][0]["id"]

        rating_data = {"rating": 6.0}  # Invalid: > 5
        response = client.put(f"/jokes/{joke_id}/rating", json=rating_data)
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
            "category": "general",
            "steps": [
                {
                    "role": "setup",
                    "content": "Test setup for deletion"
                },
                {
                    "role": "punchline",
                    "content": "Test punchline for deletion"
                }
            ]
        }
        response = client.post("/jokes", json=new_joke)
        assert response.status_code == 200
        joke_id = response.json()["id"]

        # Now delete it
        response = client.delete(f"/jokes/{joke_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["message"] == "Joke deleted successfully"
        assert data["joke_id"] == joke_id

    def test_delete_joke_not_found(self):
        """Test deleting a non-existent joke"""
        response = client.delete("/jokes/nonexistent")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
