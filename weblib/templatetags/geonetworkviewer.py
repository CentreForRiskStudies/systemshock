__author__ = 'Simon Ruffle'

from django.template import Library

register = Library()

@register.inclusion_tag ('geonetworkviewer.html', takes_context=True)
def geonetworkviewer(context, viewerstructure):

    return {'STATIC_URL': context['STATIC_URL'], 'editlink': context['editlink'], 'browser': context['browser'],
            'jsonGraph': viewerstructure['jsonGraph'], 'metrics': viewerstructure['metrics'], 'startup': viewerstructure['startup'], 'viewerid': viewerstructure['uniqueid']}

