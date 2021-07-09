import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import response
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()

TEMP_MEDIA = tempfile.mkdtemp(dir=settings.BASE_DIR)
@override_settings (MEDIA_ROOT=TEMP_MEDIA)
class OurTestCase(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)
        super().tearDownClass()

class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='Anonim')
        
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title='Test_name',
            slug='test_slug',
            description='Test_description'
        )

        cls.post = Post.objects.create(
            text='The title of the test post is more than 15 characters' * 15,
            author=cls.author,
            group=cls.group,
            image=cls.uploaded
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_post_create(self):
        posts_count = Post.objects.count()

        form_data = {
            'text': 'Test_text',
            'group': self.group.id,
            'image': self.uploaded
        }
        self.authorized_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(Post.objects.filter(
            text=form_data['text'],
            group=form_data['group'],
            image='media/small.gif'
        ).exists()
        )

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
