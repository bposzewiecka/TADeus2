from django.contrib import admin


from .models import Species, Assembly, Chromosome

admin.site.register(Species)
admin.site.register(Assembly)
admin.site.register(Chromosome)