__author__ = 'Simon Ruffle'

from django.forms import ModelForm
from django.shortcuts import render
from django.db.models import get_model
from weblib.baseclasses.pagebase import Pagebase
from threatengine.models import Threatclass, Threattype
from django.http import HttpResponseRedirect
from datetime import datetime
from weblib.models import Link

template_dir = 'threatclass/templates/'

appname = 'threatengine'
modelname = 'threatclass'


class ThreatClassForm (ModelForm):
    class Meta:
        model = Threatclass
        fields = ('image1', 'displayidentifier', 'name',  'subtitle', 'introtext' ,)

class ThreatTypeList (ModelForm):
    class Meta:
        model = Threattype
        fields = ('image1', 'displayidentifier', 'name',  'subtitle', )

class LinksListForm (ModelForm):
    class Meta:
        model = Link
        fields = ('url', 'name',  'subtitle', )

class BooksListForm (ModelForm):
    class Meta:
        model = Link
        fields = ('url', 'name',  'subtitle', 'year', )

class ThreatclassView (Pagebase):

    template_name = template_dir + "threatclass.html"

    def dispatch(self, request, *args, **kwargs):

        if self.preProcessPage(request, **kwargs):

            ix = kwargs.get('ix')

            current_object = Threatclass.objects.get(pk=ix)
            page_title = current_object.name
            page_subtitle = current_object.subtitle
            newssearchterms = current_object.newssearchterms
            shortname = current_object.shortname
            sources = current_object.sourcestext.replace('\n', '<br />')

            # display threat class
            pageFormDisplay = ThreatClassForm (instance=current_object)
            threatclassfields = self.createFormFieldStructure( pageFormDisplay, current_object )

            # intercept the field structure dictionary for "image1" field and change the type to WebLibPhoto and provide the photo size
            # this only affects generictablerenderer so is only for display
            index = 0
            for i in pageFormDisplay.visible_fields():
                if i.name == 'image1':
                    break
                index = index + 1
            threatclassfields['fields'][index][0]['image1']['type'] = 'WebLibPhoto'
            threatclassfields['fields'][index][0]['image1']['photosize'] = 'admin_thumbnail'

            # the threat types list
            threattypesqueryset = Threattype.objects.filter(threatclassid=str(ix)).only('displayidentifier','image1','name','subtitle').all().order_by('weight')
            threatTypeListForm = ThreatTypeList()
            threattypesfields = self.createListFieldStructure( threatTypeListForm, threattypesqueryset, '/threattype/' )

            # intercept the dictionary for "image1" field and change the type to WebLibPhoto and provide the photo size
            index = 0
            for i in threatTypeListForm.visible_fields():
                if i.name == 'image1':
                    break
                index = index + 1
            threattypesfields['fields'][index][0]['image1']['type'] = 'WebLibPhoto'
            threattypesfields['fields'][index][0]['image1']['photosize'] = 'threattype_icon'

            # the Links list - we use display order to split the links into two lists. Links are display order <100
            linkslistqueryset = Link.objects.filter(parentid=str(ix)).filter(parenttype=modelname).filter(displayorder__lt=100).only('url','name','subtitle').all().order_by('displayorder')
            linksListForm = LinksListForm()
            linkslistfields = self.createListFieldStructure( linksListForm, linkslistqueryset, 'none' )

            # the Books list - we use display order to split the links into two lists. Books are display order >100
            bookslistqueryset = Link.objects.filter(parentid=str(ix)).filter(parenttype=modelname).filter(displayorder__gt=100).only('url','name','subtitle').all().order_by('displayorder')
            booksListForm = BooksListForm()
            bookslistfields = self.createListFieldStructure( booksListForm, bookslistqueryset, 'none' )


            # using a class dictionary from Pagebase in weblib
            self.page_context['ix'] = ix
            self.page_context['page_title'] = page_title
            self.page_context['page_subtitle'] = page_subtitle
            self.page_context['tablesetup1'] = threatclassfields
            self.page_context['typeslist'] = threattypesfields
            self.page_context['linkslist'] = linkslistfields
            self.page_context['linkscount'] = linkslistqueryset.count()
            self.page_context['bookslist'] = bookslistfields
            self.page_context['bookscount'] = bookslistqueryset.count()
            self.page_context['newssearchterms'] = newssearchterms
            self.page_context['shortname'] = shortname
            self.page_context['sources'] = sources
            self.page_context['pageclass'] = appname + '-' + modelname
            self.page_context['editlink'] = '/' + modelname + '/' + str(ix)
            self.page_context['current_object'] = current_object





            ###############
            # POST
            ###############

            if request.method == 'POST':
                pageFormEdit = ThreatClassForm(request.POST, instance=current_object , prefix='mainpageform') # A form bound to the POST data, prefix allows multiple forms
                if pageFormEdit.is_valid(): # All validation rules pass

                    current_object.lastupdate = datetime.now()
                    current_object.lastupdatebyid = request.user.id
                    pageFormEdit.save()

                    return HttpResponseRedirect('/threatclass/' + str(ix)) # Redirect after successful POST to the non editing version
                else:
                    self.page_context['form'] = pageFormEdit

                    return render(request, self.template_name, self.page_context)  # Error - return just the form when there is an error - the template must not try and render anything outside the form because the contact data is not present


            ###############
            # GET
            ###############

            if request.method == 'GET':

                # edit form
                if self.page_context['editmode']:
                    pageFormEdit = ThreatClassForm (instance=current_object, prefix="mainpageform") #prefix allows multiple forms
                    self.page_context['form'] = pageFormEdit

                return render(request, self.template_name, self.page_context)
