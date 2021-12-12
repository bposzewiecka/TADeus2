from django.urls import path

from . import views

app_name = "evaluation"

urlpatterns = [
    path("", views.index, name="index"),
    path("create/<p_type>", views.create, name="create"),
    path("<int:p_id>", views.update, name="update"),
    path("<int:p_id>/delete", views.delete, name="delete"),
    path("<int:p_id>/show", views.show, name="show_evaluation"),
    path("<int:p_id>/add", views.add_entry, name="add_entry"),
    path("<int:p_id>/delete_ebtry", views.delete_entry, name="delete_entry"),
]
