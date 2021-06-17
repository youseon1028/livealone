from django.db import models
from django.urls import reverse

class Category(models.Model):
    name = models.CharField(max_length=200, db_index=True)
    meta_description = models.TextField(blank=True)

    slug = models.SlugField(max_length=200, db_index=True, allow_unicode=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'category'
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('shop:product_in_category', args=[self.slug])

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    name = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(max_length=200, db_index=True, allow_unicode=True)

    image = models.ImageField(upload_to='products/%Y/%m/%d', blank=True)
    description = models.TextField(blank=True)
    meta_description = models.TextField(blank=True)

    # decimal_places는 숫자와 함께 저장할 소수 자릿수를 의미하므로 2를 0으로 바꿔서 소수점을 삭제함
    price = models.DecimalField(max_digits=10, decimal_places=0)
    stock = models.PositiveIntegerField()

    available_display = models.BooleanField('Display', default=True)
    available_order = models.BooleanField('Order', default=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created']
        index_together = [['id', 'slug']]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('shop:product_detail', args=[self.id, self.slug])


class ProductView(models.Model):
    def get(self, request):
        order_condition = request.GET.get('order', None)

        order_by_time = {'recent': 'created_at', 'old': '-created_at'}
        order_by_price = {'min_price': 'discount_price', 'max_price': '-discount_price'}

        if order_condition in order_by_time:
            products = Product.objects.order_by(order_by_time[order_condition])

        if order_condition in order_by_price:
            products = products.extra(
                select={'discount_price': 'original_price * (100 - discount_percentage) / 100'}).order_by(
                order_by_price[order_condition])

