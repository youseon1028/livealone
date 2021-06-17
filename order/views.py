from django.shortcuts import render, get_object_or_404
from .models import *
from cart.cart import Cart
from .forms import *

# JavaScript가 동작하지 않는 환경에서도 주문은 가능해야 함
def order_create(request):
    cart = Cart(request)
    if request.method == 'POST': #입력받은 정보를 후처리 하는 부분
        form = OrderCreateForm(request.POST) # 입력받은 정보를 넣어서 form 생성
        if form.is_valid():
            order = form.save()
            if cart.coupon:
                order.coupon = cart.coupon
                order.discount = cart.coupon.amount
                order.save()

            for item in cart:
                OrderItem.objects.create(order=order, product=item['product'], price=item['price'], quantity=item['quantity'])

            cart.clear()

            return render(request, 'order/created.html', {'order':order})
    else: # 주문자 정보를 입력받는 페이지
            form = OrderCreateForm()

    return render(request, 'order/create.html', {'cart':cart, 'form':form})

# JavaScript가 동작하지 않는 환경에서도 주문은 가능해야 함
def order_complete(request):
    order_id = request.GET.get('order_id') #
    order = Order.objects.get(id=order_id)
    return render(request, 'order/created.html', {'order':order})

from django.views.generic.base import View
from django.http import JsonResponse

# 화면 전환 없이 Javascript를 통해 호출되는 뷰
class OrderCreateAjaxView(View):
    def post(self, request, *args, **kwargs):

        if not request.user.is_authenticated: # 로그인 하지 않은 경우
            return JsonResponse({"authenticated":False}, status=403)

        cart = Cart(request)

        # 아래 부분은 order_create() 부분과 거의 동일
        form = OrderCreateForm(request.POST)

        if form.is_valid():
            order = form.save(commit=False) # database 저장하는 query 보내지 않음
            if cart.coupon:
                order.coupon = cart.coupon
                order.discount = cart.coupon.amount

            order.save() # database에 실제 query가 보내짐

            # order = form.save() # 교재의 코드를 위처럼 변경
            for item in cart:
                OrderItem.objects.create(order=order, product=item['product'], price=item['price'], quantity=item['quantity'])

            cart.clear()

            data = {
                "order_id": order.id
            }
            return JsonResponse(data)

        else:
            return JsonResponse({}, status=401)


class OrderCheckoutAjaxView(View):
    def post(self, request, *args, **kwargs):

        if not request.user.is_authenticated:
            return JsonResponse({"authenticated":False}, status=403)

        order_id = request.POST.get('order_id')
        order = Order.objects.get(id=order_id)
        amount = request.POST.get('amount')

        try:
            # transaction 생성
            merchant_order_id = OrderTransaction.objects.create_new(order=order, amount=amount)
        except:
            merchant_order_id = None

        if merchant_order_id is not None:
            data = {
                "works": True,
                "merchant_id": merchant_order_id
            }
            return JsonResponse(data)
        else:
            return JsonResponse({}, status=401)


class OrderImpAjaxView(View):
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"authenticated":False}, status=403)

        order_id = request.POST.get('order_id')
        order = Order.objects.get(id=order_id)
        merchant_id = request.POST.get('merchant_id')
        imp_id = request.POST.get('imp_id')
        amount = request.POST.get('amount')

        try:
            trans = OrderTransaction.objects.get(
                order=order,
                merchant_order_id=merchant_id,
                amount=amount
            )
        except:
            trans = None

        if trans is not None:
            trans.transaction_id = imp_id
            trans.success = True
            trans.save()

            order.paid = True
            order.save()

            data = {
                "works": True
            }
            return JsonResponse(data)
        else:
            return JsonResponse({}, status=401)

from django.contrib.admin.views.decorators import staff_member_required
@staff_member_required
def admin_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'order/admin/detail.html', {'order':order})

from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string
import weasyprint

@staff_member_required
def admin_order_pdf(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    html = render_to_string('order/admin/pdf.html', {'order':order})
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'filename=order_{}.pdf'.format(order.id)
    weasyprint.HTML(string=html).write_pdf(response, stylesheets=[weasyprint.CSS(str(settings.STATICFILES_DIRS[0])+'/css/pdf.css')])
    return response

