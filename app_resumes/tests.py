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
        self.assertEqual(tutor.phone_number, data["phone_number"])
        self.assertEqual(tutor.branch, data["tutor_branch_id"])

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
