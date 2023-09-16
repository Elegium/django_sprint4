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
from .utils import object_filter
from django.core.paginator import Paginator
from django.db.models import Count

NOW_DATE = dt.datetime.now().date()


class CustomSettingsCommentMixin:
    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(
                'blog:post_detail', self.kwargs['post_id']
            )
        get_object_or_404(Comment,
                          id=kwargs['comment_id'],
                          author=request.user)
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
    paginate_by = 10
    queryset = object_filter(
        Post.objects.select_related(
            'category',
            'location'
        )
    )

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        comment_count = Post.objects.annotate(
            comments_count=Count(
                'comments'
            )
        ).all()
        context['comment_count'] = comment_count
        return context


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
                or dt.datetime.date(post.pub_date) >= NOW_DATE
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
        if not self.request.user.is_authenticated:
            return redirect('blog:post_detail', post_id=self.kwargs['post_id'])
        post = get_object_or_404(
            Post.objects.select_related(
                'category',
                'location',
            ),
            pk=self.kwargs['post_id'],

        )
        if post.author != self.request.user and not request.user.is_superuser:
            raise Http404
        return super().dispatch(request, *args, **kwargs)


class CategoryDetailView(DetailView):
    current_category = None
    model = Category
    template_name = 'blog/category.html'
    slug_url_kwarg = 'category_slug'
    queryset = Category.objects.filter(
        is_published=True
    )

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = object_filter(
            self.object.posts.all().order_by(
                '-pub_date'
            )
        )
        paginator = Paginator(queryset, 10)
        page = self.request.GET.get('page')
        page_obj = paginator.get_page(page)
        context['category'] = self.current_category
        context['page_obj'] = page_obj
        return context


class CommentCreateView(LoginRequiredMixin, CreateView):
    current_post = None
    model = Comment
    form_class = CommentForm

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(
                'blog:post_detail', self.kwargs['post_id']
            )
        self.current_post = get_object_or_404(
            Post,
            id=kwargs['post_id']
        )
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = self.current_post
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:post_detail', kwargs={
                'post_id': self.current_post.id
            }
        )


class CommentUpdateView(
    CustomSettingsCommentMixin,
    LoginRequiredMixin,
    UpdateView
):
    form_class = CommentForm

    def form_valid(self, form):
        post = get_object_or_404(
            Post,
            id=self.kwargs['post_id']
        )
        form.instance.post = post
        return super().form_valid(form)


class CommentDeleteView(
    CustomSettingsCommentMixin,
    LoginRequiredMixin,
    DeleteView
):
    """
    Класс использует миксины.
    """


class ProfileListView(ListView):
    model = Post
    template_name = 'blog/profile.html'
    paginate_by = 10

    def get_queryset(self):
        return super(
            ProfileListView, self
        ).get_queryset().filter(
            author__username=self.kwargs.get(
                'username'
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
    user = None
    model = User
    form_class = UserForm
    template_name = 'blog/user.html'

    def get_object(self, queryset=None):
        self.user = get_object_or_404(
            User, username=self.request.user.username
        )
        return self.user

    def get_success_url(self):
        return reverse('blog:profile', kwargs={'username': self.user.username})
