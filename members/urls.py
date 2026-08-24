from django.urls import path
from . import views

urlpatterns = [
    path('', views.rankings, name='rankings'),
    path('signup/', views.signup, name='signup'),
    path('manage/', views.manage_members, name='manage_members'),
    path('admin/stats/', views.admin_stats, name='admin_stats'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/password/', views.change_password, name='change_password'),
    path('2fa/setup/', views.setup_2fa, name='setup_2fa'),
    path('2fa/disable/', views.disable_2fa, name='disable_2fa'),
    path('<int:pk>/', views.player_profile, name='player_profile'),
]
