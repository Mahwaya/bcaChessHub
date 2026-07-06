from django.urls import path
from . import views

urlpatterns = [
    path('<int:match_pk>/', views.match_detail, name='match_detail'),
    path('<int:match_pk>/lichess/', views.link_lichess, name='link_lichess'),
    path('challenges/', views.challenge_list, name='challenge_list'),
    path('challenges/send/<int:opponent_pk>/', views.challenge_send, name='challenge_send'),
    path('challenges/<int:challenge_pk>/', views.challenge_detail, name='challenge_detail'),
    path('challenges/<int:challenge_pk>/respond/', views.challenge_respond, name='challenge_respond'),
    path('challenges/<int:challenge_pk>/result/', views.challenge_record_result, name='challenge_record_result'),
]
