from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory, TestCase
from django.urls import reverse
from model_bakery import baker

from menu.models import Item, MenuType, SubMenuType
from service.views import MenuWaiterView


class MenuWaiterViewTest(TestCase):
    ENDPOINT = reverse("service:menu-waiter")
    VIEW_CLASS = MenuWaiterView

    @classmethod
    def setUpTestData(cls):
        baker.make("menu.Item", _quantity=5, menu=MenuType.MAIN)
        baker.make(
            "menu.Item", _quantity=3, menu=MenuType.DRINK, sub_menu=SubMenuType.COFFEE
        )
        baker.make(
            "menu.Item", _quantity=2, menu=MenuType.DRINK, sub_menu=SubMenuType.TEA
        )

        cls.ITEM_MAIN = Item.objects.filter(menu=MenuType.MAIN)
        cls.ITEM_DRINK = Item.objects.filter(menu=MenuType.DRINK)

    def setUp(self):
        self.factory = RequestFactory()

    def test_check_db(self):
        """Simple test verify that all object in table are created"""
        self.assertEqual(Item.objects.count(), 10)

    def test_get(self):
        response = self.client.get(self.ENDPOINT)
        self.assertEqual(response.status_code, 200)
        # self.assertTemplateUsed(response, self.VIEW_CLASS.template_name)

    def test_verify_context_manager(self):
        request = self.factory.get(self.ENDPOINT, {"category": MenuType.DRINK.value})

        view = self.VIEW_CLASS()
        view.setup(request)
        ctx = view.get_context_data(object_list=view.get_queryset())

        sub_menu_groups = ctx["sub_menu_groups"]

        self.assertEqual(len(sub_menu_groups), 2)
        self.assertEqual(sub_menu_groups[SubMenuType.COFFEE.value].count(), 3)
        self.assertEqual(sub_menu_groups[SubMenuType.TEA.value].count(), 2)

        self.assertEqual(ctx["items_no_sub"].count(), 0)

    def test_mock_should_prepare_context_for_main_category_when_category_is_invalid(
        self,
    ):
        wrong_category = "test"
        request = self.factory.get(self.ENDPOINT, {"category": wrong_category})

        # CHEAT Django tha thought that MessageMiddleware is already turn on
        request.session = {}
        messages = FallbackStorage(request)
        setattr(request, "_messages", messages)
        ######

        view = self.VIEW_CLASS()
        view.setup(request)
        ctx = view.get_context_data(object_list=view.get_queryset())

        self.assertEqual(ctx["selected_category"], wrong_category)
        self.assertEqual(ctx["object_list"].count(), self.ITEM_MAIN.count())

        stored_message = list(get_messages(request))
        self.assertEqual(len(stored_message), 1)
        self.assertEqual(stored_message[0].message, "Invalid category: test")
