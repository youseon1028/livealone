from decimal import Decimal
from django.conf import settings
from shop.models import Product
from coupon.models import Coupon

class Cart(object):
    # 초기화, Django view에서 사용한 request로 그 안에 session 정보가 들어있음
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_ID) # settings에 CART_ID를 만들어야함
        if not cart:
            # cart 정보가 없을때는 새로운 dictionary 만들어줌
            cart = self.session[settings.CART_ID] = {}
        self.cart = cart
        self.coupon_id = self.session.get('coupon_id')

    def __len__(self): # 장바구니에 들어있는 제품의 quantity 항목들을 전부 더한 결과 제공
        return sum(item['quantity'] for item in self.cart.values())

    def __iter__(self): # for 문 등 사용할 때 어떤 요소들을 건내줄 것인지 지정
        product_ids = self.cart.keys() # 제품들 번호 목록을 가져옴
        # 장바구니에 들어있는 제품들 정보만 Product database에서 가져옴
        products = Product.objects.filter(id__in=product_ids)

        # 제품들 정보 하나씩 읽어옴
        for product in products:
            # session에 키 값들을 넣을때는 문자로 넣어줌
            self.cart[str(product.id)]['product'] = product

        # 장바구니에 들어있는 제품들을 하나씩 꺼내는 것
        for item in self.cart.values():
            # 제품 가격, Decimal : 숫자형으로 바꿔서 item에 넣어줌
            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['quantity'] # price x item 수

            # Python generator 역할을 함, python 문법 (함수의 return과 유사하나 동작 방식이 조
            yield item

    # 제품 장바구니에 넣기
    # is_update : 제품 정보를 업데이트하는지 아닌지 확인하는 것
    def add(self, product, quantity=1, is_update=False):
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {'quantity':0, 'price':str(product.price)}

        if is_update:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity

        self.save()

    def save(self):
        self.session[settings.CART_ID] = self.cart
        self.session.modified = True

    def remove(self, product):
        product_id = str(product.id)
        if product_id in self.cart:
            del (self.cart[product_id])
            self.save()

    def clear(self):
        self.session[settings.CART_ID] = {}
        self.session['coupon_id'] = None
        self.session.modified = True

    def get_product_total(self):
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())

    @property
    def coupon(self):
        if self.coupon_id:
            return Coupon.objects.get(id=self.coupon_id)
        return None

    def get_discount_total(self):
        if self.coupon:
            if self.get_product_total() >= self.coupon.amount:
                return self.coupon.amount
        return Decimal(0)

    def get_total_price(self):
        return self.get_product_total() - self.get_discount_total()