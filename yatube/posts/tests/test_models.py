from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='MrCarroll')
        cls.group = Group.objects.create(
            title='Алиса и Додо',
            slug='test',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Глокая куздра боднула кузявку',
        )

    def test_models_have_correct_str_method(self):
        """__str__ моделей корректно работает корректно."""
        models = {
            'Алиса и Додо': str(PostModelTest.group),
            'Глокая куздра б': str(PostModelTest.post),
        }
        for expected_value, model in models.items():
            with self.subTest():
                self.assertEqual(model, expected_value)
