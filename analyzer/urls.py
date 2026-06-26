from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('analyze/', views.analyze, name='analyze'),
    path('error/', views.error_page, name='error'),
]
