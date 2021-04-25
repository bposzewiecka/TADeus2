from django.contrib import admin

from .models import Species, Assembly, Chromosome, Plot, Eval

admin.site.register(Species)
admin.site.register(Assembly)
admin.site.register(Chromosome)

admin.site.register(Plot)
admin.site.register(Eval)

