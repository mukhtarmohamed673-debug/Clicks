from django.db import models
from django.contrib.auth.models import AbstractUser


# ── CUSTOMER ─────────────────────────────────────
class Customer(AbstractUser):
    phone = models.CharField(max_length=15, blank=True)

    def __str__(self):
        return self.username


# ── CATEGORY ─────────────────────────────────────
class Category(models.Model):
    name = models.CharField(max_length=100)

    @staticmethod
    def get_all_categories():
        return Category.objects.all()

    def __str__(self):
        return self.name


# ── PRODUCT ──────────────────────────────────────
class Product(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('unisex', 'Unisex'),
    ]

    name = models.CharField(max_length=120)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)

    # ✅ THIS IS THE IMPORTANT FIELD
    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        default='unisex'
    )

    @staticmethod
    def get_all_products():
        return Product.objects.all()

    @staticmethod
    def get_all_products_by_categoryid(category_id):
        if category_id:
            return Product.objects.filter(category=category_id)
        return Product.get_all_products()

    @staticmethod
    def get_all_products_by_gender(gender):
        if gender:
            return Product.objects.filter(gender=gender)
        return Product.get_all_products()

    def __str__(self):
        return self.name


# ── CART ─────────────────────────────────────────
class Cart(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.product.name} ({self.quantity})"


# ── ORDER ────────────────────────────────────────
class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    address = models.CharField(max_length=200)
    phone = models.CharField(max_length=15)

    date = models.DateTimeField(auto_now_add=True)
    paid = models.BooleanField(default=False)

    def placeOrder(self):
        self.save()

    @staticmethod
    def get_orders_by_customer(customer_id):
        return Order.objects.filter(customer=customer_id).order_by('-date')

    def __str__(self):
        return f"Order {self.id}"