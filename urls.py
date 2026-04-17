from django.urls import path
from .views import (
    Index,
    ProductDetailView,
    Signup,
    Login,
    logout_view,
    CartView,
    CheckOutView,
    OrderView,
    CreateCheckoutSession,
    PaymentSuccess,
)
from .middlewares.auth import auth_middleware

urlpatterns = [
    path('', Index.as_view(), name='homepage'),
    path('product/<int:pk>/', ProductDetailView.as_view(), name='product_detail'),
    path('signup/', Signup.as_view(), name='signup'),
    path('login/', Login.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
    path('cart/', auth_middleware(CartView.as_view()), name='cart'),
    path('checkout/', auth_middleware(CheckOutView.as_view()), name='checkout'),
    path('orders/', auth_middleware(OrderView.as_view()), name='orders'),
    path('create-checkout-session/', auth_middleware(CreateCheckoutSession.as_view()), name='create_checkout_session'),
    path('success/', auth_middleware(PaymentSuccess.as_view()), name='payment_success'),
]