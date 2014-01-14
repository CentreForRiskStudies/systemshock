__author__ = 'Simon Ruffle'

from django.shortcuts import render
from django.db.models import get_model
from weblib.baseclasses.pagebase import Pagebase
from django.forms import ModelForm
from weblib.models import Page, ResourceConnection, Document
from django.http import HttpResponseRedirect
from datetime import datetime
from django.core.exceptions import ObjectDoesNotExist


template_dir = 'page/templates/'

#appname = 'weblib'
#modelname = 'Page'
formphotosize = 'admin_thumbnail'

class PageFormEdit (ModelForm):
    class Meta:
        model = Page
        fields = ('name', 'subtitle', 'introtext', 'image1', 'maintext', 'righttext', 'pagetype', 'nextlink', 'prevlink', )


class PageFormDisplay (ModelForm):
    class Meta:
        model = Page
        fields = ('introtext',  'maintext', )

class WizardFormDisplay (ModelForm):
    class Meta:
        model = Page
        fields = ('introtext', 'image1', 'maintext', )


class DocumentList (ModelForm):
    class Meta:
        model = Document
        fields = ('image1', 'name', 'introtext',)


class PageList (ModelForm):
    class Meta:
        model = Page
        fields = ('image1', 'name', 'subtitle', )

#def current_model():
#    return get_model (appname,modelname)
class BasicPage (Pagebase):

    template_name = template_dir + "basicpage.html"

    def dispatch(self, request, *args, **kwargs):

        if self.preProcessPage(request, **kwargs):

            current_object = None
            wizard = False
            nextbutton = ''
            prevbutton = ''

            if not self.page_context['addmode']:  # we are reading an existing record
                try:
                    current_object = Page.objects.get(pk=self.page_context['ix'])
                except ObjectDoesNotExist:
                    return self.showErrorPage(request, 'Error: Record ' + str(self.page_context['ix']) + ' does not exist')
                except:
                    return self.showErrorPage(request, 'Error: invalid parameter supplied')

                self.page_context['current_object'] = current_object
                self.page_context['page_title'] = current_object.name
                self.page_context['page_subtitle'] = current_object.subtitle
                if current_object.righttext is not None:
                    self.page_context['righttext'] = current_object.righttext

                if current_object.pagetype is not None:
                    if current_object.pagetype.name == "Wizard page":
                        wizard = True
                        if current_object.nextlink is not None:
                            nextbutton = current_object.nextlink
                        if current_object.prevlink is not None:
                            prevbutton = current_object.prevlink
                        formphotosize = 'wizard_image' # note only a wizard displays an in-page image

                # display
                if not wizard:
                    pageFormDisplay = PageFormDisplay (instance=current_object)
                else:
                    pageFormDisplay = WizardFormDisplay (instance=current_object)
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
            self.page_context['wizard'] = wizard
            self.page_context['nextbutton'] = nextbutton
            self.page_context['prevbutton'] = prevbutton
            self.page_context['editlink'] = ('/page/' + str(self.page_context['ix'])).lower()


            ###############
            # POST
            ###############
            if request.method == 'POST':

                if self.page_context['addmode']:
                    # new record, create at first with default values
                    current_object = Page()
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
                    return HttpResponseRedirect('/page/' + str(self.page_context['ix']))
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

                # edit form

                if self.page_context['addmode']:  # new record - initialise a dummy record that we dont save with defaults to see on the page
                    current_object = Page()
                    current_object.name = 'untitled'
                    self.page_context['editmode'] = True

                if self.page_context['editmode']: # edit or add mode
                    pageFormEdit = PageFormEdit (instance=current_object, prefix="mainpageform") #prefix allows multiple forms
                    self.page_context['form'] = pageFormEdit
                else:
                    # compose the lower section of the page based on page type
                    if current_object.pagetype is not None:
                        if current_object.pagetype.containerclass is not None:
                            self.page_context['containerclass'] = current_object.pagetype.containerclass.lower()
                        if current_object.pagetype.listmodel is not None:
                            self.page_context['pagelist'] = {'entity': [], 'targeturl': '', 'fields': [] }

                            # use the ResourceConnection model to identify the linked resources
                            # The Pagetype provides the app and model that we are listing
                            target_model = get_model(current_object.pagetype.listapp, current_object.pagetype.listmodel)
                            connections = ResourceConnection.objects.filter(parentmodel__iexact='Page').filter(parentpk=self.page_context['ix']).filter(childmodel__iexact=current_object.pagetype.listmodel).order_by('timeline')
                            connectionsidlist = [int(connection.childpk) for connection in connections]
                            listitems = target_model.objects.filter(id__in=connectionsidlist)
                            # this horrible bit of Django (which creates a subquery and adds a field to the model) is to copy the timeline from the resource connection model and then order by it
                            listitems = listitems.extra(select={'timeline': "SELECT timeline FROM " + ResourceConnection._meta.db_table + " WHERE lower(parentmodel)='page' AND parentpk=" + self.page_context['ix'] + " AND lower(childmodel)='" + current_object.pagetype.listmodel.lower() + "' AND childpk=" + target_model._meta.db_table + ".id"}).order_by('timeline')

                            if len(listitems) > 0:
                                listForm = None
                                listFields = None

                                self.page_context['listmodel'] = current_object.pagetype.listmodel

                                #########
                                # Document list
                                #########
                                if current_object.pagetype.listmodel.lower() == 'document':
                                    listForm = DocumentList()
                                    listFields = self.createListFieldStructure(listForm, listitems, '' )
                                    # intercept the dictionary for "image1" field and change the type to WebLibPhoto and provide the photo size
                                    index = 0
                                    for i in listForm.visible_fields():
                                        if i.name == 'image1':
                                            break
                                        index = index + 1
                                    listFields['fields'][index][0]['image1']['type'] = 'WebLibPhoto'
                                    listFields['fields'][index][0]['image1']['photosize'] = 'portrait_icon'
                                    self.page_context['pagelist'] = listFields

                                #########
                                # Page list
                                #########
                                if current_object.pagetype.listmodel == 'Page':
                                    listForm = PageList()
                                    listFields = self.createListFieldStructure(listForm, listitems, '/page/' )
                                    # intercept the dictionary for "image1" field and change the type to WebLibPhoto and provide the photo size
                                    index = 0
                                    for i in listForm.visible_fields():
                                        if i.name == 'image1':
                                            break
                                        index = index + 1
                                    listFields['fields'][index][0]['image1']['type'] = 'WebLibPhoto'
                                    listFields['fields'][index][0]['image1']['photosize'] = 'square110'
                                    self.page_context['pagelist'] = listFields

                return render(request, self.template_name, self.page_context)
