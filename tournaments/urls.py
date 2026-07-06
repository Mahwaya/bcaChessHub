from django.urls import path
from . import views

urlpatterns = [
    path('', views.tournament_list, name='tournament_list'),
    path('<int:pk>/', views.tournament_detail, name='tournament_detail'),
    path('<int:pk>/register/', views.tournament_register, name='tournament_register'),
    path('<int:pk>/standings/', views.tournament_standings, name='tournament_standings'),
    path('<int:pk>/crosstable/', views.tournament_crosstable, name='tournament_crosstable'),
    path('<int:pk>/rounds/<int:round_number>/', views.tournament_round, name='tournament_round'),
    path('<int:pk>/manage/', views.tournament_manage, name='tournament_manage'),
    path('<int:pk>/manage/result/<int:match_pk>/', views.tournament_record_result, name='tournament_record_result'),
    path('<int:pk>/export/standings/', views.export_standings_csv, name='export_standings'),
    path('<int:pk>/export/pairings/', views.export_pairings_csv, name='export_pairings'),
    path('<int:pk>/export/print/', views.export_print, name='export_print'),
    path('create/', views.create_tournament, name='tournament_create'),
    path('<int:pk>/edit/', views.edit_tournament, name='tournament_edit'),
]
