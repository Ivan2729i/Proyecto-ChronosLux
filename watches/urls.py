from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('catalogo/', views.catalog, name='catalog'),
    path('accounts/', include('accounts.urls')),
]
