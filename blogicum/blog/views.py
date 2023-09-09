from django.shortcuts import get_object_or_404, get_list_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from .models import Post, Category, Comment
from .forms import PostForm, UserForm, CommentForm
from django.contrib.auth import get_user_model
from .utils import object_filter

User = get_user_model()


class CustomSettingsCommentMixin:
    current_post = None
    model = Comment

    def dispatch(self, request, *args, **kwargs):
        self.current_post = get_object_or_404(Post, id=kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'post_id': self.current_post.id})


class PostListView(ListView):
    model = Post
    template_name = 'blog/index.html'
    paginate_by = 10
    queryset = object_filter(
        Post.objects.select_related(
            'category',
            'location'
        )
    ).order_by(
        '-pub_date')


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'

    def get_object(self):
        post = get_object_or_404(
            Post.objects.select_related(
                'category',
                'location'
            )
            , pk=self.kwargs['post_id']
        )
        return post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = (
            self.object.comments.select_related('author')
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
        return reverse('blog:profile', kwargs={'username': self.request.user.username})


class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def get_object(self):
        post = get_object_or_404(
            Post.objects.select_related(
                'category',
                'location'
            )
            , pk=self.kwargs['post_id']
        )
        return post


class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    template_name = 'blog/create.html'
    success_url = reverse_lazy('blog:index')

    def get_object(self):
        post = get_object_or_404(
            Post.objects.select_related(
                'category',
                'location'
            )
            , pk=self.kwargs['post_id']
        )
        return post


class CategoryListView(ListView):
    model = Category
    template_name = 'blog/category.html'
    paginate_by = 10

    def get_queryset(self):
        category = get_object_or_404(Category, slug=self.kwargs['category_slug'])
        return get_list_or_404(
            object_filter(
                category.posts.all().order_by(
                    '-pub_date'
                )
            )
        )

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        category = get_object_or_404(Category, slug=self.kwargs['category_slug'])
        context['category'] = category
        return context

    # def get_related_activities(self):
    #     queryset = self.object.activity_rel.all()
    #     paginator = Paginator(queryset, 5)  # paginate_by
    #     page = self.request.GET.get('page')
    #     activities = paginator.get_page(page)
    #     return activities Добавь в контекст

class CommentCreateView(CustomSettingsCommentMixin, LoginRequiredMixin, CreateView):
    form_class = CommentForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = self.current_post
        return super().form_valid(form)


class CommentUpdateView(CustomSettingsCommentMixin, LoginRequiredMixin, UpdateView):
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def get_object(self, queryset=None):
        return get_object_or_404(Comment, pk=self.kwargs.get('comment_id'))

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = self.current_post
        return super().form_valid(form)


class CommentDeleteView(CustomSettingsCommentMixin, LoginRequiredMixin, DeleteView):
    template_name = 'blog/comment.html'

    def get_object(self, queryset=None):
        return get_object_or_404(Comment, pk=self.kwargs.get('comment_id'))

class ProfileDetailView(LoginRequiredMixin, ListView):
    model = Post
    template_name = 'blog/profile.html'
    paginate_by = 10

    def get_queryset(self):
        return Post.objects.filter(author__username=self.kwargs.get('username')).select_related(
            'category',
            'location'
        ).order_by(
            '-pub_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = get_object_or_404(User, username=self.kwargs.get('username'))
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    user = None
    model = User
    form_class = UserForm
    template_name = 'blog/user.html'

    def get_object(self, queryset=None):
        self.user = get_object_or_404(User, username=self.request.user.username)
        return self.user

    def get_success_url(self):
        return reverse('blog:profile', kwargs={'username': self.user.username})
