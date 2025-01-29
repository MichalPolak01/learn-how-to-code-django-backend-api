import pytest
from django.test import TestCase
from ninja_jwt.tokens import RefreshToken
from ninja_extra.testing import TestClient

from authentication.models import User
from course.models import Course
from lesson.models import Lesson, StudentProgress
from module.models import Module

from .api import router


class LessonApiTestCase(TestCase):
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

        self.lesson = Lesson.objects.create(
            module=self.module,
            topic="Lesson 1",
            order=1
        )

    def get_access_token(self, user):
        """Helper function to get JWT token for a user"""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    

    @pytest.mark.django_db
    def test_add_lessons_with_content_success(self):
        """Test adding lessons to a module with valid data"""

        # Arrange
        access_token = self.get_access_token(self.teacher)
        headers = {"Authorization": f"Bearer {access_token}"}
        payload = [{"topic": "New Lesson 1", "order": 2}]

        # Act
        response = self.client.post(f"/modules/{self.module.id}/lessons", json=payload, headers=headers)

        # Assert
        assert response.status_code == 201
        assert len(response.json()) == 1
        assert response.json()[0]["topic"] == "New Lesson 1"


    @pytest.mark.django_db
    def test_add_lessons_module_not_found(self):
        """Test adding lessons to a non-existent module"""

        # Arrange
        access_token = self.get_access_token(self.teacher)
        headers = {"Authorization": f"Bearer {access_token}"}
        payload = [{"topic": "New Lesson 1", "order": 1}]

        # Act
        response = self.client.post("/modules/999/lessons", json=payload, headers=headers)

        # Assert
        assert response.status_code == 404
        assert response.json()["message"] == "Module with id 999 not found."


    @pytest.mark.django_db
    def test_get_list_lessons_for_module_success(self):
        """Test retrieving all lessons for a module"""

        # Arrange
        access_token = self.get_access_token(self.teacher)
        headers = {"Authorization": f"Bearer {access_token}"}

        # Act
        response = self.client.get(f"/modules/{self.module.id}/lessons", headers=headers)

        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["topic"] == "Lesson 1"


    @pytest.mark.django_db
    def test_get_list_lessons_module_not_found(self):
        """Test retrieving lessons for a non-existent module"""

        # Arrange
        access_token = self.get_access_token(self.teacher)
        headers = {"Authorization": f"Bearer {access_token}"}

        # Act
        response = self.client.get("/modules/999/lessons", headers=headers)

        # Assert
        assert response.status_code == 404
        assert response.json()["message"] == "Module with id 999 not found."


    @pytest.mark.django_db
    def test_get_lesson_success(self):
        """Test retrieving a specific lesson"""

        # Arrange
        access_token = self.get_access_token(self.teacher)
        headers = {"Authorization": f"Bearer {access_token}"}

        # Act
        response = self.client.get(f"/lessons/{self.lesson.id}", headers=headers)

        # Assert
        assert response.status_code == 200
        assert response.json()["topic"] == "Lesson 1"


    @pytest.mark.django_db
    def test_get_lesson_not_found(self):
        """Test retrieving a non-existent lesson"""

        # Arrange
        access_token = self.get_access_token(self.teacher)
        headers = {"Authorization": f"Bearer {access_token}"}

        # Act
        response = self.client.get("/lessons/999", headers=headers)

        # Assert
        assert response.status_code == 404
        assert response.json()["message"] == "Lesson with id 999 not found."


    @pytest.mark.django_db
    def test_get_lesson_unauthorized(self):
        """Test retrieving a lesson from a private course as a non-author"""

        # Arrange
        self.course.is_public = False
        self.course.save()
        access_token = self.get_access_token(self.student)
        headers = {"Authorization": f"Bearer {access_token}"}

        # Act
        response = self.client.get(f"/lessons/{self.lesson.id}", headers=headers)

        # Assert
        assert response.status_code == 403
        assert response.json()["message"] == "You do not have permission to view this lesson."


    @pytest.mark.django_db
    def test_update_lesson_success(self):
        """Test updating a specific lesson"""

        # Arrange
        access_token = self.get_access_token(self.teacher)
        headers = {"Authorization": f"Bearer {access_token}"}
        payload = {"topic": "Updated Lesson"}

        # Act
        response = self.client.patch(f"/lessons/{self.lesson.id}", json=payload, headers=headers)

        # Assert
        assert response.status_code == 200
        assert response.json()["topic"] == "Updated Lesson"

    @pytest.mark.django_db
    def test_update_lesson_not_found(self):
        """Test updating a non-existent lesson"""

        # Arrange
        access_token = self.get_access_token(self.teacher)
        headers = {"Authorization": f"Bearer {access_token}"}
        payload = {"topic": "Updated Lesson"}

        # Act
        response = self.client.patch("/lessons/999", json=payload, headers=headers)

        # Assert
        assert response.status_code == 404
        assert response.json()["message"] == "Lesson with id 999 not found."


    @pytest.mark.django_db
    def test_delete_lesson_success(self):
        """Test deleting a specific lesson"""

        # Arrange
        access_token = self.get_access_token(self.teacher)
        headers = {"Authorization": f"Bearer {access_token}"}

        # Act
        response = self.client.delete(f"/lessons/{self.lesson.id}", headers=headers)

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == "Lesson deleted successfully."

    @pytest.mark.django_db
    def test_delete_lesson_not_found(self):
        """Test deleting a non-existent lesson"""

        # Arrange
        access_token = self.get_access_token(self.teacher)
        headers = {"Authorization": f"Bearer {access_token}"}

        # Act
        response = self.client.delete("/lessons/999", headers=headers)

        # Assert 
        assert response.status_code == 404
        assert response.json()["message"] == "Lesson with id 999 not found."


    @pytest.mark.django_db
    def test_add_student_progress_success(self):
        """Test adding student progress"""

        # Arrange
        access_token = self.get_access_token(self.student)
        headers = {"Authorization": f"Bearer {access_token}"}
        payload = {
            "lesson_id": self.lesson.id,
            "introduction_completed": True,
            "quiz_score": 80,
            "assignment_score": 85,
        }

        # Act
        response = self.client.post("/student-progress", json=payload, headers=headers)
        progress = StudentProgress.objects.get(user=self.student, lesson=self.lesson)

        # assert
        assert response.status_code == 201
        assert response.json()["message"] == "Progress added or updated successfully."

        assert progress.introduction_completed is True
        assert progress.quiz_score == 80
        assert progress.assignment_score == 85


    @pytest.mark.django_db
    def test_update_student_progress_success(self):
        """Test updating existing student progress"""

        # Arrange
        StudentProgress.objects.create(
            user=self.student,
            lesson=self.lesson,
            introduction_completed=False,
            quiz_score=50,
            assignment_score=60,
        )
        access_token = self.get_access_token(self.student)
        headers = {"Authorization": f"Bearer {access_token}"}
        payload = {"lesson_id": self.lesson.id, "quiz_score": 90}

        # Act
        response = self.client.post("/student-progress", json=payload, headers=headers)
        progress = StudentProgress.objects.get(user=self.student, lesson=self.lesson)

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == "Progress added or updated successfully."

        assert progress.quiz_score == 90
        assert progress.assignment_score == 60


    @pytest.mark.django_db
    def test_add_student_progress_lesson_not_found(self):
        """Test adding progress to a non-existent lesson"""

        # Arrange
        access_token = self.get_access_token(self.student)
        headers = {"Authorization": f"Bearer {access_token}"}
        payload = {"lesson_id": 999, "quiz_score": 80}

        # Act
        response = self.client.post("/student-progress", json=payload, headers=headers)

        # Assert
        assert response.status_code == 400
        assert "Error" in response.json()["message"]


    @pytest.mark.django_db
    def test_get_student_progress_success(self):
        """Test retrieving student progress for a course"""
        
        # Arrange
        StudentProgress.objects.create(
            user=self.student,
            lesson=self.lesson,
            introduction_completed=True,
            quiz_score=90,
            assignment_score=95,
            lesson_completed=True,
        )
        access_token = self.get_access_token(self.student)
        headers = {"Authorization": f"Bearer {access_token}"}

        # Act
        response = self.client.get(f"/student-progress/{self.course.id}", headers=headers)

        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["lesson_id"] == self.lesson.id
        assert response.json()[0]["quiz_score"] == 90


    @pytest.mark.django_db
    def test_get_student_progress_no_progress(self):
        """Test retrieving progress when no progress exists"""

        # Arrange
        access_token = self.get_access_token(self.student)
        headers = {"Authorization": f"Bearer {access_token}"}

        # Act
        response = self.client.get(f"/student-progress/{self.course.id}", headers=headers)

        # Assert
        assert response.status_code == 404
        assert response.json()["message"] == f"No progress found for user {self.student.id} in course {self.course.id}."