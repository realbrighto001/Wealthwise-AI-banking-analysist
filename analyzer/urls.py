from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('analyze/', views.upload_and_analyze, name='analyze'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('clear/', views.clear_session, name='clear'),
]
