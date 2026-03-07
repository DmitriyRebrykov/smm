from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.db import transaction

from .forms import (
    CustomUserCreationForm,
    CustomAuthenticationForm,
    UserUpdateForm,
    UserProfileUpdateForm
)
from apps.courses.models import CourseAccess, Purchase



@require_http_methods(["GET", "POST"])
def register_view(request):
    if request.user.is_authenticated:
        return redirect('users:profile')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)

            messages.success(request, f'Добро пожаловать, {user.first_name}!')

            next_url = request.GET.get('next', 'users:profile')
            return redirect(next_url)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = CustomUserCreationForm()

    return render(request, 'users/register.html', {'form': form})


@require_http_methods(["GET", "POST"])
def login_view(request):

    if request.user.is_authenticated:
        return redirect('users:profile')

    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()
            login(request, user)

            messages.success(request, f'Добро пожаловать, {user.get_short_name()}!')

            next_url = request.GET.get('next') or request.POST.get('next', 'users:profile')
            return redirect(next_url)
        else:
            messages.error(request, 'Неверный email или пароль')
    else:
        form = CustomAuthenticationForm()

    return render(request, 'users/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'Вы успешно вышли из системы')
    return redirect('main:index')


@login_required
def profile_view(request):
    accesses = CourseAccess.objects.filter(
        user=request.user,
        is_active=True
    ).select_related('course')

    purchases = Purchase.objects.filter(
        user=request.user
    ).select_related('course').order_by('-created_at')[:10]

    from .models import UserProfile
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    context = {
        'accesses': accesses,
        'purchases': purchases,
        'profile': profile,
    }

    return render(request, 'users/profile.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def profile_edit_view(request):
    from .models import UserProfile
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, request.FILES, instance=request.user)
        profile_form = UserProfileUpdateForm(request.POST, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            with transaction.atomic():
                user_form.save()
                profile_form.save()

            messages.success(request, 'Профиль успешно обновлен!')
            return redirect('users:profile')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = UserProfileUpdateForm(instance=profile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }

    return render(request, 'users/profile_edit.html', context)


@login_required
def my_courses_view(request):
    accesses = CourseAccess.objects.filter(
        user=request.user,
        is_active=True
    ).select_related('course')

    return render(request, 'users/my_courses.html', {
        'accesses': accesses,
    })


@login_required
def purchases_history_view(request):
    purchases = Purchase.objects.filter(
        user=request.user
    ).select_related('course').order_by('-created_at')

    return render(request, 'users/purchases_history.html', {
        'purchases': purchases,
    })