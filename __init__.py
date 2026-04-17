from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth import authenticate, login, logout
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
import stripe

from store.models import Product, Category, Cart, Order, Customer

stripe.api_key = settings.STRIPE_SECRET_KEY


class Index(View):
    def post(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        product_id = request.POST.get('product')
        if not product_id:
            return redirect('homepage')

        product = get_object_or_404(Product, id=product_id)
        cart_item, created = Cart.objects.get_or_create(
            customer=request.user,
            product=product
        )

        if created:
            cart_item.quantity = 1
        else:
            cart_item.quantity += 1

        cart_item.save()

        next_url = request.POST.get('next_url') or reverse('homepage')
        return redirect(next_url)

    def get(self, request):
        products = Product.objects.select_related('category').all()
        categories = Category.objects.all()

        query = request.GET.get('q', '').strip()
        category_id = request.GET.get('category', '').strip()
        gender = request.GET.get('gender', '').strip()

        if query:
            products = products.filter(name__icontains=query)

        selected_category = None
        if category_id:
            products = products.filter(category_id=category_id)
            selected_category = category_id

        selected_gender = None
        if gender in ['male', 'female']:
            products = products.filter(gender=gender)
            selected_gender = gender

        context = {
            'products': products,
            'categories': categories,
            'selected_category': selected_category,
            'selected_gender': selected_gender,
        }
        return render(request, 'index.html', context)


class ProductDetailView(View):
    def get(self, request, pk):
        product = get_object_or_404(Product.objects.select_related('category'), pk=pk)
        categories = Category.objects.all()
        related_products = Product.objects.filter(category=product.category).exclude(pk=product.pk)[:4]

        context = {
            'product': product,
            'categories': categories,
            'related_products': related_products,
        }
        return render(request, 'product_detail.html', context)


class Signup(View):
    def get(self, request):
        return render(request, 'signup.html')

    def post(self, request):
        data = request.POST
        first_name = data.get('firstname', '').strip()
        last_name = data.get('lastname', '').strip()
        phone = data.get('phone', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')

        error = None
        values = {
            'first_name': first_name,
            'last_name': last_name,
            'phone': phone,
            'email': email,
        }

        if Customer.objects.filter(email=email).exists():
            error = "Email already registered"
        elif not password:
            error = "Password is required"

        if error:
            return render(request, 'signup.html', {'error': error, 'values': values})

        user = Customer.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone=phone
        )
        login(request, user)
        return redirect('homepage')


class Login(View):
    def get(self, request):
        return render(request, 'login.html')

    def post(self, request):
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(username=email, password=password)

        if user:
            login(request, user)
            return redirect(request.GET.get('next', 'homepage'))

        return render(request, 'login.html', {'error': 'Invalid credentials'})


def logout_view(request):
    logout(request)
    return redirect('login')


class CartView(View):
    def get(self, request):
        cart_items = Cart.objects.filter(customer=request.user).select_related('product', 'product__category')
        total = sum(item.product.price * item.quantity for item in cart_items)

        items_list = []
        for item in cart_items:
            items_list.append({
                'product': item.product,
                'quantity': item.quantity,
                'subtotal': item.product.price * item.quantity
            })

        return render(request, 'cart.html', {
            'cart_items': items_list,
            'total': total
        })

    def post(self, request):
        product_id = request.POST.get('product')
        action = request.POST.get('action')
        qty = int(request.POST.get('quantity', 1))

        if product_id:
            product = get_object_or_404(Product, id=product_id)
            cart_item, _ = Cart.objects.get_or_create(
                customer=request.user,
                product=product
            )

            if action == 'remove':
                cart_item.delete()
            elif action == 'update':
                if qty > 0:
                    cart_item.quantity = qty
                    cart_item.save()
                else:
                    cart_item.delete()
            else:
                cart_item.quantity += 1
                cart_item.save()

        return redirect('cart')


class CheckOutView(View):
    def get(self, request):
        cart_items = Cart.objects.filter(customer=request.user).select_related('product')
        if not cart_items.exists():
            return redirect('cart')

        total = sum(item.product.price * item.quantity for item in cart_items)
        items_list = [
            {
                'product': item.product,
                'quantity': item.quantity,
                'subtotal': item.product.price * item.quantity
            }
            for item in cart_items
        ]

        return render(request, 'checkout.html', {
            'cart_items': items_list,
            'total': total
        })

    def post(self, request):
        address = request.POST.get('address', '').strip()
        phone = request.POST.get('phone', '').strip()

        if not address or not phone:
            return redirect('checkout')

        request.session['checkout_info'] = {
            'address': address,
            'phone': phone
        }
        return redirect('create_checkout_session')


class CreateCheckoutSession(View):
    def get(self, request):
        return self.post(request)

    def post(self, request):
        cart_items = Cart.objects.filter(customer=request.user).select_related('product')
        if not cart_items.exists():
            return redirect('cart')

        line_items = []
        for item in cart_items:
            line_items.append({
                'price_data': {
                    'currency': 'gbp',
                    'product_data': {
                        'name': item.product.name,
                    },
                    'unit_amount': int(item.product.price * 100),
                },
                'quantity': item.quantity,
            })

        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=request.build_absolute_uri(reverse('payment_success')),
            cancel_url=request.build_absolute_uri(reverse('cart')),
        )

        return redirect(session.url, code=303)


class PaymentSuccess(View):
    def get(self, request):
        cart_items = Cart.objects.filter(customer=request.user).select_related('product')
        info = request.session.get('checkout_info', {})
        address = info.get('address', '')
        phone = info.get('phone', '')

        for item in cart_items:
            Order.objects.create(
                customer=request.user,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price,
                address=address,
                phone=phone,
                paid=True
            )

        cart_items.delete()
        request.session.pop('checkout_info', None)

        html_content = render_to_string(
            'emails/order_confirmation.html',
            {'user': request.user}
        )
        msg = EmailMultiAlternatives(
            "Order Confirmation - Black Is Beauty",
            "Thank you for your order!",
            settings.DEFAULT_FROM_EMAIL,
            [request.user.email]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=True)

        return render(request, 'payment_success.html')


class OrderView(View):
    def get(self, request):
        orders = Order.get_orders_by_customer(request.user.id)
        return render(request, 'orders.html', {'orders': orders})