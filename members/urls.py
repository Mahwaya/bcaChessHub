from django.urls import path
from . import views

urlpatterns = [
    path('', views.rankings, name='rankings'),
    path('signup/', views.signup, name='signup'),
    path('manage/', views.manage_members, name='manage_members'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/password/', views.change_password, name='change_password'),
    path('<int:pk>/', views.player_profile, name='player_profile'),
]
