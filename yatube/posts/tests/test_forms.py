import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post, User


TEMP_MEDIA = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class TestPostForm(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='Anonim')
        cls.group = Group.objects.create(
            title='Test_name',
            slug='test_slug',
            description='Test_description'
        )

        cls.post = Post.objects.create(
            text='The title of the test post is more than 15 characters' * 15,
            author=cls.author,
            group=cls.group
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_create_form_post(self):
        posts = Post.objects.count()

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {'text': 'test text form',
                     'group': self.group.id,
                     'image': uploaded}
        self.authorized_client.post(
            reverse('new_post'),
            data=form_data
        )
        response = self.authorized_client.get(reverse('index'))
        self.assertEqual(Post.objects.count(), posts + 1)
        self.assertTrue(Post.objects.filter(
            text=form_data['text'],
            group=self.group,
            image='posts/small.gif'
        ).exists()
        )
        self.assertTrue(response.context['page'][0].image.name, uploaded.name)

    def test_form_post_edit_to_db(self):
        form_post = {
            'text': 'another test text form',
            'group': self.group.id
        }
        self.authorized_client.post(reverse(
            'post_edit',
            kwargs={
                'username': self.author.username,
                'post_id': self.post.id
            }),
            data=form_post)
        response = self.authorized_client.get(reverse(
            'post',
            kwargs={
                'username': self.author.username,
                'post_id': self.post.id
            }
        )
        )
        self.assertEqual(
            response.context['post'].text,
            form_post['text']
        )
        self.assertTrue(Post.objects.filter(text=form_post['text'],
                        id=self.post.id, group=self.group.id).exists())
