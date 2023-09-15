from django import forms
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from .models import Post, Comment

User = get_user_model()


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        exclude = ('author', 'is_published',)
        widgets = {
            'pub_date': forms.DateInput(attrs={'type': 'date'})
        }

    def clean(self):
        super().clean()
        title = self.cleaned_data['title']
        category = self.cleaned_data['category']
        pub_date = self.cleaned_data['pub_date']
        send_mail(
            subject='Новый ПОСТ!!!!',
            message=f'Название: {title} '
                    f'Категория: {category}'
                    f'Дата публикации:{pub_date}',
            from_email='from@example.com',
            recipient_list=['to@example.com'],
            fail_silently=True,
        )


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
