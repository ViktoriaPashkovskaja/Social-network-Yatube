from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from http import HTTPStatus
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class TaskURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='Anonim')
        cls.not_author = User.objects.create_user(username='Not_Author')
        cls.group = Group.objects.create(
            title='Тестовое назвние группы',
            slug='slug',
            description='Тестовое описание группы',
        )
        cls.post = Post.objects.create(
            text='The title of the test post is more than 15 characters' * 15,
            author=cls.author,
            group=cls.group
        )

        cls.templates_url_names = {
            'index.html': '/',
            'posts/group.html': f'/group/{cls.group.slug}/',
            'posts/new.html': '/new/',
            'posts/profile.html': f'/{cls.author.username}/',
            'posts/post.html': f'/{cls.author.username}/{cls.post.id}/'
        }

    def setUp(self):
        self.guest_client = Client()
        self.not_author_client = Client()
        self.not_author_client.force_login(self.not_author)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_pages_authorized_client(self):
        for template, reverse_name in self.templates_url_names.items():
            with self.subTest():
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(response.status_code, HTTPStatus.OK)
        response = self.authorized_client.get(
            f'/{self.author.username}/{self.post.id}/edit/'
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_guest_client(self):
        for template, reverse_name in self.templates_url_names.items():
            with self.subTest():
                if reverse_name == reverse('new_post'):
                    response = self.guest_client.get(reverse_name)
                    self.assertEqual(response.status_code, HTTPStatus.FOUND)
                    self.assertRedirects(response, '/auth/login/?next=/new/')
                else:
                    response = self.guest_client.get(reverse_name)
                    self.assertEqual(response.status_code, HTTPStatus.OK)
        response = self.guest_client.get(
            f'/{self.author.username}/{self.post.id}/edit/'
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_pages_not_author_client(self):
        for template, reverse_name in self.templates_url_names.items():
            with self.subTest():
                response = self.not_author_client.get(reverse_name)
                self.assertEqual(response.status_code, HTTPStatus.OK)
        response = self.not_author_client.get(
            f'/{self.author.username}/{self.post.id}/edit/'
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_page_correct_templates(self):
        for template, reverse_name in self.templates_url_names.items():
            with self.subTest():
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
        response = self.authorized_client.get(
            f'/{self.author.username}/{self.post.id}/edit/'
        )
        self.assertTemplateUsed(response, 'posts/new.html')
