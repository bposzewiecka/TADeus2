from django.urls import path
from django.views.generic import TemplateView

from . import views

app_name = 'evaluation'

urlpatterns = [
	path('', views.index, name='index'),
	path('create/<p_type>', views.create, name='create'),
	path('<int:p_id>', views.update, name='update'),
	path('<int:p_id>/delete', views.delete, name='delete'),


	path('<int:p_id>/show', views.show, name='show_evaluation'),
	path('<int:p_id>/add', views.add_entry, name='add_entry'),
]