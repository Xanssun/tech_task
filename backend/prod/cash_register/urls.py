from django.urls import path

from .views import CashMachineAPIView

app_name = 'cash_register'

urlpatterns = [
    path('cash_machine/', CashMachineAPIView.as_view(), name='cash_machine'),
]
