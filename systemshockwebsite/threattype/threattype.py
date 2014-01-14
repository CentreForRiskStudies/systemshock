__author__ = 'Simon Ruffle'

from django.forms import ModelForm
from django.shortcuts import render
from django.db.models import get_model
from weblib.baseclasses.pagebase import Pagebase
from threatengine.models import Threatclass, Threattype
from django.http import HttpResponseRedirect
from datetime import datetime

template_dir = 'threattype/templates/'

appname = 'threatengine'
modelname = 'threattype'

class ThreatTypeForm (ModelForm):
    class Meta:
        model = Threattype
        fields = ('image1', 'threatclassid', 'displayidentifier', 'name',  'subtitle', 'introtext' ,)


class ThreattypeView (Pagebase):

    template_name = template_dir + "threattype.html"

    def dispatch(self, request, *args, **kwargs):

        if self.preProcessPage(request, **kwargs):

            ix = kwargs.get('ix')

            current_object = Threattype.objects.get(pk=ix)
            page_title = current_object.name
            page_subtitle = current_object.subtitle

            # display threat class
            pageFormDisplay = ThreatTypeForm (instance=current_object)
            threattypefields = self.createFormFieldStructure( pageFormDisplay, current_object )

            # intercept the field structure dictionary for "image1" field and change the type to WebLibPhoto and provide the photo size
            # this only affects generictablerenderer so is only for display
            index = 0
            for i in pageFormDisplay.visible_fields():
                if i.name == 'image1':
                    break
                index = index + 1
            threattypefields['fields'][index][0]['image1']['type'] = 'WebLibPhoto'
            threattypefields['fields'][index][0]['image1']['photosize'] = 'threattype_icon'

            # using a class dictionary from Pagebase in weblib
            self.page_context['ix'] = ix
            self.page_context['page_title'] = page_title
            self.page_context['page_subtitle'] = page_subtitle
            self.page_context['tablesetup1'] = threattypefields
            self.page_context['pageclass'] = appname + '-' + modelname
            self.page_context['editlink'] =  '/' + modelname + '/' + str(ix)
            self.page_context['current_object'] = current_object


            ###############
            # POST
            ###############

            if request.method == 'POST':
                pageFormEdit = ThreatTypeForm(request.POST, instance=current_object , prefix='mainpageform') # A form bound to the POST data, prefix allows multiple forms
                if pageFormEdit.is_valid(): # All validation rules pass

                    current_object.lastupdate = datetime.now()
                    current_object.lastupdatebyid = request.user.id
                    pageFormEdit.save()

                    return HttpResponseRedirect('/threattype/' + str(ix)) # Redirect after successful POST to the non editing version
                else:
                    self.page_context['form'] = pageFormEdit

                    return render(request, self.template_name, self.page_context)  # Error - return just the form when there is an error - the template must not try and render anything outside the form because the contact data is not present


            ###############
            # GET
            ###############

            if request.method == 'GET':

                # edit form
                if self.page_context['editmode']:
                    pageFormEdit = ThreatTypeForm (instance=current_object, prefix="mainpageform") #prefix allows multiple forms
                    self.page_context['form'] = pageFormEdit

                return render(request, self.template_name, self.page_context)

