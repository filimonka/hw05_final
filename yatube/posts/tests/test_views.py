import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django import forms
from django.test import TestCase, Client, override_settings
from django.core.cache import cache

from ..models import Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class TestTemplateCorrect(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Buratino')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test',
            description='Тествое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Не доведёт тебя до добра это ученье...',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(TestTemplateCorrect.user)
        cache.clear()

    def test_template_is_correct(self):
        """Проверяем соответствие шаблонов адресам."""
        template_urls = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': TestTemplateCorrect.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': TestTemplateCorrect.user.username}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': TestTemplateCorrect.post.id}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_create'
            ): 'posts/create_post.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': TestTemplateCorrect.post.id}
            ): 'posts/create_post.html',
            reverse(
                'posts:follow_index'
            ):
            'posts/follow.html',
        }
        for url, template in template_urls.items():
            response = self.authorized_client.get(url)
            with self.subTest(response=response):
                self.assertTemplateUsed(
                    response,
                    template,
                    f'Для адреса {url} ожидался шаблон {template}')


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ContextCheck(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        temp_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='temp.gif',
            content=temp_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Test group',
            slug='test',
            description='Test description',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Всё чудесатее и чудесатее',
            group=cls.group,
            image=uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(ContextCheck.user)
        cache.clear()

    def help_context(self, post) -> dict:
        return {
            post.author: ContextCheck.user,
            post.text: 'Всё чудесатее и чудесатее',
            post.group: ContextCheck.group,
            post.author.posts.count(): 1,
            post.image: 'posts/temp.gif'
        }

    def test_index_context(self):
        """Словарь контекста главной страницы."""
        response = self.authorized_client.get(
            reverse('posts:index')
        )
        post = response.context['page_obj'][0]
        context = self.help_context(post)
        for expected, value in context.items():
            with self.subTest():
                self.assertEqual(expected, value)

    def test_group_context(self):
        """Контекст страницы группы"""
        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': ContextCheck.group.slug}
            )
        )
        post = response.context['page_obj'][0]
        context = self.help_context(post)
        for expected, value in context.items():
            with self.subTest():
                self.assertEqual(
                    expected,
                    value,
                    f'{expected} не соответствует ожиданиям'
                )

    def test_profile_page_context(self):
        """Контекст страницы пользователя."""
        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': ContextCheck.group.slug}
            )
        )
        post = response.context['page_obj'][0]
        context = self.help_context(post)
        for expected, value in context.items():
            with self.subTest():
                self.assertEqual(expected, value)

    def test_post_detail(self):
        """Один пост, отфильтрованный по id."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': ContextCheck.post.id}
            )
        )
        post = response.context['post']
        context = self.help_context(post)
        for expected, value in context.items():
            with self.subTest():
                self.assertEqual(expected, value)

    def test_create_post_shows_correct_form(self):
        """В форму создания нового поста передается правильный шаблон."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField
        }
        for value, expected in form_fields.items():
            with self.subTest():
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        self.assertFalse(response.context.get('is_edit'))

    def test_post_edit_shows_correct_fields(self):
        """В форму редактирования поста передан правильный шаблон."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': ContextCheck.post.id}
            )
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest():
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        self.assertTrue(response.context.get('is_edit'))


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test',
            description='Тествое описание',
        )
        cls.posts = [
            Post(
                author=cls.user,
                text=f'I hate bulk_create for {number}',
                group=cls.group
            ) for number in range(1, 14)
        ]
        Post.objects.bulk_create(cls.posts)

    def setUp(self):
        self.client = Client()
        cache.clear()

    def test_paginator(self):
        """Проверяем Paginator."""
        pages = (
            reverse('posts:index'),
            reverse(
                'posts:group_list',
                kwargs={'slug': PaginatorViewsTest.group.slug}
            ),
            reverse(
                'posts:profile',
                kwargs={'username': PaginatorViewsTest.user}
            ),
        )
        number = {
            1: 10,
            2: 3,
        }
        for number, quantity in number.items():
            for page in pages:
                response = self.client.get(page, {'page': number})
                with self.subTest(response=response):
                    self.assertEqual(
                        len(response.context['page_obj']),
                        quantity,
                        f'Paginator для стр. {number} работает неправильно.'
                    )

    def test_cache(self):
        """Проверяем, что главная страница кэшируется."""
        page = (reverse('posts:index'), {'page': 2})
        posts_to_show = self.client.get(
            *page).content.decode('utf-8').count('<article>')
        Post.objects.last().delete()
        posts_shows = self.client.get(
            *page).content.decode('utf-8').count('<article>')
        self.assertEqual(posts_shows, posts_to_show)

    def test_unchached(self):
        """Проверяем, что после сброса кэша страница работает правильно."""
        page = (reverse('posts:index'), {'page': 2})
        posts_to_show = self.client.get(*page).content.decode(
            'utf-8').count('<article>')
        Post.objects.last().delete()
        cache.clear()
        posts_shows = self.client.get(*page).content.decode(
            'utf-8').count('<article>')
        self.assertEqual(posts_to_show - 1, posts_shows)


class NewPostCreationCheck(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test',
            description='Тестовое описание группы',
        )
        cls.other_group = Group.objects.create(
            title='Другая тестовая группа',
            slug='other_test',
            description='Тестовое описание другой группы',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Фрекс, пекс, кекс',
            group=NewPostCreationCheck.group
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(NewPostCreationCheck.user)
        self.user = User.objects.create_user(username='Muzzy')
        self.muzzy = Client()
        self.muzzy.force_login(self.user)
        self.fm = User.objects.create_user(username='Достоевский')
        self.client_fm = Client()
        self.client_fm.force_login(self.fm)
        cache.clear()

    def test_group_post(self):
        """Пост с группой виден на правильных страницах."""
        paths = (
            reverse('posts:index'),
            reverse(
                'posts:group_list',
                kwargs={'slug': NewPostCreationCheck.group.slug}
            ),
            reverse(
                'posts:profile',
                kwargs={'username': NewPostCreationCheck.user.username}
            ),
        )
        for path in paths:
            response = self.authorized_client.get(path)
            post = response.context['page_obj'][0]
            self.assertEqual(
                post.group,
                NewPostCreationCheck.group,
                f'Пост не виден на странице {path}'
            )
        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={
                    'slug': NewPostCreationCheck.other_group.slug
                }
            )
        )
        self.assertEqual(
            len(response.context['page_obj']),
            0,
            'Пост виден на странице группы, которой он не принадлежит'
        )

    def test_comment_is_seen(self):
        """Коммент появился на странице поста."""
        post_page = reverse(
            'posts:add_comment',
            kwargs={'post_id': NewPostCreationCheck.post.id}
        )
        response = self.authorized_client.post(
            post_page,
            data={'text': 'Пилите, Шура, она золотая!'},
            follow=True
        )
        comment = response.context['comments']
        context = {
            comment[0].text: 'Пилите, Шура, она золотая!',
            len(comment): 1,
        }
        for value, expected in context.items():
            with self.subTest(value=value):
                self.assertEqual(value, expected)

    def test_authorized_client_can_subscribe(self):
        """Авторизованный пользователь может подписаться на автора
        и отписаться от него."""
        subscriptions_count = self.fm.follower.count()
        self.client_fm.get(
            reverse('posts:profile_follow', kwargs={'username': 'Muzzy'})
        )
        self.assertEqual(self.fm.follower.count(), subscriptions_count + 1)
        self.client_fm.get(
            reverse('posts:profile_unfollow', kwargs={'username': 'Muzzy'})
        )
        self.assertEqual(self.fm.follower.count(), subscriptions_count)

    def test_new_post_subscribed(self):
        """Новый пост виден подписчику и не виден другому пользователю."""
        self.muzzy.get(
            reverse('posts:profile_follow', kwargs={'username': 'Достоевский'})
        )
        new_post = Post.objects.create(
            author=self.fm,
            text='Молчать - большой талант.'
        )
        seen = self.muzzy.get(reverse('posts:follow_index'))
        unseen = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(
            seen.context['page_obj'][0].text,
            new_post.text
        )
        self.assertEqual(
            len(unseen.context['page_obj']),
            0
        )
