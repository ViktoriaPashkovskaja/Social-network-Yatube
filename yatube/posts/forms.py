from django import forms
from django.forms import ModelForm

from .models import Post, Comment


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ['text', 'group', 'image']
        group = forms.ModelChoiceField(queryset=Post.objects.all(),
                                       required=False, to_field_name="group")
        widgets = {
            'text': forms.Textarea(),
        }

        labels = {
            "group": "Группа",
            "text": "Текст"
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ("text",)

        widgets = {
            'text': forms.Textarea(),
        }

        labels = {

            "text": "Текст"
        }
