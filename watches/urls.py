from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('catalogo/', views.catalog, name='catalog'),
    path('producto/<int:producto_id>/', views.product_detail, name='product_detail'),
    path('accounts/', include('accounts.urls')),
]
