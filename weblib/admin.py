__author__ = 'ruffles'

from django.contrib import admin
from weblib.models import Page, Link, Pagetype, ResourceConnection, Document

admin.site.register(Pagetype)
admin.site.register(Page)
admin.site.register(Link)
admin.site.register(ResourceConnection)
admin.site.register(Document)
