from django.urls import path
from django.views.generic import TemplateView

from . import views

app_name = 'evaluation'

urlpatterns = [
	path('', views.index, name='index'),
	path('eval/add/<p_type>', views.create, name='create'),
	path('eval/<int:p_id>', views.edit, name='update'),
	path('evals/eval/delete/<int:p_id>', views.delete, name='delete'),
	path('evals/eval/<int:p_id>/show', views.show, name='show_evaluation'),
	path('evals/eval/<int:p_id>/add', views.add_entry_eval, name='add_entry'),
]