from django.shortcuts import render, redirect
from storx.models import Product

def home(request):
	products = Product.objects.all().filter(is_available=True)
	
	context = {
		'products': products,
	}
	return render(request, 'pages/index.html', context)
	
#def store(request):
#    return redirect ('storx')
