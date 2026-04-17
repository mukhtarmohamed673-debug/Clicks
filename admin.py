from django.contrib import admin
from .models import Product, Category, Customer, Cart, Order

admin.site.register(Product)
admin.site.register(Category)
admin.site.register(Customer)
admin.site.register(Cart)
admin.site.register(Order)