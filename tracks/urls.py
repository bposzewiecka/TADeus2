from django.urls import path

from . import views

app_name = "tracks"

urlpatterns = [
    path("create/<int:p_plot_id>", views.create, name="create"),
    path("<int:p_id>", views.update, name="update"),
    path("delete/<int:p_id>", views.delete, name="delete"),
    path("fox", views.fox, name="fox"),
]
