from django.urls import path

from . import views

app_name = "plots"

urlpatterns = [
    path("", views.index, name="index"),
    path("create", views.create, name="create"),
    path("<int:p_id>", views.update, name="update"),
    path("<int:p_id>/delete", views.delete, name="delete"),
]
