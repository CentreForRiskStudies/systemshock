__author__ = 'Simon Ruffle'

from django.contrib import admin
from modellingengine.models import Run
from modellingengine.fincat.models import FinCatRun

admin.site.register(Run)
admin.site.register(FinCatRun)

