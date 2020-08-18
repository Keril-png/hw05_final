from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.test import Client
from .models import Post, User, Group
from django.urls import reverse
from django.core.cache import cache


class NotAuthotizedTests(TestCase):
    def SetUp(self):
        self.client = Client()

    def test_NotAuthUserCantCreatePost(self):
        response = self.client.get(reverse('new_post'), follow=True)
        self.assertRedirects(response, '/auth/login/?next=/new/')


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
        cache.clear()
        response = self.client.get(url)
        if response.context.get('paginator') is None:
            post = response.context.get('post')
        else:
            p = response.context.get('paginator')
            self.assertEqual(1, p.count)
            post = p.page(1).object_list[0]

        self.assertEqual(post.text, text)
        self.assertEqual(post.author, author)
        self.assertEqual(post.group, group)

    def test_PostIsEverywhere(self):
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

    def test_ImageExists(self):
        test_text = 'Just wanted to talk to you about baba'
        post = Post.objects.create(
            text = test_text, 
            group = self.group1,
            author = self.myuser
        )
        with open(self.image_path, 'rb') as img:     
            self.client.post(
                reverse('post_edit', args=[self.myuser.username, post.id]), 
                {'author': self.myuser, 'text': 'post with image', 'image': img}
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
                
    


        