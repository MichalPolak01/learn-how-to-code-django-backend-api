from django.test import TestCase
from ninja_extra.testing import TestClient
from ninja_jwt.tokens import RefreshToken
import pytest

from authentication.models import User
from course.models import Course
from module.models import Module

from .api import router


class ModuleApiTestCase(TestCase):
    def setUp(self):
        self.client = TestClient(router)

        self.teacher = User.objects.create_user(username='Teacher1', email='teacher1@gmail.com', password='Teacher@123', role='TEACHER')
        self.student = User.objects.create_user(username='Student1', email='student1@gmail.com', password='Student@123', role='USER')
        
        self.course = Course.objects.create(
            name="Course 1",
            description="Test Course",
            author=self.teacher,
            is_public=True,
        )

        self.module = Module.objects.create(
            course=self.course,
            name="Module 1",
            order=1,
            is_visible=True
        )

    def get_access_token(self, user):
        """Helper function to get JWT token for a user"""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)


    @pytest.mark.django_db
    def test_add_modules_with_lessons(self):
        """Test adding modules with lessons to a course"""

        # Arrange
        access_token = self.get_access_token(self.teacher)
        headers = {"Authorization": f"Bearer {access_token}"}
        payload = [
            {"name": "Module 2", "order": 2},
            {"name": "Module 3", "order": 3}
        ]

        # Act
        response = self.client.post(f"/{self.course.id}/modules", json=payload, headers=headers)

        # Assert
        assert response.status_code == 201
        assert len(response.json()) == 2
        assert response.json()[0]["name"] == "Module 2"


    @pytest.mark.django_db
    def test_add_modules_with_lessons_to_unexisting_course(self):
        """Test adding modules with lessons to not existing course"""
        
        # Arrange
        access_token = self.get_access_token(self.teacher)
        headers = {"Authorization": f"Bearer {access_token}"}
        payload = [
            {"name": "Module 2", "order": 2},
            {"name": "Module 3", "order": 3}
        ]

        # Act
        response = self.client.post(f"/999/modules", json=payload, headers=headers)

        # Assert
        assert response.status_code == 404
        assert response.json()["message"] == "Course with id 999 not found for the current user."


    @pytest.mark.django_db
    def test_get_list_modules_for_course(self):
        """Test retrieving modules for a course"""

        # Arrange
        access_token = self.get_access_token(self.teacher)
        headers = {"Authorization": f"Bearer {access_token}"}

        # Act
        response = self.client.get(f"/{self.course.id}/modules", headers=headers)

        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["name"] == "Module 1"


    @pytest.mark.django_db
    def test_get_list_modules_for_non_existing_course(self):
        """Test retrieving modules for non existing course"""
        
        # Arrange
        access_token = self.get_access_token(self.teacher)
        headers = {"Authorization": f"Bearer {access_token}"}

        # Act
        response = self.client.get(f"/999/modules", headers=headers)

        # Assert
        assert response.status_code == 404
        assert response.json()["message"] == "Course with id 999 not found."


    @pytest.mark.django_db
    def test_get_module(self):
        """Test retrieving a specific module"""

        # Arrange
        access_token = self.get_access_token(self.teacher)
        headers = {"Authorization": f"Bearer {access_token}"}

        # Act
        response = self.client.get(f"/{self.course.id}/modules/{self.module.id}", headers=headers)

        # Assert
        assert response.status_code == 200
        assert response.json()["name"] == "Module 1"


    @pytest.mark.django_db
    def test_get_non_existing_module(self):
        """Test retrieving a non existing module"""
        
        # Arrange
        access_token = self.get_access_token(self.teacher)
        headers = {"Authorization": f"Bearer {access_token}"}

        # Act
        response = self.client.get(f"/{self.course.id}/modules/999", headers=headers)

        # Assert
        assert response.status_code == 404
        assert response.json()["message"] == "Module with id 999 not found."


    @pytest.mark.django_db
    def test_update_module(self):
        """Test updating a specific module"""

        # Arrange
        access_token = self.get_access_token(self.teacher)
        headers = {"Authorization": f"Bearer {access_token}"}
        payload = {"name": "Updated Module", "order": 2}

        # Act
        response = self.client.patch(f"/{self.course.id}/modules/{self.module.id}", json=payload, headers=headers)

        # Assert
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Module"
        assert response.json()["order"] == 2


    @pytest.mark.django_db
    def test_update_non_existing_module(self):
        """Test updating a non existing module"""
        
        # Arrange
        access_token = self.get_access_token(self.teacher)
        headers = {"Authorization": f"Bearer {access_token}"}
        payload = {"name": "Updated Module", "order": 2}

        # Act
        response = self.client.patch(f"/{self.course.id}/modules/999", json=payload, headers=headers)

        # Assert
        assert response.status_code == 404
        assert response.json()["message"] == "Module with id 999 not found."


    @pytest.mark.django_db
    def test_delete_module(self):
        """Test deleting a specific module"""

        # Arrange
        access_token = self.get_access_token(self.teacher)
        headers = {"Authorization": f"Bearer {access_token}"}

        # Act
        response = self.client.delete(f"/{self.course.id}/modules/{self.module.id}", headers=headers)

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == "Module deleted successfully."


    @pytest.mark.django_db
    def test_delete_non_existing_module(self):
        """Test deleting a non existing module"""
        
        # Arrange
        access_token = self.get_access_token(self.teacher)
        headers = {"Authorization": f"Bearer {access_token}"}

        # Act
        response = self.client.delete(f"/{self.course.id}/modules/999", headers=headers)

        # Assert
        assert response.status_code == 404
        assert response.json()["message"] == "Module with id 999 not found."


    @pytest.mark.django_db
    def test_generate_lessons_for_modules(self):
        """Test generating lessons for modules"""

        # Arrange
        access_token = self.get_access_token(self.teacher)
        headers = {"Authorization": f"Bearer {access_token}"}
        payload = [{"name": "Generated Module", "order": 1}]

        # Act
        response = self.client.post(f"/{self.course.id}/modules?generate=true", json=payload, headers=headers)

        # Assert
        assert response.status_code == 201
        assert len(response.json()) == 1
        assert response.json()[0]["name"] == "Generated Module"

        # Verify lessons were created
        module = Module.objects.get(name="Generated Module")
        lessons = module.lessons.all()
        assert lessons.count() > 0 