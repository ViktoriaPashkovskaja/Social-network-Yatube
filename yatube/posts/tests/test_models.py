from django.test import TestCase
from django.contrib.auth import get_user_model
from ..models import Group, Post

User = get_user_model()


class PostGroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='Anonim')
        cls.group = Group.objects.create(
            title='Test_title',
            slug='test-task',
            description='Test_description'
        )
        cls.post = Post.objects.create(
            text='The title of the test post is more than 15 characters',
            pub_date='2021-06-20',
            author=cls.author,
            group=cls.group
        )

    def test_post_name_is_15char_text(self):
        """В поле __str__  объекта post записано более 15 символов"""
        post_text = PostGroupModelTest.post
        expected_object_name = post_text.text[:15]
        self.assertEqual(expected_object_name, str(post_text))

    def test_str_group_title(self):
        group = PostGroupModelTest.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))
