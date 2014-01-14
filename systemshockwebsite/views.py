#from django.shortcuts import render
#from django.db.models import get_model
#appname = 'laptopsupplychaindemo'
#modelname = 'Laptopnode'
#def current_model():
#    return get_model (appname,modelname)
#
#def home(request, template="helloworld2.html"):
#
#    tablesetup = {
#        'queryset':    current_model().objects.all(),
#        'fields':   ['id','location','country','place','activity','organisation',],
#        }
#
#    outstr = ''
#    try:
#        x = request.GET.get("x")
#        if x is not None:
#            rec_num = int(x) + 25003
#
#        outstr = str(rec_num)
#
#
#        # using associative arrays to pass arguments to the table viewer custom tag:
#
#
#
#    except BaseException, e:
#        outstr = 'error - must provide an x querystring argument with value 1 - 17 or: ' + str(e)
#    return render(request, template, dict(ix = outstr, tablesetup1 = tablesetup))
