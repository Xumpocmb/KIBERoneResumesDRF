from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import TutorProfile


class RegisterTutorViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse("tutor-register")

    def test_register_tutor_success(self):
        """
        Тест успешной регистрации преподавателя
        """
        data = {"phone_number": "375 44 712 3218", "tutor_branch_id": 1}

        response = self.client.post(self.register_url, data, format="json")

        # Проверяем, что статус ответа 201 (Created)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Проверяем, что преподаватель был создан в базе данных
        self.assertEqual(TutorProfile.objects.count(), 1)

        tutor = TutorProfile.objects.first()
        # Since phone number is cleaned in the serializer, compare with the cleaned version
        cleaned_phone = "".join(filter(str.isdigit, data["phone_number"]))
        self.assertEqual(tutor.phone_number, cleaned_phone)
        # Convert both values to string for comparison since branch might be stored as string
        self.assertEqual(str(tutor.branch), str(data["tutor_branch_id"]))

    def test_register_tutor_duplicate_phone(self):
        """
        Тест регистрации преподавателя с уже существующим номером телефона
        """
        # Сначала регистрируем преподавателя
        data = {"phone_number": "375 44 712 3218", "tutor_branch_id": 1}

        # Первый запрос должен быть успешным
        first_response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)

        # Второй запрос с тем же номером должен вернуть ошибку
        second_response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(second_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(second_response.data["detail"], "Phone number already registered")

    def test_register_tutor_invalid_data(self):
        """
        Тест регистрации преподавателя с невалидными данными
        """
        # Пропускаем обязательные поля
        data = {
            "phone_number": "375 44 712 3218"
            # tutor_branch_id отсутствует
        }

        response = self.client.post(self.register_url, data, format="json")

        # Проверяем, что статус ответа 400 (Bad Request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_tutor_missing_fields(self):
        """
        Тест регистрации преподавателя с отсутствующими полями
        """
        # Отправляем пустой запрос
        data = {}

        response = self.client.post(self.register_url, data, format="json")

        # Проверяем, что статус ответа 400 (Bad Request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginTutorViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.login_url = reverse("tutor-login")
        self.register_url = reverse("tutor-register")

        # Register a tutor for login tests
        register_data = {"phone_number": "375447123218", "tutor_branch_id": 1}
        self.client.post(self.register_url, register_data, format="json")

    def test_login_tutor_success(self):
        """
        Тест успешной авторизации преподавателя
        """
        data = {"phone_number": "375 44 712 3218"}  # Phone number with spaces should be cleaned

        response = self.client.post(self.login_url, data, format="json")

        # Проверяем, что статус ответа 200 (OK)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем, что в ответе есть токен
        self.assertIn("access_token", response.data)
        self.assertIn("token_type", response.data)
        self.assertEqual(response.data["token_type"], "bearer")

    def test_login_tutor_invalid_phone(self):
        """
        Тест авторизации преподавателя с неверным номером телефона
        """
        data = {"phone_number": "375447123219"}  # Non-existent phone number

        response = self.client.post(self.login_url, data, format="json")

        # Проверяем, что статус ответа 401 (Unauthorized)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["detail"], "Incorrect phone number")

    def test_login_tutor_invalid_data(self):
        """
        Тест авторизации преподавателя с невалидными данными
        """
        data = {"phone_number": ""}  # Empty phone number

        response = self.client.post(self.login_url, data, format="json")

        # Проверяем, что статус ответа 400 (Bad Request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TutorGroupsViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse("tutor-register")
        self.login_url = reverse("tutor-login")
        self.groups_url = reverse("tutor-groups")

        # Register and login a tutor for groups tests
        register_data = {"phone_number": "375447123218", "tutor_branch_id": 1}
        self.client.post(self.register_url, register_data, format="json")

        login_data = {"phone_number": "375 44 712 3218"}
        login_response = self.client.post(self.login_url, login_data, format="json")

        # Set authorization header for subsequent requests
        self.token = login_response.data["access_token"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

    def test_get_tutor_groups_success(self):
        """
        Тест получения групп преподавателя
        """
        response = self.client.get(self.groups_url)

        # Проверяем, что статус ответа 200 (OK)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем, что в ответе есть список групп (даже если пустой)
        # В зависимости от структуры ответа, проверяем наличие ключа 'groups' или проверяем тип данных
        if isinstance(response.data, dict):
            self.assertIn("groups", response.data)
        else:
            self.assertIsInstance(response.data, list)

    def test_get_tutor_groups_without_auth(self):
        """
        Тест получения групп преподавателя без аутентификации
        """
        # Сбрасываем авторизационный заголовок
        self.client.credentials()

        response = self.client.get(self.groups_url)

        # Проверяем, что статус ответа 401 (Unauthorized)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["detail"], "Authentication required")

    def test_login_tutor_missing_fields(self):
        """
        Тест авторизации преподавателя с отсутствующими полями
        """
        # Отправляем пустой запрос
        data = {}

        response = self.client.post(self.login_url, data, format="json")

        # Проверяем, что статус ответа 400 (Bad Request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
