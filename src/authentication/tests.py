from django.test import TestCase
from ninja_extra.testing import TestClient
import pytest
from .api import router
from .models import User


class NinjaAuthenticationTestCase(TestCase):
    def setUp(self):
        self.client = TestClient(router)

        self.user = User.objects.create_user(username='JohnDoe123', email='johndoe@gmail.com', password='JohnDoe@!3')


    @pytest.mark.django_db
    def test_login_success(self):
        """Test login with correct user credentials"""

        # Arrange
        payload = {
            'email': 'johndoe@gmail.com',
            'password': 'JohnDoe@!3'
        }

        # Act
        response = self.client.post('/login', json=payload)

        # Assert
        assert response.status_code == 200
        assert 'access' in response.json()
        assert 'refresh' in response.json()


    @pytest.mark.django_db
    def test_login_invalid_emial(self):
        """Test login with invalid email"""

        # Arrange
        payload = {
            'email': 'johndoe@gmail.pl',
            'password': 'JohnDoe@!3'
        }

        # Act
        response = self.client.post('/login', json=payload)

        # Assert
        assert response.status_code == 401
        assert response.json()['message'] == 'Invalid email or password'


    @pytest.mark.django_db
    def test_login_invalid_password(self):
        """Test login with invalid password"""

        # Arrange
        payload = {
            'email': 'johndoe@gmail.com',
            'password': 'JohnDoe#$2'
        }

        # Act
        response = self.client.post('/login', json=payload)

        # Assert
        assert response.status_code == 401
        assert response.json()['message'] == 'Invalid email or password'


    @pytest.mark.django_db
    def test_register_success(self):
        """Test register with correct credentials"""

        # Arrange
        payload = {
            'username': 'AliceSmith21',
            'email': 'alicesmith21@gmail.com',
            'password': 'Alice123$',
            'role': 'TEACHER'
        }

        # Act
        response = self.client.post('/register', json=payload)

        # Assert
        assert response.status_code == 201
        assert response.json()['username'] == 'AliceSmith21'
        assert response.json()['email'] == 'alicesmith21@gmail.com'
        assert response.json()['role'] == 'TEACHER'


    @pytest.mark.django_db
    def test_register_with_duplicate_email(self):
        """Test register with already used email"""

        # Arrange
        payload = {
            'username': 'JohnDoe1234',
            'email': 'johndoe@gmail.com',
            'password': 'Alice123$',
            'role': 'USER'
        }

        # Act
        response = self.client.post('/register', json=payload)

        # Assert
        assert response.status_code == 400
        assert response.json()['message'] == 'Email is already registered.'


    @pytest.mark.django_db
    def test_register_with_duplicate_username(self):
        """Test register with already used username"""

        # Arrange
        payload = {
            'username': 'JohnDoe123',
            'email': 'johndoe123@gmail.com',
            'password': 'Alice123$',
            'role': 'USER'
        }

        # Act
        response = self.client.post('/register', json=payload)

        # Assert
        assert response.status_code == 400
        assert response.json()['message'] == 'Username is already registered.'


    @pytest.mark.django_db
    def test_register_invalid_email_missing_at_sign(self):
        """Test register with missing @-sign in the email address"""

        # Arrange
        payload = {
            'username': 'AliceSmith21',
            'email': 'alicesmith21gmail.com',
            'password': 'Alice123$',
            'role': 'TEACHER'
        }

        # Act
        response = self.client.post('/register', json=payload)

        # Assert
        assert response.status_code == 422
        assert response.json()['detail'][0]['msg'] == 'value is not a valid email address: An email address must have an @-sign.'


    @pytest.mark.django_db
    def test_register_invalid_email_missing_period_in_domain(self):
        """Test register with missing period in the email domain"""

        # Arrange
        payload = {
            'username': 'AliceSmith21',
            'email': 'alicesmith21@gmailcom',
            'password': 'Alice123$',
            'role': 'TEACHER'
        }

        # Act
        response = self.client.post('/register', json=payload)

        # Assert
        assert response.status_code == 422
        assert response.json()['detail'][0]['msg'] == 'value is not a valid email address: The part after the @-sign is not valid. It should have a period.'


    @pytest.mark.django_db
    def test_register_invalid_password_missing_uppercase_letter(self):
        """Test register with missing uppercase letter in password"""

        # Arrange
        payload = {
            'username': 'AliceSmith21',
            'email': 'alicesmith21@gmail.com',
            'password': 'alice123$',
            'role': 'TEACHER'
        }

        # Act
        response = self.client.post('/register', json=payload)

        # Assert
        assert response.status_code == 422
        assert response.json()['detail'][0]['msg'] == 'Value error, Password must contain at least one uppercase letter.'


    @pytest.mark.django_db
    def test_register_invalid_password_missing_lowercase_letter(self):
        """Test register with missing uppercase letter in password"""

        # Arrange
        payload = {
            'username': 'AliceSmith21',
            'email': 'alicesmith21@gmail.com',
            'password': 'alice123$',
            'role': 'TEACHER'
        }

        # Act
        response = self.client.post('/register', json=payload)

        # Assert
        assert response.status_code == 422
        assert response.json()['detail'][0]['msg'] == 'Value error, Password must contain at least one uppercase letter.'


    @pytest.mark.django_db
    def test_register_invalid_password_missing_digit(self):
        """Test register with missing digit in password"""

        # Arrange
        payload = {
            'username': 'AliceSmith21',
            'email': 'alicesmith21@gmail.com',
            'password': 'AliceABC$',
            'role': 'TEACHER'
        }

        # Act
        response = self.client.post('/register', json=payload)

        # Assert
        assert response.status_code == 422
        assert response.json()['detail'][0]['msg'] == 'Value error, Password must contain at least one digit.'


    @pytest.mark.django_db
    def test_register_invalid_password_missing_special_character(self):
        """Test register with missing special character in password"""

        # Arrange
        payload = {
            'username': 'AliceSmith21',
            'email': 'alicesmith21@gmail.com',
            'password': 'Alice1234',
            'role': 'TEACHER'
        }

        # Act
        response = self.client.post('/register', json=payload)

        # Assert
        assert response.status_code == 422
        assert response.json()['detail'][0]['msg'] == 'Value error, Password must contain at least one special character.'


    @pytest.mark.django_db
    def test_register_invalid_password_too_short(self):
        """Test register with too short password"""

        # Arrange
        payload = {
            'username': 'AliceSmith21',
            'email': 'alicesmith21@gmail.com',
            'password': 'Alice1$',
            'role': 'TEACHER'
        }

        # Act
        response = self.client.post('/register', json=payload)

        # Assert
        assert response.status_code == 422
        assert response.json()['detail'][0]['msg'] == "String should have at least 8 characters"


    @pytest.mark.django_db
    def test_register_invalid_role(self):
        """Test register with incorect role"""

        # Arrange
        payload = {
            'username': 'AliceSmith21',
            'email': 'alicesmith21@gmail.com',
            'password': 'Alice123$',
            'role': 'SECRETARY'
        }

        # Act
        response = self.client.post('/register', json=payload)

        # Assert
        assert response.status_code == 422
        assert response.json()['detail'][0]['msg'] == "Value error, Invalid role: " + payload['role']