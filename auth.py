from django.http import HttpResponseRedirect
from django.urls import reverse


def auth_middleware(get_response):
    def middleware(request):
        if not request.user.is_authenticated:
            protected_urls = [
                reverse('cart'),
                reverse('checkout'),
                reverse('orders'),
                reverse('create_checkout_session'),
                reverse('payment_success'),
            ]

            if request.path in protected_urls:
                login_url = reverse('login')
                return HttpResponseRedirect(f'{login_url}?next={request.path}')

        response = get_response(request)
        return response

    return middleware