from django.test import TestCase
from ninja_extra.testing import TestClient
from ninja_jwt.tokens import RefreshToken
import pytest
from .api import router
from .models import User


class NinjaAuthenticationTestCase(TestCase):
    def setUp(self):
        self.client = TestClient(router)

        self.user = User.objects.create_user(username='JohnDoe123', email='johndoe@gmail.com', password='JohnDoe@!3', role='USER')
        self.user2 = User.objects.create_user(username='BobJohnson123', email='bobjohnson@gmail.com', password='BobJohnson#23', role='TEACHER')


    def get_access_token(self):
        """Helper function to get JWT token for the test user"""

        refresh = RefreshToken.for_user(self.user)
        return str(refresh.access_token)

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


    @pytest.mark.dajngo_db
    def test_get_user_success(self):
        """Test that an authenticated user can get their data"""

        # Arrange
        token = self.get_access_token()

        # Act
        response = self.client.get('/user', headers={'Authorization': f'Bearer {token}'})

        # Assert
        assert response.status_code == 200
        assert response.json()['username'] == 'JohnDoe123'
        assert response.json()['email'] == 'johndoe@gmail.com'
        assert response.json()['role'] == 'USER'


    @pytest.mark.dajngo_db
    def test_get_user_without_token(self):
        """Test user get their data without token"""

        # Arrange

        # Act
        response = self.client.get('/user')

        # Assert
        assert response.status_code == 401
        assert response.json()['detail'] == 'Unauthorized'


    @pytest.mark.dajngo_db
    def test_update_user_success(self):
        """Test that an authenticated user can update their data"""

        # Arrange
        token = self.get_access_token()
        payload = {
            'username': 'JohnDoe99',
            'email': 'johndoe99@gmail.com'
        }

        # Act
        response = self.client.patch('/user', json=payload, headers={'Authorization': f'Bearer {token}'})

        # Assert
        assert response.status_code == 200
        assert response.json()['username'] == 'JohnDoe99'
        assert response.json()['email'] == 'johndoe99@gmail.com'


    @pytest.mark.dajngo_db
    def test_update_user_without_token(self):
        """Test user update their data without token"""

        # Arrange
        payload = {
            'username': 'JohnDoe99',
            'email': 'johndoe99@gmail.com'
        }

        # Act
        response = self.client.patch('/user', json=payload)

        # Assert
        assert response.status_code == 401
        assert response.json()['detail'] == 'Unauthorized'


    @pytest.mark.dajngo_db
    def test_update_user_with_duplicate_username(self):
        """Test user update their data with duplicate username"""

        # Arrange
        token = self.get_access_token()
        payload = {
            'username': 'BobJohnson123'
        }

        # Act
        response = self.client.patch('/user', json=payload, headers={'Authorization': f'Bearer {token}'})

        # Assert
        assert response.status_code == 400
        assert response.json()['message'] == 'Username is already taken.'


    @pytest.mark.dajngo_db
    def test_update_user_with_duplicate_email(self):
        """Test user update their data with duplicate email"""

        # Arrange
        token = self.get_access_token()
        payload = {
            'email': 'bobjohnson@gmail.com'
        }

        # Act
        response = self.client.patch('/user', json=payload, headers={'Authorization': f'Bearer {token}'})

        # Assert
        assert response.status_code == 400
        assert response.json()['message'] == 'Email is already taken.'


    @pytest.mark.dajngo_db
    def test_change_password_success(self):
        """Test user change password with vaild data"""

        # Arrange
        token = self.get_access_token()
        payload = {
            "old_password": "JohnDoe@!3",
            "new_password": "JohnDoe@$5",
            "confirm_password": "JohnDoe@$5"
        }

        # Act
        response = self.client.post('/user/change-password', json=payload, headers={'Authorization': f'Bearer {token}'})

        # Assert
        assert response.status_code == 200
        assert response.json()['message'] == 'Password changed successfully.'


    @pytest.mark.dajngo_db
    def test_change_password_with_wrong_old_password(self):
        """Test user change password with wrong old password"""

        # Arrange
        token = self.get_access_token()
        payload = {
            "old_password": "JohnDoe@!123",
            "new_password": "JohnDoe@$5",
            "confirm_password": "JohnDoe@$5"
        }

        # Act
        response = self.client.post('/user/change-password', json=payload, headers={'Authorization': f'Bearer {token}'})

        # Assert
        assert response.status_code == 400
        assert response.json()['message'] == 'Old password incorrect.'


    @pytest.mark.dajngo_db
    def test_change_password_with_mismatched_passwords(self):
        """Test user change password when the new passwords do not match"""

        # Arrange
        token = self.get_access_token()
        payload = {
            "old_password": "JohnDoe@!3",
            "new_password": "JohnDoe@$1234",
            "confirm_password": "JohnDoe@$5"
        }

        # Act
        response = self.client.post('/user/change-password', json=payload, headers={'Authorization': f'Bearer {token}'})

        # Assert
        assert response.status_code == 400
        assert response.json()['message'] == 'New passwords do not match.'