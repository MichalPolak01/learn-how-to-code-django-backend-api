import datetime
from django.test import TestCase
from ninja_extra.testing import TestClient
from ninja_jwt.tokens import RefreshToken
import pytest

from lesson.models import Lesson, StudentProgress
from module.models import Module
from .api import generate_modules, router
from .models import Course, User


class NinjaCourseTestCase(TestCase):
    def setUp(self):
        self.client = TestClient(router)

        self.teacher = User.objects.create_user(username='Teacher1', email='teacher1@gmail.com', password='Teacher@123', role='TEACHER')
        self.student = User.objects.create_user(username='Student1', email='student1@gmail.com', password='Student@123', role='USER')

        self.course_data = {
            "name": "Python Basics",
            "description": "Learn Python from scratch",
            "is_public": True,
            "image": "",
            "creator_state": "details"
        }


    def get_access_token(self, user):
        """Helper function to get JWT token for a user"""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    

    @pytest.mark.django_db
    def test_create_course_success(self):
        """Test course creation by a teacher"""

        # Arrange
        access_token = self.get_access_token(self.teacher)
        headers = {"Authorization": f"Bearer {access_token}"}
        payload = self.course_data

        # Act
        response = self.client.post("", json=payload, headers=headers)

        # Assert
        assert response.status_code == 201
        assert response.json()["name"] == payload["name"]


    @pytest.mark.django_db
    def test_create_course_unauthorized(self):
        """Test course creation by a non-teacher"""

        # Arrange
        access_token = self.get_access_token(self.student)
        headers = {"Authorization": f"Bearer {access_token}"}
        payload = self.course_data

        # Act
        response = self.client.post("", json=payload, headers=headers)

        # Assert
        assert response.status_code == 400
        assert response.json()["message"] == "Only teachers can create courses."


    @pytest.mark.django_db
    def test_create_course_duplicate_name(self):
        """Test course creation with a duplicate name"""
        
        # Arrange
        Course.objects.create(name=self.course_data["name"], author=self.teacher, is_public=True)
        access_token = self.get_access_token(self.teacher)
        headers = {"Authorization": f"Bearer {access_token}"}
        payload = self.course_data

        # Act
        response = self.client.post("", json=payload, headers=headers)

        # Assert
        assert response.status_code == 400
        assert response.json()["message"] == "A course with this name already exists."


    @pytest.mark.django_db
    def test_get_list_public_courses(self):
        """Test retrieving public courses"""

        # Arrange
        Course.objects.create(name="Course 1", description="Test 1", author=self.teacher, is_public=True)
        Course.objects.create(name="Course 2", description="Test 2", author=self.teacher, is_public=False)
        access_token = self.get_access_token(self.student)
        headers = {"Authorization": f"Bearer {access_token}"}

        # Act
        response = self.client.get("", headers=headers)

        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 1


    @pytest.mark.django_db
    def test_get_my_courses(self):
        """Test retrieving courses created by the authenticated teacher"""

        # Arrange
        Course.objects.create(name="Course 1", author=self.teacher, is_public=True)
        Course.objects.create(name="Course 2", author=self.teacher, is_public=False)
        access_token = self.get_access_token(self.teacher)
        headers = {"Authorization": f"Bearer {access_token}"}

        # Act
        response = self.client.get("", headers=headers, params={"sortBy": "my"})

        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 2


    @pytest.mark.django_db
    def test_get_latest_courses(self):
        """Test retrieving last updated courses"""

        # Arrange
        Course.objects.create(name="Course 1", author=self.teacher, is_public=True)
        Course.objects.create(name="Course 2", author=self.teacher, is_public=True)
        access_token = self.get_access_token(self.teacher)
        headers = {"Authorization": f"Bearer {access_token}"}

        # Act
        response = self.client.get("", headers=headers, params={"sortBy": "latest"})

        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 2
        
        course1_last_updated = datetime.datetime.fromisoformat(response.json()[0]['last_updated'])
        course2_last_updated = datetime.datetime.fromisoformat(response.json()[1]['last_updated'])

        assert course1_last_updated >= course2_last_updated


    @pytest.mark.django_db
    def test_get_highest_rated_courses(self):
        """Test retrieving highest rated courses"""

        # Arrange
        Course.objects.create(name="Course 1", author=self.teacher, is_public=True, rating='3.5')
        Course.objects.create(name="Course 2", author=self.teacher, is_public=True, rating='1.0')
        access_token = self.get_access_token(self.teacher)
        headers = {"Authorization": f"Bearer {access_token}"}

        # Act
        response = self.client.get("", headers=headers, params={"sortBy": "highest-rated"})

        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 2
        
        rating_course1 = float(response.json()[0]['rating'])
        rating_course2 = float(response.json()[1]['rating'])

        assert rating_course1 > rating_course2

    @pytest.mark.django_db
    def test_get_courses_with_limit(self):
        """Test retrieving courses with limit"""

        # Arrange
        Course.objects.create(name="Course 1", author=self.teacher, is_public=True)
        Course.objects.create(name="Course 2", author=self.teacher, is_public=True)
        access_token = self.get_access_token(self.teacher)
        headers = {"Authorization": f"Bearer {access_token}"}

        # Act
        response = self.client.get("?limit=1", headers=headers)

        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 1


    @pytest.mark.django_db
    def test_get_courses_with_wrong_param(self):
        """Test retrieving courses with wrong param"""

        # Arrange
        Course.objects.create(name="Course 1", author=self.teacher, is_public=True)
        Course.objects.create(name="Course 2", author=self.teacher, is_public=True)
        access_token = self.get_access_token(self.teacher)
        headers = {"Authorization": f"Bearer {access_token}"}

        # Act
        response = self.client.get("?sortBy=wrong-param", headers=headers)

        # Assert
        assert response.status_code == 400

    @pytest.mark.django_db
    def test_get_enrolled_courses(self):
        """Test retrieving IDs of enrolled courses"""

        # Arrange
        Course.objects.create(name="Course 1", author=self.teacher, is_public=True)
        Course.objects.create(name="Course 2", author=self.teacher, is_public=True)
        access_token = self.get_access_token(self.student)
        headers = {"Authorization": f"Bearer {access_token}"}

        # Act
        response = self.client.get("/stats", headers=headers)

        print(response.json())

        # Assert
        assert response.status_code == 200
        assert response.json()['courses_count'] == 2
        assert response.json()['students_count'] == 1
        assert response.json()['completed_lessons'] == 0


    @pytest.mark.django_db
    def test_get_enrolled_courses(self):
        """Test retrieving IDs of enrolled courses"""

        # Arrange
        course = Course.objects.create(name="Course 1", author=self.teacher, is_public=True)
        course.students.add(self.student)
        access_token = self.get_access_token(self.student)
        headers = {"Authorization": f"Bearer {access_token}"}

        # Act
        response = self.client.get("/enrolled", headers=headers)

        # Assert
        assert response.status_code == 200
        assert response.json() == [course.id]


    @pytest.mark.django_db
    def test_get_public_course_success(self):
        """Test retrieving details of a public course"""

        # Arrange
        course = Course.objects.create(name="Course 1", author=self.teacher, is_public=True)
        access_token = self.get_access_token(self.student)
        headers = {"Authorization": f"Bearer {access_token}"}

        # Act
        response = self.client.get(f"/{course.id}", headers=headers)

        # Assert
        assert response.status_code == 200
        assert response.json()["name"] == course.name


    @pytest.mark.django_db
    def test_get_private_course_unauthorized(self):
        """Test retrieving a private course without being the author"""

        # Arrange
        course = Course.objects.create(name="Private Course", author=self.teacher, is_public=False)
        access_token = self.get_access_token(self.student)
        headers = {"Authorization": f"Bearer {access_token}"}

        # Act
        response = self.client.get(f"/{course.id}", headers=headers)

        # Assert
        assert response.status_code == 403
        assert response.json()["message"] == "You are not authorized to access this course."


    @pytest.mark.django_db
    def test_get_non_existing_course(self):
        """Test retrieving details of a non existing course"""

        # Arrange
        access_token = self.get_access_token(self.student)
        headers = {"Authorization": f"Bearer {access_token}"}

        # Act
        response = self.client.get(f"/1", headers=headers)

        # Assert
        assert response.status_code == 404


    @pytest.mark.django_db
    def test_update_course_success(self):
        """Test updating a course by its author"""

        # Arrange
        course = Course.objects.create(name="Original Name", author=self.teacher, is_public=True)
        access_token = self.get_access_token(self.teacher)
        headers = {"Authorization": f"Bearer {access_token}"}
        payload = {"name": "Updated Name"}

        # Act
        response = self.client.patch(f"/{course.id}", json=payload, headers=headers)

        # Assert
        assert response.status_code == 200
        assert response.json()["name"] == payload["name"]

    @pytest.mark.django_db
    def test_update_course_name_taken(self):
        """Test updating a course with a duplicate name"""

        # Arrange
        Course.objects.create(name="Existing Name", author=self.teacher, is_public=True)
        course = Course.objects.create(name="Original Name", author=self.teacher, is_public=True)
        access_token = self.get_access_token(self.teacher)
        headers = {"Authorization": f"Bearer {access_token}"}
        payload = {"name": "Existing Name"}

        # Act
        response = self.client.patch(f"/{course.id}", json=payload, headers=headers)

        # Assert
        assert response.status_code == 400
        assert response.json()["message"] == "This course name is already taken by another course."

    @pytest.mark.django_db
    def test_update_non_existing_course(self):
        """Test updating a course which not exists"""

        # Arrange
        access_token = self.get_access_token(self.teacher)
        headers = {"Authorization": f"Bearer {access_token}"}
        payload = {"name": "Updated Name"}

        # Act
        response = self.client.patch(f"/1", json=payload, headers=headers)

        # Assert
        assert response.status_code == 404


    @pytest.mark.django_db
    def test_delete_course_success(self):
        """Test deleting a course by its author"""

        # Arrange
        course = Course.objects.create(name="Course to Delete", author=self.teacher, is_public=True)
        access_token = self.get_access_token(self.teacher)
        headers = {"Authorization": f"Bearer {access_token}"}

        # Act
        response = self.client.delete(f"/{course.id}", headers=headers)

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == "Course deleted successfully."

    @pytest.mark.django_db
    def test_delete_course_not_found(self):
        """Test deleting a course that does not exist"""

        # Arrange
        access_token = self.get_access_token(self.teacher)
        headers = {"Authorization": f"Bearer {access_token}"}

        # Act
        response = self.client.delete("/999", headers=headers)

        # Assert
        assert response.status_code == 404
        assert response.json()["message"] == "Course with id 999 not found for the current user."


    @pytest.mark.django_db
    def test_enroll_in_course_success(self):
        """Test enrolling in a public course"""

        # Arrange
        course = Course.objects.create(name="Public Course", author=self.teacher, is_public=True)
        Module.objects.create(name="Module 1", course=course, order=1, is_visible=True)
        Lesson.objects.create(topic="Lesson 1", module=course.modules.first(), order=1)
        access_token = self.get_access_token(self.student)
        headers = {"Authorization": f"Bearer {access_token}"}

        # Act
        response = self.client.post(f"/{course.id}/enroll", headers=headers)

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == "Successfully enrolled in the course and progress initialized for the first lesson."


    @pytest.mark.django_db
    def test_enroll_in_private_course_unauthorized(self):
        """Test enrolling in a private course without authorization"""

        # Arrange
        course = Course.objects.create(name="Private Course", author=self.teacher, is_public=False)
        access_token = self.get_access_token(self.student)
        headers = {"Authorization": f"Bearer {access_token}"}

        # Act
        response = self.client.post(f"/{course.id}/enroll", headers=headers)

        # Assert
        assert response.status_code == 403
        assert response.json()["message"] == "You are not authorized to access this course."


    @pytest.mark.django_db
    def test_enroll_in_course_already_enrolled(self):
        """Test enrolling in a course the user is already enrolled in"""

        # Arrange
        course = Course.objects.create(name="Course", author=self.teacher, is_public=True)
        course.students.add(self.student)
        access_token = self.get_access_token(self.student)
        headers = {"Authorization": f"Bearer {access_token}"}

        # Act
        response = self.client.post(f"/{course.id}/enroll", headers=headers)

        # Assert
        assert response.status_code == 400
        assert response.json()["message"] == "Already enrolled in this course."


    @pytest.mark.django_db
    def test_enroll_in_non_existing_course(self):
        """Test enrolling in a course which dosn't exist"""
        
        # Arrange
        access_token = self.get_access_token(self.student)
        headers = {"Authorization": f"Bearer {access_token}"}

        # Act
        response = self.client.post(f"/1/enroll", headers=headers)

        # Assert
        assert response.status_code == 404
        assert response.json()["message"] == "No public course found with id 1."


    @pytest.mark.django_db
    def test_is_student_enrolled_success(self):
        """Test checking if a student is enrolled in a course"""

        # Arrange
        course = Course.objects.create(name="Course", author=self.teacher, is_public=True)
        course.students.add(self.student)
        access_token = self.get_access_token(self.student)
        headers = {"Authorization": f"Bearer {access_token}"}

        # Act
        response = self.client.get(f"/{course.id}/is-enrolled", headers=headers)

        # Assert
        assert response.status_code == 200
        assert response.json()["is_enrolled"] is True


    @pytest.mark.django_db
    def test_is_student_not_enrolled(self):
        """Test checking if a student is not enrolled in a course"""

        # Arrange
        course = Course.objects.create(name="Course", author=self.teacher, is_public=True)
        access_token = self.get_access_token(self.student)
        headers = {"Authorization": f"Bearer {access_token}"}

        # Act
        response = self.client.get(f"/{course.id}/is-enrolled", headers=headers)

        # Assert
        assert response.status_code == 200
        assert response.json()["is_enrolled"] is False


    @pytest.mark.django_db
    def test_rate_course_success(self):
        """Test rating a course"""

        # Arrange
        course = Course.objects.create(name="Course", author=self.teacher, is_public=True)
        course.students.add(self.student)
        access_token = self.get_access_token(self.student)
        headers = {"Authorization": f"Bearer {access_token}"}
        payload = {"score": 5}

        # Act
        response = self.client.post(f"/{course.id}/rate", json=payload, headers=headers)

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == "Course rated successfully."


    @pytest.mark.django_db
    def test_rate_course_not_enrolled(self):
        """Test rating a course by a non-enrolled user"""

        # Arrange
        course = Course.objects.create(name="Course", author=self.teacher, is_public=True)
        access_token = self.get_access_token(self.student)
        headers = {"Authorization": f"Bearer {access_token}"}
        payload = {"score": 4}

        # Act
        response = self.client.post(f"/{course.id}/rate", json=payload, headers=headers)

        # Assert
        assert response.status_code == 400
        assert response.json()["message"] == "Only enrolled users can rate this course."


    @pytest.mark.django_db
    def test_rate_course_not_found(self):
        """Test rating a non-existent course"""

        # Arrange
        access_token = self.get_access_token(self.student)
        headers = {"Authorization": f"Bearer {access_token}"}
        payload = {"score": 5}

        # Act
        response = self.client.post("/999/rate", json=payload, headers=headers)

        # Assert
        assert response.status_code == 404
        assert response.json()["message"] == "No public course found with id 999."


    @pytest.mark.django_db
    def test_update_course_success(self):
        """Test updating the entire course"""

        # Arrange
        course = Course.objects.create(name="Original Name", author=self.teacher, is_public=True)
        access_token = self.get_access_token(self.teacher)
        headers = {"Authorization": f"Bearer {access_token}"}
        payload = {
            "id": f"{course.id}",
            "name": "Updated Course",
            "description": "New description",
            "image": "new-image.jpg",
            "is_public": False,
            "creator_state": "completed",
            "modules": [
                {
                    "name": "Module 1",
                    "order": 1,
                    "is_visible": True,
                    "lessons": [
                        {
                            "topic": "Lesson 1",
                            "order": 1,
                            "introduction": {"description": "Introduction 1"},
                            "quiz": [{"question": "Q1", "answers": [{"answer": "A1", "is_correct": True}]}],
                            "assignment": {"instructions": "Assignment 1"}
                        }
                    ]
                }
            ]
        }

        # Act
        response = self.client.put(f"/{course.id}", json=payload, headers=headers)

        # Assert
        assert response.status_code == 200
        assert response.json()["name"] == payload["name"]

    
    @pytest.mark.django_db
    def test_update_non_existing_course(self):
        """Test updating non existing course"""

        # Arrange
        access_token = self.get_access_token(self.teacher)
        headers = {"Authorization": f"Bearer {access_token}"}
        payload = {
            "id": "1",
            "name": "Updated Course",
            "description": "New description",
            "image": "new-image.jpg",
            "is_public": False,
            "creator_state": "completed",
            "modules": [
                {
                    "name": "Module 1",
                    "order": 1,
                    "is_visible": True,
                    "lessons": [
                        {
                            "topic": "Lesson 1",
                            "order": 1,
                            "introduction": {"description": "Introduction 1"},
                            "quiz": [{"question": "Q1", "answers": [{"answer": "A1", "is_correct": True}]}],
                            "assignment": {"instructions": "Assignment 1"}
                        }
                    ]
                }
            ]
        }

        # Act
        response = self.client.put("/1", json=payload, headers=headers)

        # Assert
        assert response.status_code == 404


    @pytest.mark.django_db
    def test_get_general_progress_stats(self):
        """Test retrieving general progress stats"""

        # Arrange
        course = Course.objects.create(name="Course 1", author=self.teacher, is_public=True)
        Module.objects.create(name="Module 1", course=course, order=1, is_visible=True)
        Lesson.objects.create(topic="Lesson 1", module=course.modules.first(), order=1)
        StudentProgress.objects.create(user=self.student, lesson=Lesson.objects.first(), lesson_completed=True)
        access_token = self.get_access_token(self.teacher)
        headers = {"Authorization": f"Bearer {access_token}"}

        # Act
        response = self.client.get("/progress/general", headers=headers)

        # Assert
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert "username" in response.json()[0]


    @pytest.mark.django_db
    def test_get_progress_in_enrolled_courses(self):
        """Test retrieving progress in courses the user is enrolled in"""

        # Arrange
        course = Course.objects.create(name="Course", author=self.teacher, is_public=True)
        module = Module.objects.create(name="Module 1", course=course, order=1, is_visible=True)
        lesson = Lesson.objects.create(topic="Lesson 1", module=module, order=1)
        course.students.add(self.student)
        StudentProgress.objects.create(user=self.student, lesson=lesson, lesson_completed=True)
        access_token = self.get_access_token(self.student)
        headers = {"Authorization": f"Bearer {access_token}"}

        # Act
        response = self.client.get("/progress/enrolled", headers=headers)

        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["course_name"] == "Course"


    @pytest.mark.django_db
    def test_get_teacher_course_progress(self):
        """Test retrieving progress stats for teacher's courses"""

        # Arrange
        course = Course.objects.create(name="Course", author=self.teacher, is_public=True)
        module = Module.objects.create(name="Module 1", course=course, order=1, is_visible=True)
        lesson = Lesson.objects.create(topic="Lesson 1", module=module, order=1)
        StudentProgress.objects.create(user=self.student, lesson=lesson, lesson_completed=True)
        access_token = self.get_access_token(self.teacher)
        headers = {"Authorization": f"Bearer {access_token}"}

        # Act
        response = self.client.get("/teacher/progress", headers=headers)

        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["course_name"] == "Course"


    @pytest.mark.django_db
    def test_get_course_progress_stats_success(self):
        """Test retrieving progress stats for a specific course"""

        # Arrange
        course = Course.objects.create(name="Course", author=self.teacher, is_public=True)
        module = Module.objects.create(name="Module 1", course=course, order=1, is_visible=True)
        lesson = Lesson.objects.create(topic="Lesson 1", module=module, order=1)
        StudentProgress.objects.create(user=self.student, lesson=lesson, lesson_completed=True)
        access_token = self.get_access_token(self.teacher)
        headers = {"Authorization": f"Bearer {access_token}"}

        # Act
        response = self.client.get(f"/{course.id}/progress", headers=headers)

        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["username"] == self.student.username


    @pytest.mark.django_db
    def test_get_course_progress_stats_no_lessons(self):
        """Test retrieving progress stats when no lessons exist for the course"""

        # Arrange
        course = Course.objects.create(name="Course", author=self.teacher, is_public=True)
        access_token = self.get_access_token(self.teacher)
        headers = {"Authorization": f"Bearer {access_token}"}

        # Act
        response = self.client.get(f"/{course.id}/progress", headers=headers)

        # Assert
        assert response.status_code == 404
        assert response.json()["message"] == f"No lessons found for course {course.id}."


    @pytest.mark.django_db
    def test_generate_modules_success(self):
        """Test module generation for a course"""

        # Arrange
        course_name = "Programming Basics"
        course_description = "Learn the basics of programming with hands-on exercises."
        language = "Polish"

        # Act
        modules = generate_modules(course_name, course_description, language)

        # Assert
        assert len(modules) == 3
        for module in modules:
            assert module.name