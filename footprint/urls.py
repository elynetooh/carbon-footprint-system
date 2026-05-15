from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('dashboard/', views.dashboard, name='dashboard'),

    path('transport/', views.add_transport, name='add_transport'),
    path('energy/', views.add_energy, name='add_energy'),
    path('waste/', views.add_waste, name='add_waste'),
    path('water/', views.add_water, name='add_water'),

    path('download-pdf/', views.download_pdf, name='download_pdf'),

    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('manager-dashboard/', views.manager_dashboard, name='manager_dashboard'),

    path('data-history/', views.data_history, name='data_history'),

    # LOGOUT
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
]