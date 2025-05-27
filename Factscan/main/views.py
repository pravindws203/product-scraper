from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import ScrappedData
import json

def product_list(request):
    products = ScrappedData.objects.all()
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'products/product_list.html', {'page_obj': page_obj})

def product_detail(request, id):
    product = get_object_or_404(ScrappedData, id=id)
    main_images = []
    other_images = []
    
    if product.images != "" and product.images is not None:
        images = json.loads(product.images)
        main_images = images.get("image_urls", [])
    
    if product.other_images != "" and product.other_images is not None:
        other = json.loads(product.other_images)
        images = other.get("image_urls", {}).get("images", {})
        other_images = images.get("image_urls", [])
      
    product.images = main_images + other_images
    product.other_images = other_images
    return render(request, 'products/product_detail.html', {'product': product})
