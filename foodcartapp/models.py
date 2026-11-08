from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Case, IntegerField, Sum, Value, When
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField


class Restaurant(models.Model):
    name = models.CharField("название", max_length=50)
    address = models.CharField(
        "адрес",
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        "контактный телефон",
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = "ресторан"
        verbose_name_plural = "рестораны"

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = RestaurantMenuItem.objects.filter(availability=True).values_list("product")
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField("название", max_length=50)

    class Meta:
        verbose_name = "категория"
        verbose_name_plural = "категории"

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField("название", max_length=50)
    category = models.ForeignKey(
        ProductCategory,
        verbose_name="категория",
        related_name="products",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        "цена", max_digits=8, decimal_places=2, validators=[MinValueValidator(0)]
    )
    image = models.ImageField("картинка")
    special_status = models.BooleanField(
        "спец.предложение",
        default=False,
        db_index=True,
    )
    description = models.TextField(
        "описание",
        max_length=200,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = "товар"
        verbose_name_plural = "товары"

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name="menu_items",
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="menu_items",
        verbose_name="продукт",
    )
    availability = models.BooleanField("в продаже", default=True, db_index=True)

    class Meta:
        verbose_name = "пункт меню ресторана"
        verbose_name_plural = "пункты меню ресторана"
        unique_together = [["restaurant", "product"]]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class OrderQuerySet(models.QuerySet):
    def get_total_cost(self):
        return self.annotate(
            total_cost=Sum(F("items__price") * F("items__quantity"))
        )

    def by_status_priority(self):
        return self.annotate(
            status_priority=Case(
                When(status="new", then=Value(0)),
                When(status="cooking", then=Value(1)),
                When(status="delivering", then=Value(2)),
                When(status="completed", then=Value(3)),
                default=Value(4),
                output_field=IntegerField(),
            )
        ).order_by("status_priority", "-created_at")


class Order(models.Model):
    STATUS = [
        ("new", "Требует подтверждения"),
        ("cooking", "Готовится"),
        ("delivering", "Доставляется"),
        ("completed", "Завершен"),
    ]
    PAYMENT_METHODS = [
        ("unspecified", "Не указан"),
        ("online", "Онлайн"),
        ("cash", "Наличными"),
    ]

    first_name = models.CharField("Имя клиента", max_length=100)
    last_name = models.CharField("Фамилия клиента", max_length=100)
    phonenumber = PhoneNumberField("Телефон клиента", region="RU", db_index=True)
    address = models.TextField("Адрес доставки")
    created_at = models.DateTimeField("Дата создания", default=timezone.now, db_index=True)
    comment = models.TextField("Комментарии к заказу", blank=True)
    called_at = models.DateTimeField("Звонок в", null=True, blank=True, db_index=True)
    delivered_at = models.DateTimeField("Доставлен в", null=True, blank=True, db_index=True)
    status = models.CharField(
        "Статус заказа",
        max_length=40,
        choices=STATUS,
        default="new",
        db_index=True,
    )
    payment_method = models.CharField(
        "Способ оплаты",
        max_length=20,
        choices=PAYMENT_METHODS,
        default="unspecified",
        db_index=True,
    )
    restaurant = models.ForeignKey(
        Restaurant,
        verbose_name="Ресторан - исполнитель",
        related_name="orders",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )
    objects = OrderQuerySet.as_manager()

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"

    def __str__(self):
        return f"Заказ #{self.id} от {self.first_name} {self.last_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        verbose_name="Заказ",
        related_name="items",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        verbose_name="Продукт",
        related_name="order_items",
        on_delete=models.PROTECT,
    )
    quantity = models.PositiveIntegerField("Количество", default=1)
    price = models.DecimalField(
        "Цена на момент заказа",
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )

    class Meta:
        verbose_name = "позиция заказа"
        verbose_name_plural = "позиции заказа"

    def __str__(self):
        return f"{self.product.name} × {self.quantity}"
