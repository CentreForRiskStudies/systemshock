__author__ = 'Simon Ruffle'

from django.forms import ModelForm
from django.shortcuts import render
from django.db.models import get_model
from weblib.baseclasses.pagebase import Pagebase
from weblib.models import Page
from django.http import HttpResponseRedirect
from datetime import datetime

template_dir = 'home/templates/'

appname = 'weblib'
modelname = 'Page'

#def current_model():
#    return get_model (appname,modelname)

class PageFormEdit (ModelForm):
    class Meta:
        model = Page
        fields = ('name', 'subtitle', 'introtext',  'maintext', 'righttext'  )

class PageFormDisplay (ModelForm):
    class Meta:
        model = Page
        fields = ( 'introtext',  'maintext', )

class HomePage (Pagebase):

    template_name = template_dir + "home.html"

    def dispatch(self, request, *args, **kwargs):

        if self.preProcessPage(request, **kwargs):

            ix = 1 # home page id

            current_object = Page.objects.get(pk=ix)

            page_title = current_object.name
            page_subtitle = current_object.subtitle
            if current_object.righttext is not None:
                self.page_context['righttext'] = current_object.righttext

            pageForm = PageFormDisplay (instance=current_object)
            pagefields = self.createFormFieldStructure( pageForm, current_object )

            # using a class dictionary from Pagebase in weblib
            self.page_context['ix'] = ix
            self.page_context['page_title'] = page_title
            self.page_context['page_subtitle'] = page_subtitle
            self.page_context['tablesetup1'] = pagefields
            self.page_context['pageclass'] = 'home'
            self.page_context['editlink'] = '/home'

            ###############
            # POST
            ###############

            if request.method == 'POST':
                pageFormEdit = PageFormEdit(request.POST, instance=current_object , prefix='mainpageform') # A form bound to the POST data, prefix allows multiple forms
                if pageFormEdit.is_valid(): # All validation rules pass

                    current_object.lastupdate = datetime.now()
                    current_object.lastupdatebyid = request.user.id
                    pageFormEdit.save()

                    return HttpResponseRedirect('/home') # Redirect after successful POST to the non editing version
                else:
                    self.page_context['form'] = pageFormEdit

                    return render(request, self.template_name, self.page_context)  # Error - return just the form when there is an error - the template must not try and render anything outside the form because the contact data is not present


            ###############
            # GET
            ###############

            if request.method == 'GET':

                # edit form
                if self.page_context['editmode']:
                    pageFormEdit = PageFormEdit (instance=current_object, prefix="mainpageform") #prefix allows multiple forms
                    self.page_context['form'] = pageFormEdit

                return render(request, self.template_name, self.page_context)

