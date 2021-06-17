from django.shortcuts import render
from django.db.models import Q
from shop.models import Product

def searchResult(request):
    query = None
    products = None

    if 'q' in request.GET:
        query = request.GET.get('q')
        products = Product.objects.all().filter(Q(name__contains=query) | Q(description__contains=query))

    return render(request, 'search_app/search.html', {'query': query, 'products': products})