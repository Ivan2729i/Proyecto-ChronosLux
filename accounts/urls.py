from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import HomeLoginView, signup, domicilio_list, domicilio_create, domicilio_edit, domicilio_delete, mis_compras, solicitar_devolucion, mis_devoluciones

urlpatterns = [
    path('login/', HomeLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('signup/', signup, name='signup'),
    path('mis-domicilios/', domicilio_list, name='domicilio_list'),
    path('mis-domicilios/agregar/', domicilio_create, name='domicilio_create'),
    path('mis-domicilios/editar/<int:domicilio_id>/', domicilio_edit, name='domicilio_edit'),
    path('mis-domicilios/eliminar/<int:domicilio_id>/', domicilio_delete, name='domicilio_delete'),
    path('mis-compras/', mis_compras, name='mis_compras'),
    path('mis-compras/devolucion/<int:pedido_id>/', solicitar_devolucion, name='solicitar_devolucion'),
    path('mis-devoluciones/', mis_devoluciones, name='mis_devoluciones'),
]
