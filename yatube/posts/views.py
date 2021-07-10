from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PostForm, CommentForm
from .models import Post, Group, User, Follow


def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, settings.COUNT_PAGINATOR)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'index.html',
        {'page': page, 'paginator': paginator}
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = Post.objects.filter(group=group)
    paginator = Paginator(posts, settings.COUNT_PAGINATOR)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, "posts/group.html", {'page': page,
                  'group': group, 'posts': posts, 'paginator': paginator})


def profile(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    posts = Post.objects.filter(author=author)
    count_posts = posts.count()
    paginator = Paginator(posts, settings.COUNT_PAGINATOR)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    following = user.is_authenticated and (
        Follow.objects.filter(user=user, author=author).exists())
    return render(request, "posts/profile.html", {
        "author": author,
        "page": page,
        "count_posts": count_posts,
        "following": following
    }
    )


@login_required
def new_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, files=request.FILES or None)

        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()

            return redirect('index')
        return render(request, 'posts/new.html', {'form': form})
    form = PostForm()
    return render(request, 'posts/new.html', {'form': form})


def post_view(request, username, post_id):
    post_object = get_object_or_404(Post.objects.select_related('author'),
                                    id=post_id, author__username=username)
    post_count = Post.objects.filter(author=post_object.author).count()
    comments = post_object.comments.all()
    form = CommentForm()
    context_dict = {
        'author': post_object.author,
        'post_count': post_count,
        'post': post_object,
        'comments': comments,
        'form': form,
    }
    return render(request, 'posts/post.html', context_dict)


@login_required
def post_edit(request, username, post_id):
    if request.user.username != username:
        return redirect('index')
    post = get_object_or_404(
        Post.objects.select_related('author'), id=post_id,
        author__username=username)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('post', username=username, post_id=post_id)
    return render(request, 'posts/new.html', {'form': form, 'post': post})


def page_not_found(request, exception):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post,
                             author__username=username,
                             id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        new_comment = form.save(commit=False)
        new_comment.author = request.user
        new_comment.post = post
        new_comment.save()
        return redirect('post', username, post_id)
    return render(request, "post.html", context={"form": form})


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, settings.COUNT_PAGINATOR)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        "includes/follow.html",
        {'page': page, 'paginator': paginator}
    )


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('profile', username=username)
