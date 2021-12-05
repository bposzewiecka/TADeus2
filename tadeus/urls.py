from django.urls import path
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    path('', views.index, name='index'),


    path('plots/', views.plots, name='plots'),
    path('plots/add', views.create_plot, name='create_plot'),
    path('plots/plot/<int:p_id>', views.edit_plot, name='edit_plot'),
    path('plots/plot/delete/<int:p_id>', views.delete_plot, name='delete_plot'),
    path('plots/plot/<int:p_plot_id>/add_track/', views.create_track, name='create_track'),

    path('track/<int:p_id>', views.edit_track, name='track'),
    path('track/delete/<int:p_id>', views.delete_track, name='delete_track'),


]


