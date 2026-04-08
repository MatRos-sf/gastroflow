from django.test import RequestFactory, TestCase
from django.urls import reverse
from model_bakery import baker

from menu.models import Category, Item, SubCategory
from service.views.order_flow.menu import MenuWaiterView


class MenuWaiterViewTest(TestCase):
    ENDPOINT = reverse("service:order-select-items")

    @classmethod
    def setUpTestData(cls):
        cls.category_main = baker.make(Category)
        cls.category_drinks = baker.make(Category)
        cls.sub_coffee = baker.make(SubCategory)
        cls.sub_tea = baker.make(SubCategory)

        baker.make(Item, _quantity=5, category=cls.category_main, is_delete=False)
        baker.make(
            Item,
            _quantity=3,
            category=cls.category_drinks,
            sub_menu=cls.sub_coffee,
            is_delete=False,
        )
        baker.make(
            Item,
            _quantity=2,
            category=cls.category_drinks,
            sub_menu=cls.sub_tea,
            is_delete=False,
        )

    def setUp(self):
        self.factory = RequestFactory()

    def _make_view(self, params=None):
        request = self.factory.get(self.ENDPOINT, params or {})
        view = MenuWaiterView()
        view.setup(request)
        return view

    def test_get_returns_200(self):
        response = self.client.get(self.ENDPOINT)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, MenuWaiterView.template_name)

    def test_queryset_filters_items_by_category(self):
        view = self._make_view({"category": self.category_drinks.pk})
        self.assertEqual(view.get_queryset().count(), 5)  # 3 coffee + 2 tea

    def test_queryset_returns_empty_when_no_categories_exist(self):
        Category.objects.all().delete()
        view = self._make_view()
        self.assertEqual(view.get_queryset().count(), 0)

    def test_context_groups_items_by_sub_menu(self):
        view = self._make_view({"category": self.category_drinks.pk})
        ctx = view.get_context_data(object_list=view.get_queryset())

        sub_menu_groups = ctx["sub_menu_groups"]
        self.assertEqual(len(sub_menu_groups), 2)
        self.assertEqual(sub_menu_groups[self.sub_coffee].count(), 3)
        self.assertEqual(sub_menu_groups[self.sub_tea].count(), 2)

    def test_context_items_no_sub_excludes_items_with_sub_menu(self):
        view = self._make_view({"category": self.category_drinks.pk})
        ctx = view.get_context_data(object_list=view.get_queryset())
        self.assertEqual(ctx["items_no_sub"].count(), 0)

    def test_context_items_no_sub_includes_items_without_sub_menu(self):
        view = self._make_view({"category": self.category_main.pk})
        ctx = view.get_context_data(object_list=view.get_queryset())
        self.assertEqual(ctx["items_no_sub"].count(), 5)
        self.assertEqual(len(ctx["sub_menu_groups"]), 0)

    def test_context_selected_category_matches_requested_category(self):
        view = self._make_view({"category": self.category_drinks.pk})
        ctx = view.get_context_data(object_list=view.get_queryset())
        self.assertEqual(ctx["selected_category"], self.category_drinks)

    def test_context_defaults_to_first_category_on_invalid_pk(self):
        view = self._make_view({"category": "not-a-number"})
        ctx = view.get_context_data(object_list=view.get_queryset())
        self.assertEqual(ctx["selected_category"], Category.objects.first())
