from django.core.management.base import BaseCommand

from service.models import Table


class Command(BaseCommand):
    help = "Create record tables for Frisztek restaurant"

    def handle(self, *args, **options):
        table_data = [
            {"name": "P1", "x": 660, "y": 65},
            {"name": "P2", "x": 660, "y": 120},
            {"name": "P3", "x": 660, "y": 180},
            {"name": "P4", "x": 660, "y": 245},
            {"name": "L1", "x": 30, "y": 55},
            {"name": "L2", "x": 30, "y": 115},
            {"name": "L3", "x": 30, "y": 175},
            {"name": "L4", "x": 30, "y": 235},
            {"name": "1", "x": 130, "y": 80},
            {"name": "2", "x": 200, "y": 80},
            {"name": "3", "x": 270, "y": 80},
            {"name": "4", "x": 340, "y": 80},
            {"name": "5", "x": 410, "y": 80},
            {"name": "6", "x": 480, "y": 80},
            {"name": "7", "x": 550, "y": 80},
            {"name": "8", "x": 270, "y": 195},
            {"name": "9", "x": 340, "y": 195},
            {"name": "10", "x": 410, "y": 195},
            {"name": "Na wynos", "x": 350, "y": 300},
        ]
        for table in table_data:
            obj, created = Table.objects.get_or_create(**table)
            if created:
                print(f"Created table: {obj}")
            else:
                print(f"Table already exists: {obj}")
