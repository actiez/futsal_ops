from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from accounts.views import RegisterView, PlayerHomeView, CustomLoginView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("dashboard.urls")),
    path("events/", include("events.urls")),
    path("registrations/", include("registrations.urls")),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="login"), name="logout"),
    path("register/", RegisterView.as_view(), name="register"),
    path("home/", PlayerHomeView.as_view(), name="player_home"),
    
]