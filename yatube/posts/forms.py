from django import forms
from django.forms import ModelForm

from .models import Post, Group, Comment


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ["text", "group", "image"]
        widgets = {
            "text": forms.Textarea(),
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
            "text": forms.Textarea(),
        }

        labels = {

            "text": "Текст"
        }
