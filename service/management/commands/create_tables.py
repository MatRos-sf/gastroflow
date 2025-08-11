from django.core.management.base import BaseCommand

from service.models import Table


class Command(BaseCommand):
    help = "Create record tables for Frisztek restaurant"

    def handle(self, *args, **options):
        table_data = [
            {"name": "ŚL", "x": 250, "y": 165},
            {"name": "ŚP", "x": 390, "y": 165},
            {"name": "P1", "x": 660, "y": 65},
            {"name": "P2", "x": 660, "y": 120},
            {"name": "P3", "x": 660, "y": 180},
            {"name": "P4", "x": 660, "y": 245},
            {"name": "L1", "x": 50, "y": 65},
            {"name": "L2", "x": 50, "y": 120},
            {"name": "L3", "x": 50, "y": 180},
            {"name": "L4", "x": 50, "y": 245},
            {"name": "1", "x": 150, "y": 80},
            {"name": "2", "x": 220, "y": 80},
            {"name": "3", "x": 290, "y": 80},
            {"name": "4", "x": 390, "y": 80},
            {"name": "5", "x": 460, "y": 80},
            {"name": "6", "x": 540, "y": 80},
            {"name": "Na wynos", "x": 305, "y": 300},
        ]
        for table in table_data:
            obj, created = Table.objects.get_or_create(**table)
            if created:
                print(f"Created table: {obj}")
            else:
                print(f"Table already exists: {obj}")
