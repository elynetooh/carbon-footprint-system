from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from footprint import views as footprint_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('footprint.urls')),
    path('login/', auth_views.LoginView.as_view(template_name='footprint/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('register/', footprint_views.register, name='register'),
]