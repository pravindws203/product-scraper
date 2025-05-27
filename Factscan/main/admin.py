from django.contrib import admin
from .models import ScrappedData

# Register your models here.
@admin.register(ScrappedData)
class ProductsImageAdmin(admin.ModelAdmin):
    list_display = ('name', 'id', 'product_url')