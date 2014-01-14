__author__ = 'ruffles'

from django.contrib import admin
from threatengine.models import Event,Threatclass,Threattype
from django.forms import TextInput, Textarea
from django.db import models

class SystemShockModelAdmin(admin.ModelAdmin):
    formfield_overrides = \
    {
        #models.CharField: {'widget': TextInput(attrs={'size':'120'})}
    }

admin.site.register(Event, SystemShockModelAdmin)
admin.site.register(Threatclass, SystemShockModelAdmin)
admin.site.register(Threattype, SystemShockModelAdmin)



