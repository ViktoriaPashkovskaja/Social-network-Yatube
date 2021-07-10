import time

from django import forms
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse
from http import HTTPStatus

from ..models import Group, Post, Follow

User = get_user_model()


class PostPagesTests(TestCase):
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

        cls.url_comment = reverse(
            'add_comment',
            kwargs={
                'username': cls.post.author.username,
                'post_id': cls.post.id
            }
        )

        cls.templates_url_names = {
            'index.html': reverse('index'),
            'posts/group.html': (
                reverse('group', kwargs={'slug': cls.group.slug})
            ),
            'posts/new.html': reverse('new_post'),
            'posts/profile.html': reverse(
                'profile',
                kwargs={'username': cls.author.username}
            ),
            'posts/post.html': reverse(
                'post',
                kwargs={
                    'username': cls.author.username,
                    'post_id': cls.post.id
                }
            ),
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_pages_use_correct_template(self):
        for template, reverse_name in self.templates_url_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_shows_correct_context(self):
        """
        Шаблон index c правильным контекстом.
        """
        response = self.authorized_client.get(reverse('index'))
        self.context_post_check(response.context, one_post=False)

    def test_group_page_shows_correct_context(self):
        """
        Шаблон group сформирован с правильным контекстом.
        """
        response = self.authorized_client.get(
            reverse('group', kwargs={'slug': self.group.slug})
        )
        group = response.context['group']
        self.assertEqual(group.title, PostPagesTests.group.title)
        self.assertEqual(group.slug, PostPagesTests.group.slug)
        self.assertEqual(group.description, PostPagesTests.group.description)
        self.assertIn('group', response.context)
        self.context_post_check(response.context, one_post=False)

    def test_profile_page_shows_correct_context(self):
        """
        Приложение post test_views profile контекст.
        """
        response = self.authorized_client.get(reverse(
            'profile', kwargs={'username': PostPagesTests.author}))
        self.assertEqual(response.context['author'],
                         PostPagesTests.post.author)
        self.assertIn('author', response.context)
        self.context_post_check(response.context, one_post=False)

    def test_post_page_shows_correct_context(self):
        """
        Приложение post test_views отдельный пост контекст.
        """
        response = self.authorized_client.get(reverse(
            'post', kwargs={'username': PostPagesTests.post.author.username,
                            'post_id': PostPagesTests.post.id}))
        self.assertIn('post', response.context)
        self.context_post_check(response.context, one_post=True)

    def test_post_page_edit_correct_context(self):
        """
        Приложение post test_views отдельный пост контекст.
        """
        response = self.authorized_client.get(reverse(
            'post_edit',
            kwargs={
                'username': self.author.username,
                'post_id': self.post.id
            }
        )
        )
        form_fields = {
            'text': forms.fields.CharField,

        }
        for value, expect in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expect)

    def context_post_check(self, context, one_post=False):
        if one_post:
            self.assertIn('post', context)
            post = context['post']
        else:
            self.assertIn('page', context)
            post = context['page'][0]
        self.assertEqual(post.text, PostPagesTests.post.text)
        self.assertEqual(post.author, PostPagesTests.post.author)
        self.assertEqual(post.group, PostPagesTests.post.group)
        self.assertEqual(post.pub_date, PostPagesTests.post.pub_date)


class TestFollow(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(title='TestGroup',
                                         slug='test_slug',
                                         description='Test description')
        cls.follow_user = User.objects.create_user(username='TestAuthor')

    def setUp(self):
        self.authorized_user = Client()
        self.authorized_user.force_login(self.follow_user)

    def test_follow(self):
        self.authorized_user.get(reverse('profile_follow', kwargs={
            'username': self.user.username}))
        follow = Follow.objects.first()
        self.assertEqual(Follow.objects.count(), 1)
        self.assertEqual(follow.author, self.user)
        self.assertEqual(follow.user, self.follow_user)

    def test_unfollow(self):
        self.authorized_user.get(reverse('profile_follow', kwargs={
            'username': self.user.username}))
        self.authorized_user.get(reverse('profile_unfollow', kwargs={
            'username': self.user.username}))
        self.assertFalse(Follow.objects.exists())

    def test_follow_index(self):
        Post.objects.create(author=self.user, text='test follow text',
                            group=self.group)
        self.authorized_user.get(reverse('profile_follow', kwargs={
            'username': self.user.username}))
        response = self.authorized_user.get(reverse('follow_index'))
        post = response.context['post']
        self.assertEqual(post.text, 'test follow text')
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.group.id, self.group.id)

    def test_not_follow_index(self):
        Post.objects.create(author=self.user, text='test follow text',
                            group=self.group)
        response = self.authorized_user.get(reverse('follow_index'))
        self.assertEqual(response.context['paginator'].count, 0)

    def test_following_self(self):
        self.assertEqual(Follow.objects.all().count(), 0)
        self.authorized_user.get(reverse('profile_follow', kwargs={
            'username': self.follow_user.username}))
        self.assertEqual(Follow.objects.all().count(), 0)
        self.authorized_user.get(reverse('profile_follow', kwargs={
            'username': self.user.username}))
        self.assertEqual(Follow.objects.all().count(), 1)


class TestComments(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.comment_user = User.objects.create_user(username='TestCommentUser')
        cls.post = Post.objects.create(text='test text', author=cls.user)
        cls.url_comment = reverse('add_comment', kwargs={
            'username': cls.post.author.username, 'post_id': cls.post.id})

    def setUp(self):
        self.anonymous = Client()
        self.authorized_user = Client()
        self.authorized_user.force_login(self.comment_user)

    def test_comment_anonymous(self):
        response = self.anonymous.get(self.url_comment)
        urls = '/auth/login/?next={}'.format(self.url_comment)
        self.assertRedirects(response, urls, status_code=HTTPStatus.FOUND)

    def test_comment_authorized(self):
        response = self.authorized_user.post(self.url_comment, {
            'text': 'test comment'}, follow=True)
        self.assertContains(response, 'test comment')


class CacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='Anonim')

        Post.objects.create(
            text='Text_test_1',
            author=cls.author,
            group=None
        )

    def setUp(self):
        self.user = CacheTests.author
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_cache_home_page(self):
        """Кеш главной страницы работает."""
        cache.clear()
        response_before = self.authorized_client.get(reverse('index'))
        self.assertEqual(
            len(response_before.context.get('page').object_list), 1)

        Post.objects.create(
            text='Text_test_2',
            author=self.author,
            group=None
        )

        response_after = self.authorized_client.get(reverse('index'))
        self.assertEqual(
            len(response_after.context.get('page').object_list), 2)

        time.sleep(21)

        response_after_20 = self.authorized_client.get(reverse('index'))
        self.assertEqual(
            len(response_after_20.context.get('page').object_list), 2)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='Anonim')
        cls.group = Group.objects.create(title='Test_group', slug='test_slug')
        cls.autoriz_client = Client()
        cls.autoriz_client.force_login(cls.author)
        for page in range(13):
            cls.post = Post.objects.create(
                author=cls.author,
                text='text_{page}',
                group=cls.group
            )

        cls.templates_pages_names = {
            'index.html': reverse('index'),
            'posts/group.html': (
                reverse('group', kwargs={'slug': cls.group.slug})
            ),
            'posts/profile.html': reverse(
                'profile',
                kwargs={'username': cls.author.username}
            ),
        }

    def test_first_page_paginator_ten_records(self):
        for template, reverse_name in self.templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.autoriz_client.get(reverse_name)
                self.assertEqual(
                    len(response.context.get('page').object_list), 10
                )

    def test_second_page_paginator_tree_records(self):
        for template, reverse_name in self.templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.autoriz_client.get(reverse_name + '?page=2')
                self.assertEqual(
                    len(response.context.get('page').object_list), 3
                )


class AboutPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.templates_pages_names = {
            'about/about.html': reverse('about:author'),
            'about/tech.html': reverse('about:tech')
        }

    def setUp(self):
        self.guest_client = Client()

    def test_about_pages_available_name(self):
        """URL, генерируемые в приложении about, доступны"""
        for adress, reverse_name in self.templates_pages_names.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(reverse_name)
                self.assertEqual(response.status_code, HTTPStatus.OK)
