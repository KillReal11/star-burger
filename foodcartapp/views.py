from django.db import transaction
from django.http import JsonResponse
from django.templatetags.static import static
from phonenumber_field.modelfields import PhoneNumberField
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.serializers import CharField, ModelSerializer

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


class OrderItemSerializer(ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["product", "quantity"]


class OrderSerializer(ModelSerializer):
    firstname = CharField(source="first_name")
    lastname = CharField(source="last_name")
    products = OrderItemSerializer(many=True, allow_empty=False, write_only=True)

    class Meta:
        model = Order
        fields = ["id", "firstname", "lastname", "phonenumber", "address", "products"]


@api_view(["POST"])
def register_order(request):
    serializer = OrderSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    positions = serializer.validated_data["products"]

    with transaction.atomic():
        order = Order.objects.create(
            first_name=serializer.validated_data["first_name"],
            last_name=serializer.validated_data["last_name"],
            phonenumber=serializer.validated_data["phonenumber"],
            address=serializer.validated_data["address"],
        )

        OrderItem.objects.bulk_create(
            [
                OrderItem(
                    order=order,
                    product=position["product"],
                    quantity=position["quantity"],
                    price=position["product"].price,
                )
                for position in positions
            ]
        )

    return Response(OrderSerializer(order).data, status=201)
