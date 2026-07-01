from django.urls import path
from . import views

urlpatterns = [
    path('<int:match_pk>/', views.match_detail, name='match_detail'),
    path('<int:match_pk>/lichess/', views.link_lichess, name='link_lichess'),
]
