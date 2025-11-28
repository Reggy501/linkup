from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.conf import settings
from .models import Profile,Post, Like, Group, GroupPost, GroupMessage
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.core.files.storage import default_storage
from django.db.models import Q
from django.core.paginator import Paginator


def home(request):
    return render(request, 'core/home.html')

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()                                   # creates User
            username = form.cleaned_data.get('username')
            messages.success(
                request,
                f'Account created for {username}! You can now log in.'
            )
            return redirect('login')                      # we’ll create login later
    else:
        form = UserCreationForm()
    return render(request, 'core/register.html', {'form': form})


def logout_view(request):
    """Log the user out and redirect to LOGOUT_REDIRECT_URL (or home).

    Accepts GET and POST to make logout links convenient in the UI. This
    is intentionally simple — for higher security prefer a POST form.
    """
    logout(request)
    redirect_url = getattr(settings, 'LOGOUT_REDIRECT_URL', '/') or '/'
    return redirect(redirect_url)

@login_required
def dashboard(request):
    # Ensure the user has a Profile object. If not, create a blank one.
    profile, _ = Profile.objects.get_or_create(user=request.user)
    query = request.GET.get('q', '')

    members = Profile.objects.select_related('user')
    if query:
        members = members.filter(
            Q(user__username__icontains=query) |
            Q(full_name__icontains=query) |
            Q(email__icontains=query)
        )

    members = members.exclude(user=request.user)  # optional: hide self
    paginator = Paginator(members, 6)  # 6 per page
    page = request.GET.get('page')
    members_page = paginator.get_page(page)
    context = {
        'profile': profile,
        # pass the paginated page object so template pagination helpers work
        'members': members_page,
        'query': query,
    }
    return render(request, 'core/dashboard.html', context)

@login_required
def update_profile(request):
    profile = request.user.profile

    if request.method == 'POST':
        # Handle avatar
        if 'avatar' in request.FILES:
            # Delete old avatar if exists
            if profile.avatar:
                default_storage.delete(profile.avatar.path)
            profile.avatar = request.FILES['avatar']

        profile.full_name = request.POST.get('full_name', '').strip()
        profile.email     = request.POST.get('email', '').strip()
        profile.phone     = request.POST.get('phone', '').strip()
        profile.bio       = request.POST.get('bio', '').strip()
        profile.save()

        messages.success(request, 'Profile updated!')
        return redirect('dashboard')
    return redirect('dashboard')

@login_required
def update_consistency(request):
    profile = request.user.profile

    if request.method == 'POST':
        members_input = request.POST.get('members', '').strip()
        score_input   = request.POST.get('score', '').strip()

        # Parse members into list
        members = [m.strip() for m in members_input.split(',') if m.strip()]

        # Validate score
        score = None
        if score_input.isdigit():
            score = int(score_input)
            if not (0 <= score <= 100):
                score = None

        profile.consistency_family = {
            'members': members,
            'score': score
        }
        profile.save()

        messages.success(request, 'Consistency Family updated!')
        return redirect('dashboard')

    return redirect('dashboard')

@login_required
def member_detail(request, pk):
    member = get_object_or_404(Profile, pk=pk)
    return render(request, 'core/member_detail.html', {'member': member})

@login_required
def create_post(request):
    if request.method == 'POST':
        caption = request.POST.get('caption', '')
        image = request.FILES.get('image')

        Post.objects.create(
            author=request.user,
            caption=caption,
            image=image
        )
        messages.success(request, 'Your post is live!')
        return redirect('explore')

    return redirect('dashboard')

@login_required
def explore(request):
    posts = Post.objects.all().prefetch_related('likes')
    return render(request, 'core/explore.html', {'posts': posts})

@login_required
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    like, created = Like.objects.get_or_create(user=request.user, post=post)

    if not created:
        like.delete()  # Unlike
    return redirect('explore')

@login_required
def groups(request):
    # Use the related_name defined on Group.members to access core groups
    my_groups = request.user.member_groups.all()
    other_groups = Group.objects.exclude(members=request.user)
    return render(request, 'core/groups.html', {
        'my_groups': my_groups,
        'other_groups': other_groups
    })

@login_required
def create_group(request):
    if request.method == 'POST':
        name = request.POST['name']
        description = request.POST.get('description', '')
        image = request.FILES.get('image')
        
        group = Group.objects.create(
            name=name,
            description=description,
            creator=request.user,
            image=image
        )
        group.members.add(request.user)
        messages.success(request, f'Group "{name}" created!')
        return redirect('group_detail', group.id)
    return render(request, 'core/create_group.html')

@login_required
def group_detail(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    if request.user not in group.members.all():
        messages.error(request, "You are not a member of this group.")
        return redirect('groups')
    
    posts = group.posts.all()
    messages_chat = group.messages.all()[:50]  # last 50
    return render(request, 'core/group_detail.html', {
        'group': group,
        'posts': posts,
        'messages': messages_chat
    })

@login_required
def join_group(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    group.members.add(request.user)
    messages.success(request, f"You joined {group.name}!")
    return redirect('group_detail', group.id)

@login_required
def post_in_group(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    if request.user not in group.members.all():
        return redirect('groups')
        
    if request.method == 'POST':
        content = request.POST['content']
        image = request.FILES.get('image')
        GroupPost.objects.create(
            group=group,
            author=request.user,
            content=content,
            image=image
        )
    return redirect('group_detail', group_id)

@login_required
def send_message(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    if request.user not in group.members.all():
        return redirect('groups')
        
    if request.method == 'POST':
        content = request.POST['message']
        GroupMessage.objects.create(
            group=group,
            author=request.user,
            content=content
        )
    return redirect('group_detail', group_id)
