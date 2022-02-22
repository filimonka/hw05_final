import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.test import Client, TestCase, override_settings

from ..forms import PostForm
from ..models import Post, Group, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.form = PostForm()
        cls.user = User.objects.create_user(username='Буратино')
        cls.group = Group.objects.create(
            title='Дуремар',
            slug='duremar',
            description='Всё о пиявках.',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Три корочки хлеба',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(user=PostCreateFormTest.user)
        self.guest_client = Client()

    def test_post_created(self):
        """Новый пост создается правильно."""
        posts_count = Post.objects.count()
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
        form_data = {
            'text': 'Крекс, фекс, пекс',
            'group': PostCreateFormTest.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        last_post = Post.objects.first()
        context = {
            last_post.author.username: 'Буратино',
            last_post.text: 'Крекс, фекс, пекс',
            last_post.group.id: PostCreateFormTest.group.id,
            last_post.image: 'posts/temp.gif',
            Post.objects.count(): posts_count + 1,
        }
        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                kwargs={
                    'username': PostCreateFormTest.user.username
                }
            )
        )
        for expected, value in context.items():
            with self.subTest():
                self.assertEqual(expected, value)

    def test_post_edited(self):
        """Пост редактируется правильно."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'В стране дураков',
            'group': PostCreateFormTest.group.id,
        }
        response = self.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostCreateFormTest.post.id},
            ),
            data=form_data,
            follow=True,
        )
        db_post = Post.objects.get(pk=PostCreateFormTest.post.id)
        context = {
            posts_count: Post.objects.count(),
            db_post.author.username: 'Буратино',
            db_post.text: 'В стране дураков',
            db_post.group.id: PostCreateFormTest.group.id,
        }
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={
                    'post_id': PostCreateFormTest.post.id
                }
            )
        )
        for value, expected in context.items():
            with self.subTest():
                self.assertEqual(value, expected)

    def test_comment_creation(self):
        """Комментарий создается правильно."""
        data = {
            'text': 'Пилите, Шура, она золотая!'
        }
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': PostCreateFormTest.post.id}
            ),
            data=data,
            follow=True
        )
        comment = response.context['comments']
        context = {
            comment[0].text: 'Пилите, Шура, она золотая!',
            len(comment): PostCreateFormTest.post.comments.count(),
            comment[0].author: PostCreateFormTest.user,
        }
        for value, expected in context.items():
            with self.subTest():
                self.assertEqual(value, expected)
