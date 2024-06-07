from django.urls import path, re_path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("form/<uuid:file_id>", views.form_view, name="form_view"),
    path("form_new_doc", views.form_new_doc_view, name="form_new_doc_view"),
    path("delete_file/<uuid:file_id>/", views.delete_file_view, name="delete_file_view"),
    path("edit_doc/<uuid:file_id>/", views.edit_doc_view, name="edit_doc_view"),
    #rejestracja i logowanie:
    path("register", views.register_view, name="register_view"),
    path("login", views.login_view, name="login_view"),
    path("logout", views.logout_view, name="logout_view"),
]