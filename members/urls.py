from django.urls import path
from . import views

urlpatterns = [
    path('', views.rankings, name='rankings'),
    path('signup/', views.signup, name='signup'),
]
