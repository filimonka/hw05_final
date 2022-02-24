from http.client import HTTPResponse

from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page

from .models import Post, Group, Follow, User
from .forms import PostForm, CommentForm


def paginator(request, posts) -> Paginator:
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj


@cache_page(20, key_prefix='index_page')
def index(request) -> HTTPResponse:
    template = 'posts/index.html'
    posts = Post.objects.all()
    context: dict = {
        'page_obj': paginator(request, posts)
    }
    return render(request, template, context)


def group_posts(request, slug) -> HTTPResponse:
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    context: dict = {
        'group': group,
        'page_obj': paginator(request, posts),
    }
    return render(request, template, context)


def profile(request, username) -> HTTPResponse:
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    is_following = None
    if request.user.is_authenticated:
        is_following = request.user.follower.filter(author=author).exists()
    posts_count = author.posts.count()
    context = {
        'author': author,
        'page_obj': paginator(request, author.posts.all()),
        'posts_count': posts_count,
        'following': is_following,
    }
    return render(request, template, context)


def post_detail(request, post_id) -> HTTPResponse:
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, id=post_id)
    posts_count = Post.objects.filter(author_id=post.author_id).count()
    comments = post.comments.all()
    form = CommentForm(
        request.POST or None,
    )
    context: dict = {
        'post': post,
        'posts_count': posts_count,
        'form': form,
        'comments': comments,
    }
    return render(request, template, context)


@login_required
def post_create(request) -> HTTPResponse:
    user = request.user
    template = 'posts/create_post.html'
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = user
        post.save()
        return redirect('posts:profile', user.username)
    context: dict = {
        'form': form,
        'is_edit': False,
    }
    return render(request, template, context)


def post_edit(request, post_id) -> HTTPResponse:
    template = 'posts/create_post.html'
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.save()
        return redirect('posts:post_detail', post_id)
    context: dict = {
        'post': post,
        'form': form,
        'is_edit': True,
    }
    return render(request, template, context)


@login_required
def add_comment(request, post_id) -> HTTPResponse:
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id)


@login_required
def follow_index(request) -> HTTPResponse:
    template = 'posts/follow.html'
    current_user = request.user
    posts = Post.objects.filter(
        author__in=current_user.follower.values('author')
    )
    context = {
        'page_obj': paginator(request, posts),
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username) -> HTTPResponse:
    author = get_object_or_404(User, username=username)
    if Follow.objects.filter(user=request.user, author=author).exists():
        return redirect('posts:profile', username)
    if request.user != author:
        Follow.objects.create(user=request.user, author=author)
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username) -> HTTPResponse:
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:profile', username)
