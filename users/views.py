from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import User


def login_view(request):
    if request.user.is_authenticated:
        return redirect('exam-list')

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('exam-list')
        else:
            messages.error(request, 'Invalid credentials')

    return render(request, 'users/login.html', {})


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('exam-list')

    if request.method == 'POST':
        print("POST data:", request.POST)
        username = request.POST.get('username', '')
        email = request.POST.get('email', '')
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        role = request.POST.get('role', 'student')

        if not username:
            messages.error(request, 'Username is required')
            return render(request, 'users/signup.html', {})

        if password1 != password2:
            messages.error(request, 'Passwords do not match')
            return render(request, 'users/signup.html', {})

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken')
            return render(request, 'users/signup.html', {})

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1,
            role=role
        )
        login(request, user)
        return redirect('exam-list')

    return render(request, 'users/signup.html', {})


def logout_view(request):
    logout(request)
    return redirect('login')