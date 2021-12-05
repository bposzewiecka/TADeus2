from django.urls import path

from . import views

app_name = "datasources"

urlpatterns = [
    path('', views.datasources, name='datasources'),
    path('add/<p_type>', views.create_datasource, name='add_datasource'),
    path('<int:p_id>', views.update_datasource, name='update_datasource'),
    path('delete/<int:p_id>', views.delete_datasource, name='delete_datasource'),
    
]


