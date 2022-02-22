from http import HTTPStatus

from django.test import TestCase, Client
from django.urls import reverse


class TestStaticUrls(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_static_urls_respond_correctly(self):
        """Об авторе и Технологии доступны."""
        static_list = [
            reverse('about:author'),
            reverse('about:tech'),
        ]
        for adress in static_list:
            response = self.guest_client.get(adress)
            with self.subTest(response=response):
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    f'Не работает {adress}')
