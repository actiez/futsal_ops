from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import RegisterView, PlayerHomeView, CustomLoginView
from . import views

urlpatterns = [
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(next_page="login"), name="logout"),
    path("register/", RegisterView.as_view(), name="register"),
    path("home/", PlayerHomeView.as_view(), name="player_home"),
    path("profile/", views.profile_view, name="profile"),
    path("users/<int:user_id>/", views.admin_user_profile, name="admin_user_profile"),
]