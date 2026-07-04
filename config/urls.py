from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from core.views import home
from members.views import dashboard

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('tournaments/', include('tournaments.urls')),
    path('associations/', include('associations.urls')),
    path('rankings/', include('members.urls')),
    path('dashboard/', dashboard, name='dashboard'),
    path('matches/', include('matches.urls')),
    path('payments/', include('payments.urls')),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
