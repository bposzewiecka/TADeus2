"""tadeus_portal URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import include, path, re_path
from django.contrib import admin


urlpatterns = [

    path('', include('tadeus.urls')),
    path('tracks/', include('tracks.urls')),
    path('help/', include('help.urls')),
    path('plots/', include('plots.urls')),
    path('browser/', include('browser.urls')),
    path('ontologies/', include('ontologies.urls')),
    path('datasources/', include('datasources.urls')),
    path('evaluation/', include('evaluation.urls')),
    
    path('api/ontologies/', include('ontologies.api.urls')),
    #path('api/plots/', include('tadeus.api.urls')),

    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
]

