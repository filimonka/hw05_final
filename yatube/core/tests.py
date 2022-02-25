from http import HTTPStatus

from django.test import TestCase, Client
from django.contrib.auth import get_user_model


User = get_user_model()


class TestUrlCore(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='TheAuthor')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.guest_client = Client()

    def test_unexisting_page(self):
        """Ответ для несуществующей страницы."""
        users = (
            self.authorized_client,
            self.guest_client,
        )
        for user in users:
            with self.subTest(user=user):
                self.assertEqual(
                    user.get('/unexisting_page/').status_code,
                    HTTPStatus.NOT_FOUND,
                )

    def test_template_unexisting(self):
        """Для несуществующей страницы использован правильный шаблон."""
        self.assertTemplateUsed(
            self.authorized_client.get('/unexisting_page/'),
            'core/404.html'
        )
