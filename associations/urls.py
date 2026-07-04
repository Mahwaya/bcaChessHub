from django.urls import path
from . import views

urlpatterns = [
    path('', views.association_list, name='association_list'),
    path('<int:pk>/', views.association_detail, name='association_detail'),
]
