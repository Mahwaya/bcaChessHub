from django.urls import path
from . import views

urlpatterns = [
    path('', views.tournament_list, name='tournament_list'),
    path('<int:pk>/', views.tournament_detail, name='tournament_detail'),
    path('<int:pk>/register/', views.tournament_register, name='tournament_register'),
    path('<int:pk>/standings/', views.tournament_standings, name='tournament_standings'),
    path('<int:pk>/rounds/<int:round_number>/', views.tournament_round, name='tournament_round'),
]
