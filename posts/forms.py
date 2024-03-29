from django.forms import ModelForm
from .models import Post, Comment

class PostForm(ModelForm):
    class Meta:
        model = Post
#        fields = ['group', 'text']
        fields = ['group', 'text', 'image']
        labels = {
            'group': 'Группа',
            'text': 'Текст',
            'image': 'Картинка',
        }

class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields =['text']
        labels = {
            'text': 'Текст',
        }

        