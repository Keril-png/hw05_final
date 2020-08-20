from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Post, Group, User, Comment, Follow
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

@login_required
def follow_index(request):
    post_list = Post.objects.order_by('-pub_date').filter(author__following__user=request.user)
    paginator = Paginator(post_list, 10)

    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    
    return render(
        request, 
        "follow.html", 
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
    profile = True
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    posts_count = post_list.count
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    following = False
    follows_count = Follow.objects.filter(author=author).count
    subs_count = Follow.objects.filter(user=author).count
    

    if request.user.is_authenticated:
        if Follow.objects.filter(user=request.user, author=author).exists():
            following = True
        if request.user == author:
            profile = False
        
            
    return render(
        request, 
        'profile.html', 
        {   
            'profile': profile,
            'posts_count': posts_count,
            'follows_count': follows_count,
            'subs_count': subs_count,
            'page': page, 
            'author': author,
            'paginator': paginator,
            'following': following,
        }
    )
 
 
def post_view(request, username, post_id):
    profile = False
    post = get_object_or_404(
        Post,
        author__username=username,
        pk=post_id
    )
    author = get_object_or_404(User, username=username)
    posts_count = author.posts.all().count
    form = CommentForm()
    comments = post.comments.all()
    following = False
    follows_count = Follow.objects.filter(author=author).count
    subs_count = Follow.objects.filter(user=author).count
    
    return render(
        request,
        'post_view.html',
        {   
            'profile': profile,
            'posts_count': posts_count,
            'follows_count': follows_count,
            'subs_count': subs_count,
            'post': post, 
            'author': post.author, 
            'comments': comments, 
            'form': form,
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
        
    form = CommentForm(request.POST or None)
    if form.is_valid():
        form = form.save(commit=False)
        form.author = request.user
        form.post = post
        form.save()
        return redirect('post', username=post.author.username, post_id=post_id)
    form = CommentForm()
    return redirect("post", username=username, post_id=post_id)


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
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    samefollow = Follow.objects.filter(user=request.user, author=author)
    
    if request.user != author and not samefollow.exists():
        Follow.objects.create(
            user = request.user,
            author = author
        )
    return redirect('profile', username=username)
    


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    if Follow.objects.filter(user = request.user, author = author).exists():
        Follow.objects.filter(
            user = request.user,
            author = author
        ).delete()
    return redirect('profile', username=username)