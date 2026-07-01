from django.urls import path
from . import views

urlpatterns = [
    path('pay/<int:tournament_pk>/', views.initiate_payment, name='payment_initiate'),
    path('callback/', views.paynow_callback, name='paynow_callback'),
    path('return/', views.payment_return, name='payment_return'),
    path('poll/<int:payment_pk>/', views.poll_payment, name='poll_payment'),
    # Sandbox only
    path('sandbox-checkout/<int:payment_pk>/', views.sandbox_checkout, name='sandbox_checkout'),
    path('sandbox-approve/<int:payment_pk>/', views.sandbox_approve, name='sandbox_approve'),
    path('sandbox-poll/<int:payment_pk>/', views.sandbox_poll, name='sandbox_poll'),
]
