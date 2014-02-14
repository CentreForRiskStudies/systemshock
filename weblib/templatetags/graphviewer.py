__author__ = 'Simon Ruffle'

from django.template import Library

register = Library()

@register.inclusion_tag ('graphviewer.html', takes_context=True)
def graphviewer(context, viewerstructure):

    # some keys may be absent - set the defaults values here
    if 'metrics' not in viewerstructure:
        viewerstructure['metrics'] = {}
    if 'startup' not in viewerstructure:
        viewerstructure['startup'] = {}
    if 'maptype' not in viewerstructure:
        viewerstructure['maptype'] = 'event'
    if 'epicentre' not in viewerstructure:
        viewerstructure['epicentre'] = [0, 0]
    if 'zoomtoextent' not in viewerstructure:
        viewerstructure['zoomtoextent'] = False
    if 'classname' not in viewerstructure:
        viewerstructure['classname'] = ''
    if 'markershape' not in viewerstructure:
        viewerstructure['markershape'] = 'circle'
    if 'markersize' not in viewerstructure:
        viewerstructure['markersize'] = 4
    if 'linkweight' not in viewerstructure:
        viewerstructure['linkweight'] = 1
    if 'ganglist' not in viewerstructure:
        viewerstructure['ganglist'] = []


    return {'STATIC_URL': context['STATIC_URL'], 'editlink': context['editlink'], 'browser': context['browser'],
            'jsonGraph': viewerstructure['jsonGraph'], 'metrics': viewerstructure['metrics'],
            'startup': viewerstructure['startup'], 'viewerid': viewerstructure['uniqueid'],
            'maptype': viewerstructure['maptype'], 'zoomtoextent': viewerstructure['zoomtoextent'],
            'epicentre': viewerstructure['epicentre'], 'classname': viewerstructure['classname'], 'markershape': viewerstructure['markershape'],
            'markersize': viewerstructure['markersize'], 'linkweight': viewerstructure['linkweight'], 'ganglist': viewerstructure['ganglist'], }

