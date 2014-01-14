__author__ = 'Simon Ruffle'

# "page package" for locations, contains several pages all to do with locations

from django.shortcuts import render
from django.db.models import get_model
from weblib.baseclasses.pagebase import Pagebase

from django.views.generic import ListView
from django.views.generic import View
from django.views.generic.base import TemplateView

appname = 'laptopsupplychaindemo'
modelname = 'Laptopnode'
template_dir = 'locations/templates/'
def current_model():
    return get_model (appname,modelname)

def locations_list(request):

    tablesetup = {
        'queryset':    current_model().objects.all().order_by('id'),
        'fields':   ['id','location','country','place','activity','organisation',],
        }

    template= template_dir + "locations.html"
    return render(request, template, dict(tablesetup1 = tablesetup))


def locations_view(request,ix):

    location_name = current_model().objects.get(pk=ix).place

    tablesetup = {
        'queryset':    current_model().objects.get(pk=ix),
        'fields':   ['id','location','country','place','activity','organisation',],
        }

    tablesetup2 = {
        'queryset':    current_model().objects.all().order_by('activity'),
        'fields':   ['id','location','country','place','activity','organisation',],
        }

    template= template_dir +  "locations_view.html"
    return render(request, template, dict(ix = ix, tablesetup1 = tablesetup, tablesetup2 = tablesetup2, location_name = location_name))


# using class based Generic Views - same as above but use locations/view/17 not locations/17

from django import forms
from django.http import HttpResponseRedirect

class MyForm(forms.Form):
    name = forms.CharField()
    name.label = "Type the id of the record you want to view"

class LocationsView (Pagebase):

    template_name = template_dir + "locations_view.html"

    def get(self, request, *args, **kwargs):

        form_class = MyForm

        ix = kwargs.get('ix')

        location_name = current_model().objects.get(pk=ix).place

        tablesetup1 = {
            'queryset':    current_model().objects.get(pk=ix),
            'fields':   ['id','location','country','place','activity','organisation',],
            }

        tablesetup2 = {
            'queryset':    current_model().objects.all().order_by('activity'),
            'fields':   ['id','location','country','place','activity','organisation',],
            }

        # using a class dictionary from Pagebase in weblib
        self.page_context['ix'] = ix
        self.page_context['tablesetup1'] = tablesetup1
        self.page_context['tablesetup2'] = tablesetup2
        self.page_context['location_name'] = location_name
        self.page_context['form'] = form_class

        return render(request, self.template_name, self.page_context)

    def send_email(self):
        # send email using the self.cleaned_data dictionary
        pass

    def post(self, request, *args, **kwargs):
        form = MyForm(request.POST) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
            name = form.cleaned_data['name']
            return HttpResponseRedirect('/locations/view/' + name) # Redirect after POST
        else:
            return HttpResponseRedirect('/locations/view/1') # Redirect after POST










#this is using ListView but maybe this does not give us the ability to use custom tags?

class LocationsList (ListView):
    queryset = current_model().objects.filter(activity='Gold').order_by('place')
    template_name = template_dir + "locationstest.html"

    # if you replace ListView with just View you need to add this:
    #def get(self, request, *args, **kwargs):
    #    return render(request, self.template_name, dict(object_list=['hello world']))

    # if you replace ListView with TemplateView you need to add this
    #def get_context_data(self, *args, **kwargs):
    #    context = super(LocationsList, self).get_context_data(**kwargs)
    #    context['object_list'] = ['hello world']
    #    return context


#see https://docs.djangoproject.com/en/dev/ref/class-based-views/
#see https://docs.djangoproject.com/en/dev/ref/class-based-views/base/#templateview
# and https://docs.djangoproject.com/en/dev/topics/class-based-views/generic-display/

