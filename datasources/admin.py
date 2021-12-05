from django.contrib import admin

from .models import Assembly, Chromosome, Species

admin.site.register(Species)
admin.site.register(Assembly)
admin.site.register(Chromosome)
