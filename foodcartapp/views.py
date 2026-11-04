import json

from django.http import JsonResponse
from django.templatetags.static import static

from phonenumber_field.phonenumber import PhoneNumber

from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Order, OrderItem, Product


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse(
        [
            {
                "title": "Burger",
                "src": static("burger.jpg"),
                "text": "Tasty Burger at your door step",
            },
            {
                "title": "Spices",
                "src": static("food.jpg"),
                "text": "All Cuisines",
            },
            {
                "title": "New York",
                "src": static("tasty.jpg"),
                "text": "Food is incomplete without a tasty dessert",
            },
        ],
        safe=False,
        json_dumps_params={
            "ensure_ascii": False,
            "indent": 4,
        },
    )


def product_list_api(request):
    products = Product.objects.select_related("category").available()

    dumped_products = []
    for product in products:
        dumped_product = {
            "id": product.id,
            "name": product.name,
            "price": product.price,
            "special_status": product.special_status,
            "description": product.description,
            "category": {
                "id": product.category.id,
                "name": product.category.name,
            }
            if product.category
            else None,
            "image": product.image.url,
            "restaurant": {
                "id": product.id,
                "name": product.name,
            },
        }
        dumped_products.append(dumped_product)
    return JsonResponse(
        dumped_products,
        safe=False,
        json_dumps_params={
            "ensure_ascii": False,
            "indent": 4,
        },
    )


@api_view(["POST"])
def register_order(request):
    data = request.data
    products = data.get("products")

    if not isinstance(products, list) or not products:
        return Response({"error": "Поле products должно быть непустым списком"}, status=400)

    for order_field in ('firstname', 'lastname', 'phonenumber', 'address'):
        order_field_value = data.get(order_field)
        if not isinstance(order_field_value, str) or not order_field_value.strip():
            return Response({"error": f"Поле {order_field} обязательно и должно быть непустой строкой"}, status=400)

    phonenumber = PhoneNumber.from_string(data.get("phonenumber"), region='RU')
    if not phonenumber.is_valid():
        return Response({"error": "Некорректный номер телефона"}, status=400)

    products_ids = {product.get("product") for product in products}
    found_products = Product.objects.in_bulk(products_ids)
    missing_products = products_ids - found_products.keys()
    if missing_products:
        return Response({"error": f"Заказ с неcуществующим id продукта: {sorted(missing_products)}"}, status=400)

    order = Order.objects.create(
        first_name=data["firstname"],
        last_name=data["lastname"],
        phonenumber=data["phonenumber"],
        address=data["address"],
    )
    for item in data["products"]:
        product = Product.objects.get(pk=item["product"])
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=item["quantity"],
            price=product.price,
        )
    return Response({"id": order.id}, status=201)
