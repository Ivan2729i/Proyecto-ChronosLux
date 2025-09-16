from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import HomeLoginView, signup

urlpatterns = [
    path('login/', HomeLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('signup/', signup, name='signup'),
]
