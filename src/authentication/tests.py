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
        """ Test login with correct user credentials """

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
        """ Test login with invalid email """

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
        """ Test login with invalid password """

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


