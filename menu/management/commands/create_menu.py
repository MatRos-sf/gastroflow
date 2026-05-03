import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from menu.models import Addition, Category, Item, Location, SubCategory


class Command(BaseCommand):
    help = "Load menu data (categories, subcategories, additions, items) from a JSON file. Usage: python manage.py create_menu menu/fixtures/frisztek_menu.json"

    def add_arguments(self, parser):
        parser.add_argument(
            "file",
            type=str,
            help="Path to the JSON file containing menu data.",
        )

    def handle(self, *args, **options):
        path = Path(options["file"])
        if not path.exists():
            raise CommandError(f"File not found: {path}")

        with path.open(encoding="utf-8") as f:
            data = json.load(f)

        self._load_categories(data.get("categories", []))
        self._load_subcategories(data.get("subcategories", []))
        self._load_additions(data.get("additions", []))
        self._load_items(data.get("items", []))

    def _load_categories(self, entries):
        for entry in entries:
            obj, created = Category.objects.get_or_create(name=entry["name"])
            label = self.style.SUCCESS("Created") if created else "Exists "
            self.stdout.write(f"  {label} category: {obj}")

    def _load_subcategories(self, entries):
        for entry in entries:
            try:
                category = Category.objects.get(name=entry["category"])
            except Category.DoesNotExist:
                raise CommandError(
                    f"Category '{entry['category']}' not found for subcategory '{entry['name']}'. "
                    "Make sure categories are listed before subcategories in the JSON."
                )
            obj, created = SubCategory.objects.get_or_create(
                name=entry["name"], category=category
            )
            label = self.style.SUCCESS("Created") if created else "Exists "
            self.stdout.write(f"  {label} subcategory: {obj}")

    def _load_additions(self, entries):
        for entry in entries:
            obj, created = Addition.objects.get_or_create(
                name=entry["name"],
                defaults={
                    "bill_name": entry.get("bill_name"),
                    "vat": entry.get("vat", 0),
                    "price": entry["price"],
                    "id_checkout": entry["id_checkout"],
                    "priority": entry.get("priority", 1),
                },
            )
            label = self.style.SUCCESS("Created") if created else "Exists "
            self.stdout.write(f"  {label} addition: {obj}")

    def _load_items(self, entries):
        for entry in entries:
            try:
                category = Category.objects.get(name=entry["category"])
            except Category.DoesNotExist:
                raise CommandError(
                    f"Category '{entry['category']}' not found for item '{entry['name']}'."
                )

            subcategory = None
            if entry.get("subcategory"):
                try:
                    subcategory = SubCategory.objects.get(
                        name=entry["subcategory"], category=category
                    )
                except SubCategory.DoesNotExist:
                    raise CommandError(
                        f"Subcategory '{entry['subcategory']}' not found under '{category}' "
                        f"for item '{entry['name']}'."
                    )

            item, created = Item.objects.get_or_create(
                name=entry["name"],
                defaults={
                    "category": category,
                    "sub_menu": subcategory,
                    "preparation_location": entry.get(
                        "preparation_location", Location.KITCHEN
                    ),
                    "description": entry.get("description", ""),
                    "bill_name": entry.get("bill_name"),
                    "vat": entry.get("vat", 0),
                    "id_checkout": entry["id_checkout"],
                    "price": entry["price"],
                },
            )
            label = self.style.SUCCESS("Created") if created else "Exists "
            self.stdout.write(f"  {label} item: {item}")

            addition_names = entry.get("additions", [])
            if addition_names:
                additions = Addition.objects.filter(name__in=addition_names)
                missing = set(addition_names) - set(
                    additions.values_list("name", flat=True)
                )
                if missing:
                    raise CommandError(
                        f"Additions not found for item '{item.name}': {', '.join(missing)}"
                    )
                item.additions.set(additions)
