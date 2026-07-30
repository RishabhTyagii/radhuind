from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import UserProfile, PAGES_MAP

def is_admin(user):
    if user.is_superuser:
        return True
    if hasattr(user, 'profile') and getattr(user.profile, 'allowed_pages', None):
        return 'manage_users' in user.profile.allowed_pages
    return False

@login_required
@user_passes_test(is_admin)
def manage_users(request):
    users = User.objects.all().order_by('-is_superuser', 'username')
    return render(request, 'accounts/manage_users.html', {'users': users})

@login_required
@user_passes_test(is_admin)
def create_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists!')
            return redirect('create_user')
            
        user = User.objects.create_user(username=username, password=password)
        
        # Create profile and set allowed pages
        profile = UserProfile.objects.create(user=user)
        allowed = request.POST.getlist('allowed_pages')
        profile.allowed_pages = allowed
        profile.save()
        
        messages.success(request, f'User {username} created successfully!')
        return redirect('manage_users')
        
    return render(request, 'accounts/create_user.html', {'PAGES_MAP': PAGES_MAP})

@login_required
@user_passes_test(is_admin)
def edit_user(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)
    profile, created = UserProfile.objects.get_or_create(user=user_obj)
    
    if request.method == 'POST':
        new_password = request.POST.get('password')
        if new_password:
            user_obj.set_password(new_password)
            user_obj.save()
            
        allowed = request.POST.getlist('allowed_pages')
        profile.allowed_pages = allowed
        profile.save()
        
        messages.success(request, f'User {user_obj.username} updated successfully!')
        return redirect('manage_users')
        
    return render(request, 'accounts/edit_user.html', {
        'user_obj': user_obj, 
        'profile': profile,
        'PAGES_MAP': PAGES_MAP
    })
