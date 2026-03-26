import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)

class TestRootEndpoint:
    def test_root_redirects_to_static_html(self):
        response = client.get("/")
        assert response.status_code == 200  # In test environment, may serve directly

class TestActivitiesEndpoint:
    def test_get_activities_returns_all_activities(self):
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) == 9  # All activities present
        assert "Chess Club" in data
        assert "Programming Class" in data

    def test_get_activities_structure(self):
        response = client.get("/activities")
        data = response.json()
        chess_club = data["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)
        assert chess_club["max_participants"] == 12

class TestSignupEndpoint:
    def test_successful_signup(self):
        response = client.post("/activities/Chess%20Club/signup?email=newstudent@mergington.edu")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]

        # Verify participant was added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert "newstudent@mergington.edu" in activities["Chess Club"]["participants"]

    def test_signup_nonexistent_activity(self):
        response = client.post("/activities/Nonexistent%20Club/signup?email=test@mergington.edu")
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_duplicate_signup(self):
        # First signup
        client.post("/activities/Chess%20Club/signup?email=duplicate@mergington.edu")
        
        # Second signup with same email
        response = client.post("/activities/Chess%20Club/signup?email=duplicate@mergington.edu")
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_signup_with_empty_email(self):
        response = client.post("/activities/Chess%20Club/signup?email=")
        assert response.status_code == 200  # Empty email is accepted as valid string

class TestUnregisterEndpoint:
    def test_successful_unregister(self):
        # First signup
        client.post("/activities/Chess%20Club/signup?email=unregister@mergington.edu")
        
        # Then unregister
        response = client.delete("/activities/Chess%20Club/signup?email=unregister@mergington.edu")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "unregister@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]

        # Verify participant was removed
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert "unregister@mergington.edu" not in activities["Chess Club"]["participants"]

    def test_unregister_nonexistent_activity(self):
        response = client.delete("/activities/Nonexistent%20Club/signup?email=test@mergington.edu")
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_unregister_not_signed_up(self):
        response = client.delete("/activities/Chess%20Club/signup?email=notsignedup@mergington.edu")
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"]

    def test_unregister_with_empty_email(self):
        response = client.delete("/activities/Chess%20Club/signup?email=")
        assert response.status_code == 400  # Not signed up

class TestDataIntegrity:
    def test_participants_list_updated_correctly(self):
        # Check initial count
        response = client.get("/activities")
        initial_count = len(response.json()["Chess Club"]["participants"])
        
        # Add participant
        client.post("/activities/Chess%20Club/signup?email=integrity@mergington.edu")
        
        # Check count increased
        response = client.get("/activities")
        new_count = len(response.json()["Chess Club"]["participants"])
        assert new_count == initial_count + 1
        
        # Remove participant
        client.delete("/activities/Chess%20Club/signup?email=integrity@mergington.edu")
        
        # Check count back to original
        response = client.get("/activities")
        final_count = len(response.json()["Chess Club"]["participants"])
        assert final_count == initial_count

    def test_multiple_activities_independent(self):
        # Signup for Chess Club
        client.post("/activities/Chess%20Club/signup?email=multi@mergington.edu")
        
        # Signup for Programming Class
        client.post("/activities/Programming%20Class/signup?email=multi@mergington.edu")
        
        # Check both have the participant
        response = client.get("/activities")
        activities = response.json()
        assert "multi@mergington.edu" in activities["Chess Club"]["participants"]
        assert "multi@mergington.edu" in activities["Programming Class"]["participants"]
        
        # Remove from Chess Club only
        client.delete("/activities/Chess%20Club/signup?email=multi@mergington.edu")
        
        # Check Programming Class still has it
        response = client.get("/activities")
        activities = response.json()
        assert "multi@mergington.edu" not in activities["Chess Club"]["participants"]
        assert "multi@mergington.edu" in activities["Programming Class"]["participants"]