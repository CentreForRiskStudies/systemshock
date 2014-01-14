__author__ = 'Simon Ruffle'

from django.shortcuts import render
from django.db.models import get_model
from weblib.baseclasses.pagebase import Pagebase
from django.forms import ModelForm
from assetengine.models import Node, Edge
from django.http import HttpResponseRedirect
from datetime import datetime
from django.core.exceptions import ObjectDoesNotExist

appname = 'assetengine'
modelname = 'Node'
formphotosize = 'admin_thumbnail'

editfields = {'include': ('name', 'guid', 'layerid', 'activity', 'organisation', 'place', 'country',  ), 'exclude': None}
displayfields = {'include': ('name', 'guid', 'layerid', 'activity', 'organisation', 'place', 'country',  ), 'exclude': None}

template_dir = 'node/templates/'

class PageFormEdit (ModelForm):
    class Meta:
        model = Node
        fields = editfields['include']
        exclude = editfields['exclude']


class PageFormDisplay (ModelForm):
    class Meta:
        model = Node
        fields = displayfields['include']
        exclude = displayfields['exclude']


class BasicPage (Pagebase):

    template_name = template_dir + "nodepage.html"

    def dispatch(self, request, *args, **kwargs):

        if self.preProcessPage(request, **kwargs):

            current_object = None

            if not self.page_context['addmode']:  # we are reading an existing record
                try:
                    current_object = Node.objects.get(pk=self.page_context['ix'])
                except ObjectDoesNotExist:
                    return self.showErrorPage(request, 'Error: Record ' + str(self.page_context['ix']) + ' does not exist')
                except:
                    return self.showErrorPage(request, 'Error: invalid parameter supplied')

                self.page_context['current_object'] = current_object
                self.page_context['page_title'] = current_object.name
                if hasattr(current_object,'subtitle'):
                    self.page_context['page_subtitle'] = current_object.subtitle
                if hasattr(current_object,'righttext'):
                    self.page_context['righttext'] = current_object.righttext

                # display
                pageFormDisplay = PageFormDisplay (instance=current_object)
                pagefields = self.createFormFieldStructure( pageFormDisplay, current_object )

                # intercept the field structure dictionary for "image1" field and
                # change the type to WebLibPhoto and provide the photo size
                # this only affects generictablerenderer so is only for display
                index = 0
                for i in pageFormDisplay.visible_fields():
                    if i.name == 'image1':
                        pagefields['fields'][index][0]['image1']['type'] = 'WebLibPhoto'
                        pagefields['fields'][index][0]['image1']['photosize'] = formphotosize
                        break
                    index += 1

                self.page_context['tablesetup1'] = pagefields  #pass field structure to generictablerenderer

            # other info to pass through the page context
            self.page_context['pageclass'] = 'basicpage'
            self.page_context['editlink'] = ('/node/' + str(self.page_context['ix'])).lower()


            ###############
            # POST
            ###############
            if request.method == 'POST':

                if self.page_context['addmode']:
                    # new record, create at first with default values
                    current_object = Node()
                    current_object.name = 'untitled'
                    current_object.lastupdate = datetime.now()
                    current_object.lastupdatebyid = request.user.id
                    current_object.ownerid = request.user.id
                    self.page_context['editmode'] = True  # in case it turns out there is an error in input

                # Create a form bound to the POST data, prefix allows multiple forms
                pageFormEdit = PageFormEdit(request.POST, instance=current_object , prefix='mainpageform')
                if pageFormEdit.is_valid():
                    # All validation rules pass
                    self.page_context['editmode'] = False  # no errors

                    if self.page_context['addmode']:
                        # if in add mode, now create the actual record in the database
                        current_object.save()

                        # now we know the new record's id
                        self.page_context['ix'] = current_object.id
                        self.page_context['current_object'] = current_object

                    current_object.lastupdate = datetime.now()
                    current_object.lastupdatebyid = request.user.id

                    # save the user input from the form to the record
                    pageFormEdit.save()

                    # Redirect after successful POST to the display version of the page
                    return HttpResponseRedirect('/node/' + str(self.page_context['ix']))
                else:
                    # Validation Error - return just the form when there is an error -
                    # the template must not try and render anything outside the form
                    # because the context data is not present
                    self.page_context['form'] = pageFormEdit
                    return render(request, self.template_name, self.page_context)


            ###############
            # GET
            ###############
            if request.method == 'GET':

                # edit mode
                if self.page_context['addmode']:
                    # new record - initialise a dummy record (that we dont save into the database)
                    # with the defaults to see on the new form
                    current_object = Node()
                    current_object.name = 'untitled'
                    self.page_context['editmode'] = True

                if self.page_context['editmode']:  # edit or add mode
                    # Create the form for either the new dummy record or an existing one; prefix allows multiple forms
                    pageFormEdit = PageFormEdit (instance=current_object, prefix="mainpageform")
                    self.page_context['form'] = pageFormEdit

                return render(request, self.template_name, self.page_context)
