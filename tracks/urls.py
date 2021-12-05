from django.urls import path

from . import views

app_name = 'tracks'

urlpatterns = [
    path('', views.index, name='index'),
    path('<int:p_id>', views.edit, name='edit'),
    path('delete/<int:p_id>', views.delete, name='delete'),
]


