from django.urls import path
from django.views.generic import TemplateView

from . import views

app_name = 'browser'

urlpatterns = [

    path('image/<int:p_cols>/<int:p_id>/<int:p_width_prop>/<int:p_breakpoint_id>/<int:p_left_side>/<p_chrom>:<p_start>-<int:p_end>', views.image, name='image'),
    path('image/<int:p_cols>/<int:p_id>/<p_chrom>:<p_start>-<int:p_end>', views.image, name='image'),

    path('<int:p_id>', views.browser, name='browser'),
    path('<int:p_id>/<p_chrom>:<int:p_start>-<int:p_end>', views.browser, name='browser'),

]



