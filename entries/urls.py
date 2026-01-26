from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("entries/new", views.new_entry, name="new_entry"),
    path("entries", views.create_entry, name="create_entry"),
    path("entries/<int:entry_id>/edit", views.edit_entry, name="edit_entry"),
    path("entries/<int:entry_id>/delete", views.delete_entry, name="delete_entry"),
    path("login", views.login_view, name="login"),
    path("auth/redirect", views.authorized, name="authorized"),
    path("logout", views.logout_view, name="logout"),
]
