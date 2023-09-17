import datetime as dt
from django.shortcuts import get_object_or_404, redirect, Http404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import (
    CreateView,
    ListView,
    DetailView,
    UpdateView,
    DeleteView
)
from django.urls import reverse_lazy, reverse
from .models import Post, Category, Comment, User
from .forms import PostForm, UserForm, CommentForm
from django.db.models import Count


class CustomSettingsCommentMixin(LoginRequiredMixin):
    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def dispatch(self, request, *args, **kwargs):
        comment = get_object_or_404(
            Comment,
            id=self.kwargs['comment_id']
        )
        if request.user != comment.author:
            return redirect(
                'blog:post_detail', self.kwargs['post_id']
            )
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            'blog:post_detail', kwargs={
                'post_id': self.kwargs['post_id']
            }
        )


class PostListView(ListView):
    model = Post
    template_name = 'blog/index.html'
    ordering = ['-pub_date']
    paginate_by = 10

    def get_queryset(self):
        return super(
            PostListView, self
        ).get_queryset().filter(
            pub_date__lte=dt.datetime.now(),
            is_published=True,
            category__is_published=True
        ).select_related(
            'category',
            'location',
            'author'
        ).annotate(
            comment_count=Count(
                'comments'
            )
        )


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        post = get_object_or_404(
            Post.objects.select_related(
                'category',
                'location',
            ),
            pk=self.kwargs['post_id'],
        )
        if (
                not post.is_published
                or not post.category.is_published
                or dt.datetime.date(post.pub_date) >= dt.datetime.now().date()
        ) and self.request.user != post.author:
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = (
            self.object.comments.select_related('author').order_by('create_at')
        )
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:profile', kwargs={
                'username': self.request.user.username
            }
        )


class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.author != self.request.user:
            return redirect('blog:post_detail', post_id=self.kwargs['post_id'])
        return super().post(request, *args, **kwargs)


class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    template_name = 'blog/create.html'
    success_url = reverse_lazy('blog:index')
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        post = get_object_or_404(
            Post.objects.select_related(
                'category',
                'location',
            ),
            pk=self.kwargs['post_id']
        )
        if post.author != self.request.user and not request.user.is_superuser:
            raise Http404
        return super().dispatch(request, *args, **kwargs)


class CategoryListView(ListView):
    model = Post
    template_name = 'blog/category.html'
    slug_url_kwarg = 'category_slug'
    ordering = ['-pub_date']
    paginate_by = 10

    def get_queryset(self):
        return super(
            CategoryListView, self
        ).get_queryset().filter(
            category__slug=self.kwargs.get(
                'category_slug'
            ), is_published=True,
            pub_date__lte=dt.datetime.now().date(),
            category__is_published=True
        ).select_related(
            'category',
            'location',
            'author'
        ).annotate(
            comment_count=Count(
                'comments'
            )
        )

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        category = get_object_or_404(
            Category, slug=self.kwargs.get(
                'category_slug'
            ), is_published=True
        )
        context['category'] = category
        return context


class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentForm

    def form_valid(self, form):
        post = get_object_or_404(Post, id=self.kwargs['post_id'])
        form.instance.author = self.request.user
        form.instance.post = post

        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:post_detail', kwargs={
                'post_id': self.kwargs['post_id']
            }
        )


class CommentUpdateView(CustomSettingsCommentMixin, UpdateView):
    form_class = CommentForm


class CommentDeleteView(CustomSettingsCommentMixin, DeleteView):
    """
    Класс использует миксины.
    """


class ProfileListView(ListView):
    model = Post
    template_name = 'blog/profile.html'
    ordering = ['-pub_date']
    paginate_by = 10

    def get_queryset(self):
        return super(
            ProfileListView, self
        ).get_queryset().filter(
            author__username=self.kwargs.get(
                'username'
            )
        ).select_related(
            'category',
            'location',
            'author'
        ).annotate(
            comment_count=Count(
                'comments'
            )
        )

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        user = get_object_or_404(
            User, username=self.kwargs.get(
                'username'
            )
        )
        context['profile'] = user
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserForm
    template_name = 'blog/user.html'

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse('blog:profile', args=[self.request.user.username])
