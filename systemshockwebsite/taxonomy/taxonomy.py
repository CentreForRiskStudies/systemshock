__author__ = 'Simon Ruffle'

from django.forms import ModelForm
from django.shortcuts import render
from django.db.models import get_model
from weblib.baseclasses.pagebase import Pagebase
from weblib.models import Page
from threatengine.models import Threatclass
from django.http import HttpResponseRedirect
from datetime import datetime

template_dir = 'taxonomy/templates/'

appname = 'weblib'
modelname = 'Page'

class PageFormEdit (ModelForm):
    class Meta:
        model = Page
        fields = ('name', 'subtitle', 'introtext', 'maintext',  )

class PageFormDisplay (ModelForm):
    class Meta:
        model = Page
        fields = ( 'introtext', 'maintext', )

class ThreatClassGrid (ModelForm):
    class Meta:
        model = Threatclass
        fields = ('displayidentifier', 'name', 'image1', 'subtitle', )

class TaxonomyPage (Pagebase):

    template_name = template_dir + "taxonomy.html"

    def dispatch(self, request, *args, **kwargs):

        if self.preProcessPage(request, **kwargs):

            ix = 2 # taxonomy page id

            current_object = Page.objects.get(pk=ix)

            page_title = current_object.name
            page_subtitle = current_object.subtitle

            pageForm = PageFormDisplay (instance=current_object)
            pagefields = self.createFormFieldStructure( pageForm, current_object )

            # the threat class grid
            threatclassqueryset = Threatclass.objects.only('displayidentifier','image1','name','subtitle').all().order_by('weight')
            threatClassGridForm = ThreatClassGrid()
            threatclassgrid = self.createListFieldStructure( threatClassGridForm, threatclassqueryset, '/threatclass/' )

            # intercept the dictionary for "image1" field and change the type to WebLibPhoto and provide the photo size
            index = 0
            for i in threatClassGridForm.visible_fields():
                if i.name == 'image1':
                    break
                index = index + 1
            threatclassgrid['fields'][index][0]['image1']['type'] = 'WebLibPhoto'
            threatclassgrid['fields'][index][0]['image1']['photosize'] = 'taxonomy_grid'

            # using a class dictionary from Pagebase in weblib
            self.page_context['ix'] = ix
            self.page_context['page_title'] = page_title
            self.page_context['page_subtitle'] = page_subtitle
            self.page_context['tablesetup1'] = pagefields
            self.page_context['tablesetupgrid'] = threatclassgrid
            self.page_context['pageclass'] = 'taxonomy'
            self.page_context['editlink'] = '/taxonomy'

            ###############
            # POST
            ###############

            if request.method == 'POST':
                pageFormEdit = PageFormEdit(request.POST, instance=current_object , prefix='mainpageform') # A form bound to the POST data, prefix allows multiple forms
                if pageFormEdit.is_valid(): # All validation rules pass

                    current_object.lastupdate = datetime.now()
                    current_object.lastupdatebyid = request.user.id
                    pageFormEdit.save()

                    return HttpResponseRedirect('/taxonomy') # Redirect after successful POST to the non editing version
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

