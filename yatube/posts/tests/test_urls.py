from http import HTTPStatus

from django.test import TestCase, Client
from django.urls import reverse

from ..models import Group, Post, User


class TestUrlResponse(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Буратино')
        cls.group = Group.objects.create(
            title='Алиса и Додо',
            slug='test',
            description='Глокая куздра боднула кузявку',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Крекс, пекс, фекс',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(TestUrlResponse.user)
        self.not_author_user = User.objects.create_user(username='Lewis')
        self.not_author = Client()
        self.not_author.force_login(self.not_author_user)

    def test_common_urls(self):
        """Статус ответа URL общедоступных страниц."""
        urls = (
            reverse('posts:index'),
            reverse(
                'posts:group_list',
                kwargs={'slug': TestUrlResponse.group.slug}
            ),
            reverse(
                'posts:profile',
                kwargs={'username': TestUrlResponse.user.username}
            ),
            reverse(
                'posts:post_detail',
                kwargs={'post_id': TestUrlResponse.post.id}
            ),
        )
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(
                    self.guest_client.get(url).status_code,
                    HTTPStatus.OK,
                )

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

    def test_create_post(self):
        """Create_post доступен авторизованному пользователю."""
        self.assertEqual(
            self.authorized_client.get(
                reverse('posts:post_create')
            ).status_code,
            HTTPStatus.OK,
        )

    def test_create_post_redirect(self):
        """Redirect  для create_post работает правильно."""
        self.assertRedirects(
            self.guest_client.get(
                reverse('posts:post_create')
            ),
            '/auth/login/?next=/create/',
        )
        self.assertRedirects(
            self.authorized_client.post(
                reverse('posts:post_create'),
                data={
                    'text': 'Сейчас мы их проверим'
                }
            ),
            reverse(
                'posts:profile',
                kwargs={'username': TestUrlResponse.user.username}
            )
        )

    def test_post_edit(self):
        """Редактирование доступно автору."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': TestUrlResponse.post.id}
            )
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_not_author(self):
        """Неавтору недоступно редактирование,
        redirect выполняется правильно."""
        clients = (
            self.guest_client,
            self.not_author,
        )
        edit_page = reverse(
            'posts:post_edit',
            kwargs={'post_id': TestUrlResponse.post.id}
        )
        redirect_page = reverse(
            'posts:post_detail',
            kwargs={'post_id': TestUrlResponse.post.id}
        )
        for client in clients:
            with self.subTest(client=client):
                self.assertRedirects(
                    client.get(edit_page),
                    redirect_page
                )

    def test_comment_authorized(self):
        """Авторизованный пользователь может комментировать."""
        post_comment = reverse(
            'posts:add_comment',
            kwargs={'post_id': TestUrlResponse.post.id}
        )
        post_detail = reverse(
            'posts:post_detail',
            kwargs={'post_id': TestUrlResponse.post.id}
        )
        response = self.authorized_client.post(
            post_comment,
            data={'text': 'Несите ваши денежки'},
            follow=True
        )
        self.assertRedirects(
            response,
            post_detail,
        )

    def test_comment_anauthorized(self):
        """Неавторизованному пользователю недоступны комментарии,
        он перенаправлен на страницу авторизации."""
        post_comment = reverse(
            'posts:add_comment',
            kwargs={'post_id': TestUrlResponse.post.id}
        )
        self.assertRedirects(
            self.guest_client.get(post_comment),
            f'/auth/login/?next=/posts/{TestUrlResponse.post.id}/comment/',
        )
