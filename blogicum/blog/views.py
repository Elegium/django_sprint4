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
from .models import Post, Category, Comment
from .forms import PostForm, UserForm, CommentForm
from django.contrib.auth import get_user_model
from .utils import object_filter
from django.core.paginator import Paginator


User = get_user_model()


class CustomSettingsCommentMixin:
    current_post = None
    model = Comment

    def get_success_url(self):
        return reverse(
            'blog:post_detail', kwargs={
                'post_id': self.current_post.id
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
    ).order_by(
        '-pub_date')


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'

    def get_object(self, **kwargs):
        post = get_object_or_404(
            Post.objects.select_related(
                'category',
                'location',

            ),
            pk=self.kwargs['post_id']
        )
        return post

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

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('blog:post_detail', post_id=self.kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.author != self.request.user:
            raise Http404
        return super().post(request, *args, **kwargs)

    # def get_object(self):
    #     post = get_object_or_404(
    #         Post.objects.select_related(
    #             'category',
    #             'location',
    #         ),
    #         pk=self.kwargs['post_id'],
    #         author=self.request.user
    #     )
    #     return post
    # #
    # def post(self, request, *args, **kwargs):
    #     post = get_object_or_404(
    #         Post.objects.select_related(
    #             'category',
    #             'location',
    #         ),
    #         pk=self.kwargs['post_id'],
    #     )
    #     if post.author != self.request.user:
    #         raise Http404
    #     return super(PostUpdateView, self).post(request, *args, **kwargs)


class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    template_name = 'blog/create.html'
    success_url = reverse_lazy('blog:index')

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return redirect('blog:post_detail', self.kwargs['post_id'])
        get_object_or_404(
            Post,
            pk=self.kwargs['post_id'],
            author=request.user
        )
        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        post = get_object_or_404(
            Post.objects.select_related(
                'category',
                'location',
            ),
            pk=self.kwargs['post_id'],

        )
        return post


class CategoryDetailView(DetailView):
    current_category = None
    model = Category
    template_name = 'blog/category.html'

    def get_object(self):
        self.current_category = get_object_or_404(
            Category.objects.filter(
                is_published=True
            ), slug=self.kwargs[
                'category_slug'
            ]
        )

        return self.current_category

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = object_filter(
            self.current_category.posts.all().order_by(
                '-pub_date'
            )
        )
        paginator = Paginator(queryset, 10)
        page = self.request.GET.get('page')
        page_obj = paginator.get_page(page)
        context['category'] = self.current_category
        context['page_obj'] = page_obj
        return context


class CommentCreateView(
    CustomSettingsCommentMixin,
    LoginRequiredMixin,
    CreateView
):
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


class CommentUpdateView(
    CustomSettingsCommentMixin,
    LoginRequiredMixin,
    UpdateView
):
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(
                'blog:post_detail', self.kwargs['post_id']
            )
        self.current_post = get_object_or_404(
            Post,
            id=kwargs['post_id']
        )
        get_object_or_404(Comment,
                          id=kwargs['comment_id'],
                          author=request.user)
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        return get_object_or_404(Comment, pk=self.kwargs.get('comment_id'))

    def form_valid(self, form):
        form.instance.post = self.current_post
        return super().form_valid(form)


class CommentDeleteView(
    CustomSettingsCommentMixin,
    LoginRequiredMixin,
    DeleteView
):
    template_name = 'blog/comment.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(
                'blog:post_detail', self.kwargs['post_id']

            )
        self.current_post = get_object_or_404(
            Post,
            id=kwargs['post_id']
        )
        get_object_or_404(Comment,
                          id=kwargs['comment_id'],
                          author=request.user)
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        return get_object_or_404(Comment, pk=self.kwargs.get('comment_id'))


class ProfileDetailView(DetailView):
    current_user = None
    model = User
    template_name = 'blog/profile.html'

    def get_object(self):
        self.current_user = get_object_or_404(
            User, username=self.kwargs.get(
                'username'
            )
        )
        return self.current_user

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)

        queryset = self.current_user.posts.all(

        ).order_by(
            '-pub_date'
        )
        paginator = Paginator(queryset, 10)
        page = self.request.GET.get('page')
        postss = paginator.get_page(page)
        context['page_obj'] = postss
        context['profile'] = self.current_user
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
