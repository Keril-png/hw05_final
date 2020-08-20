from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.test import Client
from .models import Post, User, Group, Follow, Comment
from django.urls import reverse
from django.core.cache import cache
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile

class NotAuthotizedTests(TestCase):
    def SetUp(self):
        self.client = Client()

    def test_NotAuthUserCantCreatePost(self):
        response = self.client.get(reverse('new_post'), follow=True)
        self.assertRedirects(response, '/auth/login/?next=/new/')

    def test_NotAuthUserCantComment(self):
        test_text = 'Just wanted to talk to you about baba'
        author = User.objects.create(
            username = 'avtor',
            password = 'avtor'
        )
        post = Post.objects.create(
            text = test_text,
            author = author
        )
        response = self.client.get(
            reverse('add_comment', args=[author, post.id]),
        )

        self.assertRedirects(response, reverse('login')+'?next='+reverse('add_comment', args=[author, post.id]))

        self.assertEquals(0, len(Comment.objects.filter(author=author, post=post)))


class AuthorizedTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.myuser = User.objects.create(
            username = 'biba', 
            password = 'boba'
        )
        self.group1 = Group.objects.create(
            title = 'biba&boba inc', 
            slug = 'bboys',
            description = 'our circle of b-boys'
        )
        self.group2 = Group.objects.create(
            title = 'biba&boba inc p2', 
            slug = 'bboys2',
            description = 'our square of b-boys'
        )
        self.client.force_login(self.myuser)
        self.image_path = 'media/posts/med_1547914593_image.jpg'
        self.random_path = 'posts/urls.py'

    def test_Profile(self):
        
        response = self.client.get(reverse('profile', kwargs={'username': self.myuser.username}))
        self.assertEqual(response.status_code, 200)

    def test_AuthUserCanCreatePost(self):
        test_text = 'Just wanted to talk to you about baba'
        response = self.client.post(
            reverse('new_post'), 
            {'group': self.group1.id, 'text': test_text}, 
            follow=True
        )
        
        self.assertEqual(response.status_code, 200)
        count_post = Post.objects.count()
        new_post = Post.objects.first()
            
        self.assertEqual(count_post, 1)
        self.assertEqual(new_post.text, test_text)
        self.assertEqual(new_post.author, self.myuser)
        self.assertEqual(new_post.group, self.group1)
    
    
    def contains_check(self, url, text, post_id, author, group):
        response = self.client.get(url)
        if response.context.get('paginator') is None:
            post = response.context.get('post')
        else:
            p = response.context.get('paginator')
            self.assertEqual(1, p.count)
            post = response.context['page'].object_list[0]

        self.assertEqual(post.text, text)
        self.assertEqual(post.author, author)
        self.assertEqual(post.group, group)

    @override_settings(CACHES = {'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}})
    def test_PostIsEverywhere(self):
        cache.clear()
        test_text = 'Just wanted to talk to you about baba'
        post = Post.objects.create(
            text = test_text, 
            group = self.group1,
            author = self.myuser
        )
        urls = [
            reverse('index'),
            reverse('profile', kwargs={'username': self.myuser.username}),
            reverse(
                'post', 
                kwargs={'username': self.myuser.username, 'post_id': post.id}
            ),
            reverse('group', kwargs={'slug': self.group1.slug}),
        ]

        for url in urls:
            self.contains_check(url, test_text, post.id, self.myuser, self.group1)

    @override_settings(CACHES = {'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}})
    def test_AuthUserCanEdit(self):
        test_text = 'Just wanted to talk to you about baba'
        new_text = 'Just wanted to talk to you about us...'

        post = Post.objects.create(
            text = test_text, 
            group = self.group1,
            author = self.myuser
        )
        self.client.post(
            reverse('post_edit', args=[self.myuser.username, post.id]), 
            {'text': new_text, 'group': self.group2.id}, 
            Follow=True
        )
        urls = [
            reverse('index'),
            reverse('profile', kwargs={'username': self.myuser.username}),
            reverse(
                'post', 
                kwargs={'username': self.myuser.username, 'post_id':post.id}
            ),
            reverse('group', kwargs={'slug': self.group2.slug}),
        ]

        for url in urls:
            self.contains_check(url, new_text, post.id, self.myuser, self.group2)
        
        response = self.client.get(reverse('group', kwargs={'slug': self.group1.slug}))
        self.assertEqual(response.context.get('paginator').count, 0)

    @override_settings(CACHES = {'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}})
    def test_ImageExists(self):
        test_text = 'Just wanted to talk to you about baba'
        post = Post.objects.create(
            text = test_text, 
            group = self.group1,
            author = self.myuser
        )

        image_obj = BytesIO()
        image = Image.new("RGBA", size=(100, 100), color=(255, 255, 255))
        image.save(image_obj, 'png')
        image_obj.seek(0)
        img = SimpleUploadedFile('media/posts/image.png', image_obj.read(), 'image/png')

        with open('media/posts/image.png', 'rb') as file:
            self.client.post(
                reverse('post_edit', args=[self.myuser.username, post.id]), 
                {'author': self.myuser, 'text': 'post with image', 'image': file}
            )

        urls = [
            reverse('index'),
            reverse('profile', kwargs={'username': self.myuser.username}),
            reverse(
                'post', 
                kwargs={'username': self.myuser.username, 'post_id':post.id}
            )
        ]
        
        for url in urls:
            response = self.client.get(url)
            self.assertContains(response, '<img')

    def test_ImageNotExists(self):
        test_text = 'Just wanted to talk to you about baba'
        post = Post.objects.create(
            text = test_text, 
            group = self.group1,
            author = self.myuser
        )
        with open(self.random_path, 'rb') as img:     
            response = self.client.post(
                reverse('post_edit', args=[self.myuser.username, post.id]), 
                {'author': self.myuser, 'text': 'post with no image', 'image': img}
            )
            self.assertFormError(
                response, 
                'form', 
                field='image', 
                errors='Загрузите правильное изображение. Файл, который вы загрузили, поврежден или не является изображением.'
            )

    def test_AuthUserCanFollow(self):
        author = User.objects.create(
            username = 'avtor',
            password = 'avtor'
        )
        self.client.get(
            reverse('profile_follow',
            args = [author],
            )
        )
        sub_exists = Follow.objects.filter(user=self.myuser, author=author).exists()
        self.assertEqual(sub_exists, True)

    def test_AuthUserCanUnfollow(self):
        author = User.objects.create(
            username = 'avtor',
            password = 'avtor'
        )
        Follow.objects.create(
            user=self.myuser, 
            author=author
        )
        self.client.get(
            reverse('profile_unfollow',
            args = [author],
            )
        )
        sub_exists = Follow.objects.filter(user=self.myuser, author=author).exists()
        self.assertEqual(sub_exists, False)

    def test_UserSeeOnlyFollowedPosts(self):
        author = User.objects.create(
            username = 'avtor',
            password = 'avtor'
        )
        
        post = Post.objects.create(
            text = 'test_text', 
            group = self.group1,
            author = author
        )
        Follow.objects.create(
            user=self.myuser, 
            author=author
        )
        
        self.contains_check(
            reverse('follow_index'), 
            post.text, 
            post.id, 
            author,
            self.group1
        )

    def test_UserCantSeeUnfollowedPosts(self):
        author = User.objects.create(
            username = 'avtor',
            password = 'avtor'
        )
        
        post = Post.objects.create(
            text = 'test_text', 
            group = self.group1,
            author = author
        )
        response = self.client.get(
            reverse('follow_index')
        )
        if Follow.objects.filter(user=self.myuser, author=author).exists():
            Follow.objects.filter(user=self.myuser, author=author).delete()
        self.assertEqual(len(response.context['paginator'].object_list), 0)


    
    def test_AuthUserCanComment(self):
        test_text = 'Just wanted to talk to you about baba'
        post = Post.objects.create(
            text = test_text, 
            group = self.group1,
            author = self.myuser
        )
        self.client.post(
            reverse('add_comment', args=[self.myuser.username, post.id]),
            {'text': 'koment'}
        )
        response = self.client.get(
            reverse('post', args = [self.myuser.username, post.id])
        )

        comments = Comment.objects.filter(
            post=post, 
            text='koment',
            author=self.myuser
        )
        self.assertEqual(len(comments),1)
        self.assertEqual(comments[0].text, 'koment')    


class CodesTests(TestCase):
    def SetUp(self):
        self.client = Client()

    def code404_test(self):
        response = self.client.get('/brabra/asdasdasdasd/')
        self.assertEqual(response.status_code, 404)


class CacheTest(TestCase):
    
    def setUp(self):
        self.client = Client()
        self.myuser = User.objects.create(
            username = 'biba', 
            password = 'boba'
        )
        self.client.force_login(self.myuser)

    def test_cache(self):
        test_text = 'wasd'
        new_text = 'dsaw'
        post = Post.objects.create(
            text = test_text, 
            author = self.myuser
        )
        self.client.post(
            reverse('post_edit', args=[self.myuser.username, post.id]), 
            {'text': new_text}, 
            Follow=True
        )

        response = self.client.get(reverse('index'))
        self.assertNotContains(response, new_text)
        cache.clear()
        self.assertContains(response, new_text)
                