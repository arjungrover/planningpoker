import json
import uuid
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from user.models import UserInfo


class SignUpViewTest(TestCase):
    def setUp(self):
        self.user1 = {
            'email': 'lambaa447@gmail.com',
            'first_name': 'sdfg',
            'last_name': 'dfhj',
            'password': 'asdfghjkl'
        }
        self.user2 = {
            'email': 'lambaa447@gmail.com',
            'first_name': 'sdfg',
            'last_name': 'dfhj'
        }

    def test_create_user(self):
        client = APIClient()
        url = reverse('signup-list')
        response = client.post(url, self.user1, format='json')
        self.assertEqual(response.status_code, 201)

    def test_invalid_user(self):
        client = APIClient()
        url = reverse('signup-list')
        response = client.post(url, self.user2, format='json')
        msg = {"password": ["This field is required."]}
        self.assertEqual(json.loads(response.content), msg)
        self.assertEqual(response.status_code, 400)


class EmailVerifyViewTest(TestCase):
    def setUp(self):
        self.user = UserInfo.objects.create_user(
            'abhi@gmail.com', 'abhi', 'lamba')
        self.user.set_password('asdfghjkl')
        emailtoken = uuid.uuid4()
        self.user.email_token = emailtoken
        self.user.save()

    def test_valid_token(self):
        url = reverse('verify')
        url = url + '?token=' + str(self.user.email_token)
        client = APIClient()
        response = client.get(url)
        msg = {'message': 'Verified Success'}
        self.assertEqual(json.loads(response.content), msg)
        self.assertEqual(response.status_code, 200)

    def test_invalid_token(self):
        url = reverse('verify')
        url = url + '?token=' + "p"
        client = APIClient()
        response = client.get(url)
        msg = {'error': 'Invalid Key!'}
        self.assertEqual(json.loads(response.content), msg)
        self.assertEqual(response.status_code, 404)


class LoginViewTest(TestCase):
    def setUp(self):
        self.user3 = {
            'email': 'abhi@gmail.com',
            'password': 'asdfghjkl'
        }

    def test_user_login(self):
        user = UserInfo.objects.create_user('abhi@gmail.com', 'abhi', 'lamba')
        user.set_password('asdfghjkl')
        emailtoken = uuid.uuid4()
        user.email_token = emailtoken
        user.save()
        url = reverse('verify')
        url = url + '?token=' + str(user.email_token)
        client = APIClient()
        response = client.get(url)
        url = reverse('login')
        response1 = client.post(url, self.user3, format='json')
        self.assertEqual(response.status_code, 200)
