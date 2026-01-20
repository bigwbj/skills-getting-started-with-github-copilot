"""
Tests for the Mergington High School API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add the src directory to the path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

# Create a test client
client = TestClient(app)


class TestActivitiesEndpoint:
    """Tests for the /activities endpoint"""

    def test_get_activities_returns_all_activities(self):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0
        assert "Chess Club" in data
        assert "Programming Class" in data

    def test_activities_have_required_fields(self):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)


class TestSignupEndpoint:
    """Tests for the /activities/{activity_name}/signup endpoint"""

    def test_signup_successful(self):
        """Test successful signup"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=newemail@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newemail@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]

    def test_signup_adds_participant_to_activity(self):
        """Test that signup adds the participant to the activity"""
        # Get initial count
        response = client.get("/activities")
        initial_count = len(response.json()["Chess Club"]["participants"])
        
        # Sign up
        client.post(
            "/activities/Chess%20Club/signup?email=test1@mergington.edu"
        )
        
        # Check count increased
        response = client.get("/activities")
        new_count = len(response.json()["Chess Club"]["participants"])
        assert new_count == initial_count + 1

    def test_signup_duplicate_email_fails(self):
        """Test that signing up with an existing email fails"""
        # First signup
        response1 = client.post(
            "/activities/Chess%20Club/signup?email=duplicate@mergington.edu"
        )
        assert response1.status_code == 200
        
        # Try to sign up again with same email
        response2 = client.post(
            "/activities/Chess%20Club/signup?email=duplicate@mergington.edu"
        )
        assert response2.status_code == 400
        data = response2.json()
        assert "already signed up" in data["detail"]

    def test_signup_nonexistent_activity_fails(self):
        """Test that signing up for a nonexistent activity fails"""
        response = client.post(
            "/activities/Nonexistent%20Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_with_special_characters_in_email(self):
        """Test signup with various email formats"""
        response = client.post(
            "/activities/Programming%20Class/signup?email=user%2Btest@mergington.edu"
        )
        assert response.status_code == 200


class TestUnregisterEndpoint:
    """Tests for the /activities/{activity_name}/unregister endpoint"""

    def test_unregister_successful(self):
        """Test successful unregister"""
        # First sign up
        client.post(
            "/activities/Tennis%20Club/signup?email=unregister_test@mergington.edu"
        )
        
        # Then unregister
        response = client.post(
            "/activities/Tennis%20Club/unregister?email=unregister_test@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "unregister_test@mergington.edu" in data["message"]

    def test_unregister_removes_participant(self):
        """Test that unregister removes the participant"""
        email = "remove_me@mergington.edu"
        
        # Sign up
        client.post(
            f"/activities/Basketball%20Team/signup?email={email}"
        )
        
        # Get count before unregister
        response = client.get("/activities")
        count_before = len(response.json()["Basketball Team"]["participants"])
        
        # Unregister
        client.post(
            f"/activities/Basketball%20Team/unregister?email={email}"
        )
        
        # Check count decreased
        response = client.get("/activities")
        count_after = len(response.json()["Basketball Team"]["participants"])
        assert count_after == count_before - 1

    def test_unregister_nonexistent_activity_fails(self):
        """Test that unregistering from nonexistent activity fails"""
        response = client.post(
            "/activities/Fake%20Club/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404

    def test_unregister_not_registered_fails(self):
        """Test that unregistering someone not registered fails"""
        response = client.post(
            "/activities/Debate%20Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"]


class TestRootEndpoint:
    """Tests for the root / endpoint"""

    def test_root_redirects_to_index(self):
        """Test that / redirects to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]
