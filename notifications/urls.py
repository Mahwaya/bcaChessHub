from django.urls import path
from . import views

urlpatterns = [
    path('', views.notification_centre, name='notification_centre'),
    path('mark-all-read/', views.mark_all_read, name='mark_all_read'),
]
