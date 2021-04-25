from django.urls import path
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('track_image/<int:p_cols>/<int:p_id>/<int:p_width_prop>/<int:p_breakpoint_id>/<int:p_left_side>/<p_chrom>:<int:p_start>-<int:p_end>', views.image, name='image'),
    path('track_image/<int:p_cols>/<int:p_id>/<p_chrom>:<int:p_start>-<int:p_end>', views.image, name='image'),
    path('browser/<int:p_id>', views.browser, name='browser'),
    path('browser/<int:p_id>/<p_chrom>:<int:p_start>-<int:p_end>', views.browser, name='browser'),
    path('breakpoint_browser/<int:p_id>/<int:p_breakpoint_id>/', views.breakpoint_browser, name='breakpoint_browser'),
    path('plots/', views.plots, name='plots'),
    path('plots/add', views.create_plot, name='create_plot'),
    path('plots/plot/<int:p_id>', views.edit_plot, name='edit_plot'),
    path('plots/plot/delete/<int:p_id>', views.delete_plot, name='delete_plot'),
    path('plots/plot/<int:p_plot_id>/add_track/', views.create_track, name='create_track'),
    path('datasources/', views.datasources, name='datasources'),
    path('datasources/datasource/add/<p_type>', views.create_datasource, name='add_datasource'),
    path('datasources/datasource/<int:p_id>', views.edit_datasource, name='edit_datasource'),
    path('datasources/datasource/delete/<int:p_id>', views.delete_datasource, name='delete_datasource'),
    path('track/<int:p_id>', views.edit_track, name='track'),
    path('track/delete/<int:p_id>', views.delete_track, name='delete_track'),
    path('evals', views.evals, name='evals'),
    path('evals/eval/add/<p_type>', views.create_eval, name='create_eval'),
    path('evals/eval/<int:p_id>', views.edit_eval, name='edit_eval'),
    path('evals/eval/delete/<int:p_id>', views.delete_eval, name='delete_eval'),
    path('evals/eval/<int:p_id>/show', views.show_eval, name='show_eval'),
    path('evals/eval/<int:p_id>/add', views.add_entry_eval, name='eval_add_entry'),
    path('ontologies/<p_db>', views.phenotypes, name='phenotypes'),
    path('ontologies/genes/', views.genes, name='genes'),
    path('ontologies/genes/<int:p_id>', views.gene, name='gene'),
    path('breakpoints/', views.breakpoints, name='breakpoints'),
    
    path('help/sv_evaluation/',  TemplateView.as_view(template_name='tadeus/help/sv_evaluation.html'), name = 'help_sv_evaluation'),
    path('help/plots/', TemplateView.as_view(template_name='tadeus/help/plots.html'), name='help_plots'),
    path('help/datasources/', TemplateView.as_view(template_name='tadeus/help/datasources.html'), name='help_datasources'),
    path('help/genome_browser/', TemplateView.as_view(template_name='tadeus/help/genome_browser.html'), name='help_genome_browser'),
    path('help/ontologies/', TemplateView.as_view(template_name='tadeus/help/ontologies.html'), name='help_ontologies'),

    path('help/about/', TemplateView.as_view(template_name='tadeus/help/about.html'), name = 'help_about'),
]


