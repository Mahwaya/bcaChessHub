from django.urls import path
from . import views

urlpatterns = [
    path('', views.rankings, name='rankings'),
    path('signup/', views.signup, name='signup'),
    path('<int:pk>/', views.player_profile, name='player_profile'),
]
