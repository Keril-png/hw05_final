from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Post, Group, User, Comment
from .forms import PostForm, CommentForm
from django.core.paginator import Paginator
from django.views.decorators.cache import cache_page

@cache_page(20)
def index(request):
    post_list = Post.objects.order_by('-pub_date').all()
    paginator = Paginator(post_list, 10)

    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    
    return render(request,
        "index.html",
        {
            "page": page, 
            'paginator': paginator
        }
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)

    post_list = Post.objects.filter(group=group).order_by("-pub_date")
    posts_count = post_list.count()

    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    return render(
        request,
        "group.html",
        {
            "group": group,
            'page':page, 
            'paginator': paginator
        }
    )


@login_required
def new_post(request):
    post_is_new = True
    if request.method == "POST":
        form = PostForm(request.POST)

        if form.is_valid():
            new = form.save(commit=False)
            new.author = request.user
            new.save()
            return redirect('index')
        return render(request, 'post_edit.html', {'form': form, 'post_is_new': post_is_new})

    form = PostForm()
    return render(request, 'post_edit.html', {'form': form, 'post_is_new': post_is_new})


def profile(request, username):
    user = get_object_or_404(User, username=username)
    post_list = user.posts.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request, 
        'profile.html', 
        {
            'page': page, 
            'author': user,
            'paginator': paginator
        }
    )
 
 
def post_view(request, username, post_id):
    post = get_object_or_404(
        Post,
        author__username=username,
        pk=post_id
    )
    form = CommentForm()
    comment = Comment.objects.filter(post=post_id)
    return render(
        request,
        'post_view.html',
        {
            'post': post, 
            'author': post.author, 
            'comments': comment, 
            'form': form
        }
    )


@login_required
def post_edit(request, username, post_id):
    post_is_new = False
    post = get_object_or_404(Post, author__username=username, id=post_id)

    if request.user != post.author:
        return redirect("post", username=username, post_id=post_id)

    form = PostForm(request.POST or None, files=request.FILES or None, instance=post)
    
    if form.is_valid():
        form.save()
        return redirect("post", username=username, post_id=post_id)
    return render(request, 'post_edit.html', {'post':post, 'form': form, 'post_is_new': post_is_new})
    

@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, pk=post_id)
    comments = Comment.objects.filter(post=post_id)
    if request.method == 'POST':
        form = CommentForm(request.POST or None)
        if form.is_valid():
            form = form.save(commit=False)
            form.author = request.user
            form.post = post
            form.save()
            return redirect('post', username=post.author.username, post_id=post_id)
        else:
            form = CommentForm()
    form = CommentForm()
    return render(request, 'post_view.html', {'post': post, 'author': post.author, 'comments': comments, 'form': form})


def page_not_found(request, exception):
    return render(
        request, 
        "misc/404.html", 
        {"path": request.path}, 
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)


