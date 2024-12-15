import pytest
from django.test import TestCase
from ninja_extra.testing import TestClient
from ninja_jwt.tokens import RefreshToken

from authentication.models import User
from course.models import Course
from lesson.models import Lesson
from lesson_content.models import LessonAssignment, LessonIntroduction, LessonQuiz
from module.models import Module

from .api import router


class LessonContentApiTestCase(TestCase):
    def setUp(self):
        self.client = TestClient(router)
        
        self.teacher = User.objects.create_user(username='Teacher1', email='teacher1@gmail.com', password='Teacher@123', role='TEACHER')
        self.student = User.objects.create_user(username='Student1', email='student1@gmail.com', password='Student@123', role='USER')
        
        self.course = Course.objects.create(
            name="Course 1",
            description="Test Course",
            author=self.teacher,
            is_public=True
        )

        self.module = Module.objects.create(
            name="Module 1",
            course=self.course,
            order=1,
            is_visible=True
        )

        self.lesson = Lesson.objects.create(
            topic="Lesson 1",
            module=self.module,
            order=1
        )

    def get_access_token(self, user):
        """Helper to generate JWT access token"""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)


    @pytest.mark.django_db
    def test_create_lesson_introduction_success(self):
        """Test creating an introduction for a lesson"""

        # Arrange
        access_token = self.get_access_token(self.teacher)
        headers = {"Authorization": f"Bearer {access_token}"}
        payload = {"description": "<p>Introduction content</p>"}

        # Act
        response = self.client.post(f"/{self.lesson.id}/introduction", json=payload, headers=headers)

        # Assert
        assert response.status_code == 201
        assert response.json()["description"] == "<p>Introduction content</p>"
        assert LessonIntroduction.objects.filter(lesson=self.lesson).exists()


    @pytest.mark.django_db
    def test_create_lesson_introduction_already_exists(self):
        """Test creating an introduction when it already exists"""

        # Arrange
        LessonIntroduction.objects.create(lesson=self.lesson, description="Existing introduction")
        access_token = self.get_access_token(self.teacher)
        headers = {"Authorization": f"Bearer {access_token}"}
        payload = {"description": "<p>New introduction</p>"}

        # Act
        response = self.client.post(f"/{self.lesson.id}/introduction", json=payload, headers=headers)

        # Assert
        assert response.status_code == 400
        assert "already exists" in response.json()["message"]


    @pytest.mark.django_db
    def test_create_lesson_introduction_generate(self):
        """Test generating an introduction for a lesson"""

        # Arrange
        access_token = self.get_access_token(self.teacher)
        headers = {"Authorization": f"Bearer {access_token}"}

        # Act
        response = self.client.post(f"/{self.lesson.id}/introduction?generate=true", headers=headers)

        # Assert
        assert response.status_code == 201
        assert LessonIntroduction.objects.filter(lesson=self.lesson).exists()


    @pytest.mark.django_db
    def test_create_lesson_introduction_lesson_not_found(self):
        """Test creating an introduction for a non-existent lesson"""

        # Arrange
        access_token = self.get_access_token(self.teacher)
        headers = {"Authorization": f"Bearer {access_token}"}
        payload = {"description": "<p>Introduction content</p>"}

        # Act
        response = self.client.post("/999/introduction", json=payload, headers=headers)

        # Assert
        assert response.status_code == 404
        assert "Lesson with id 999 not found" in response.json()["message"]


    @pytest.mark.django_db
    def test_get_lesson_introduction_success(self):
        """Test retrieving an introduction for a lesson"""

        # Arrange
        LessonIntroduction.objects.create(lesson=self.lesson, description="<p>Lesson introduction</p>")
        access_token = self.get_access_token(self.teacher)
        headers = {"Authorization": f"Bearer {access_token}"}

        # Act
        response = self.client.get(f"/{self.lesson.id}/introduction", headers=headers)

        # Assert
        assert response.status_code == 200
        assert response.json()["description"] == "<p>Lesson introduction</p>"


    @pytest.mark.django_db
    def test_get_lesson_introduction_not_found(self):
        """Test retrieving an introduction that does not exist"""

        # Arrange
        access_token = self.get_access_token(self.teacher)
        headers = {"Authorization": f"Bearer {access_token}"}

        # Act
        response = self.client.get(f"/{self.lesson.id}/introduction", headers=headers)

        # Assert
        assert response.status_code == 404
        assert "Introduction for lesson" in response.json()["message"]


    @pytest.mark.django_db
    def test_create_lesson_quiz_success(self):
        """Test creating a quiz for a lesson"""

        # Arrange
        access_token = self.get_access_token(self.teacher)
        headers = {"Authorization": f"Bearer {access_token}"}
        payload = {
            "question": "What is Python?",
            "answers": [
                {"answer": "A snake", "is_correct": False},
                {"answer": "A programming language", "is_correct": True}
            ]
        }

        # Act
        response = self.client.post(f"/{self.lesson.id}/quiz", json=payload, headers=headers)

        # Assert
        assert response.status_code == 201
        assert response.json()["question"] == "What is Python?"
        assert LessonQuiz.objects.filter(lesson=self.lesson).exists()


    @pytest.mark.django_db
    def test_create_lesson_quiz_generate(self):
        """Test generating a quiz for a lesson"""

        # Arrange
        access_token = self.get_access_token(self.teacher)
        headers = {"Authorization": f"Bearer {access_token}"}

        # Act
        response = self.client.post(f"/{self.lesson.id}/quiz?generate=true", headers=headers)

        # Assert
        assert response.status_code == 201
        assert LessonQuiz.objects.filter(lesson=self.lesson).exists()


    @pytest.mark.django_db
    def test_create_lesson_quiz_lesson_not_found(self):
        """Test creating a quiz for a non-existent lesson"""

        # Arrange
        access_token = self.get_access_token(self.teacher)
        headers = {"Authorization": f"Bearer {access_token}"}
        payload = {
            "question": "What is Python?",
            "answers": [
                {"answer": "A snake", "is_correct": False},
                {"answer": "A programming language", "is_correct": True}
            ]
        }

        # Act
        response = self.client.post("/999/quiz", json=payload, headers=headers)

        # Assert
        assert response.status_code == 404
        assert "Lesson with id 999 not found" in response.json()["message"]


    @pytest.mark.django_db
    def test_create_assignment_success(self):
        """Test creating an assignment for a lesson"""

        # Arrange
        access_token = self.get_access_token(self.teacher)
        headers = {"Authorization": f"Bearer {access_token}"}
        payload = {"instructions": "<p>Complete this assignment</p>"}

        # Act
        response = self.client.post(f"/{self.lesson.id}/assignment", json=payload, headers=headers)

        # Assert
        assert response.status_code == 201
        assert response.json()["instructions"] == "<p>Complete this assignment</p>"
        assert LessonAssignment.objects.filter(lesson=self.lesson).exists()


    @pytest.mark.django_db
    def test_create_assignment_generate(self):
        """Test generating an assignment for a lesson"""

        # Arrange
        access_token = self.get_access_token(self.teacher)
        headers = {"Authorization": f"Bearer {access_token}"}

        # Act
        response = self.client.post(f"/{self.lesson.id}/assignment?generate=true", headers=headers)

        # Assert
        assert response.status_code == 201
        assert LessonAssignment.objects.filter(lesson=self.lesson).exists()

    @pytest.mark.django_db
    def test_create_assignment_already_exists(self):
        """Test creating an assignment when it already exists"""

        # Arrange
        LessonAssignment.objects.create(lesson=self.lesson, instructions="Existing assignment")
        access_token = self.get_access_token(self.teacher)
        headers = {"Authorization": f"Bearer {access_token}"}
        payload = {"instructions": "<p>New assignment instructions</p>"}

        # Act
        response = self.client.post(f"/{self.lesson.id}/assignment", json=payload, headers=headers)

        # Assert
        assert response.status_code == 400
        assert "already exists" in response.json()["message"]


    @pytest.mark.django_db
    def test_create_assignment_lesson_not_found(self):
        """Test creating an assignment for a non-existent lesson"""

        # Arrange
        access_token = self.get_access_token(self.teacher)
        headers = {"Authorization": f"Bearer {access_token}"}
        payload = {"instructions": "<p>Complete this assignment</p>"}

        # Act
        response = self.client.post("/999/assignment", json=payload, headers=headers)

        # Assert
        assert response.status_code == 404
        assert "Lesson with id 999 not found" in response.json()["message"]


    @pytest.mark.django_db
    def test_evaluate_assignment_success(self):
        """Test evaluating a user's code for an assignment"""

        # Arrange
        LessonAssignment.objects.create(lesson=self.lesson, instructions="Write a Python function")
        access_token = self.get_access_token(self.student)
        headers = {"Authorization": f"Bearer {access_token}"}
        payload = {
            "lesson_id": self.lesson.id,
            "user_code": "def example(): pass"
        }

        # Act
        response = self.client.post("/assignments/evaluate", json=payload, headers=headers)

        # Assert
        assert response.status_code == 200
        assert "assignment_score" in response.json()
        assert "message" in response.json()
        # Verify score is within range
        assert 0 <= response.json()["assignment_score"] <= 100


    @pytest.mark.django_db
    def test_evaluate_assignment_no_assignment(self):
        """Test evaluating a lesson without an assignment"""

        # Arrange
        access_token = self.get_access_token(self.student)
        headers = {"Authorization": f"Bearer {access_token}"}
        payload = {
            "lesson_id": self.lesson.id,
            "user_code": "def example(): pass"
        }

        # Act
        response = self.client.post("/assignments/evaluate", json=payload, headers=headers)

        # Assert
        assert response.status_code == 404
        assert "No assignment found" in response.json()["message"]


    @pytest.mark.django_db
    def test_evaluate_assignment_lesson_not_found(self):
        """Test evaluating an assignment for a non-existent lesson"""

        # Arrange
        access_token = self.get_access_token(self.student)
        headers = {"Authorization": f"Bearer {access_token}"}
        payload = {
            "lesson_id": 999,
            "user_code": "def example(): pass"
        }

        # Act
        response = self.client.post("/assignments/evaluate", json=payload, headers=headers)

        # Assert
        assert response.status_code == 404
        assert "Lesson with id 999 not found" in response.json()["message"]


    @pytest.mark.django_db
    def test_evaluate_assignment_invalid_code(self):
        """Test evaluating invalid user code"""

        # Arrange
        LessonAssignment.objects.create(lesson=self.lesson, instructions="Write a Python function")
        access_token = self.get_access_token(self.student)
        headers = {"Authorization": f"Bearer {access_token}"}
        payload = {
            "lesson_id": self.lesson.id,
            "user_code": "def : pass"  # Invalid code
        }

        # Act
        response = self.client.post("/assignments/evaluate", json=payload, headers=headers)

        # Assert
        assert response.status_code == 200
        assert response.json()["assignment_score"] < 50  # Expect a low score for invalid code
        assert "message" in response.json()
