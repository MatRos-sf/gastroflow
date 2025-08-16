from decimal import Decimal

from django.core.management.base import BaseCommand

from menu.models import Addition, Item, Location, MenuType, SubMenuType

default_menu = [
    # MenuType.MAIN
    {
        "menu": MenuType.MAIN,
        "preparation_location": Location.KITCHEN,
        "name": "Jajecznica",
        "description": "3 jajka / pieczywo / masło / mix sałatek ze słonecznikiem",
        "additions": [
            {"name": "Szczypiorek", "id_checkout": 0, "price": Decimal("0.00")},
            {"name": "Szynka", "id_checkout": 16, "price": Decimal("2.00")},
            {"name": "Boczek", "id_checkout": 17, "price": Decimal("3.00")},
            {"name": "Pomidor", "id_checkout": 18, "price": Decimal("1.00")},
            {"name": "Opakowanie", "id_checkout": 51, "price": Decimal("2.00")},
        ],
        "id_checkout": 1,
        "price": Decimal("25.00"),
    },
    {
        "menu": MenuType.MAIN,
        "preparation_location": Location.KITCHEN,
        "name": "Jajka W Koszulce",
        "description": "jogurt grecki / czosnek / nasz autorski olej chilli/ zaatar / koperek / pieczywo",
        "additions": [
            {"name": "Opakowanie", "id_checkout": 51, "price": Decimal("2.00")},
        ],
        "id_checkout": 2,
        "price": Decimal("29.00"),
    },
    {
        "menu": MenuType.MAIN,
        "preparation_location": Location.KITCHEN,
        "name": "Autorski Omlet Witka",
        "description": "omlet z 3 jaj / wędzony pstrąg z lokalnej wędzarni / sos holenderski / ser Bursztyn / szczypiorek / mix sałat ze słonecznikiem",
        "additions": [
            {"name": "Opakowanie", "id_checkout": 51, "price": Decimal("2.00")},
        ],
        "id_checkout": 3,
        "price": Decimal("34.00"),
    },
    {
        "menu": MenuType.MAIN,
        "preparation_location": Location.KITCHEN,
        "name": "Bajgel Klasyczny: Z łososiem",
        "description": "serek śmietankowy / wędzony łosoś z lokalnej wędzarni / rukola / ogórek / mix sałat ze słonecznikiem",
        "additions": [
            {"name": "Opakowanie", "id_checkout": 51, "price": Decimal("2.00")},
        ],
        "id_checkout": 5,
        "price": Decimal("36.00"),
    },
    {
        "menu": MenuType.MAIN,
        "preparation_location": Location.KITCHEN,
        "name": "Bajgel Klasyczny: Z szarpanym kurczakiem",
        "description": "pasta ze szarpanym kurczakiem / pomidor / rukola / ogórek / mix sałat ze słonecznikiem",
        "additions": [
            {"name": "Opakowanie", "id_checkout": 51, "price": Decimal("2.00")},
        ],
        "id_checkout": 6,
        "price": Decimal("36.00"),
    },
    {
        "menu": MenuType.MAIN,
        "preparation_location": Location.KITCHEN,
        "name": "Kiełbasa Podsmarzana",
        "description": "jajka sadzone / pieczywo / sosy / mix sałat ze słonecznikiem",
        "additions": [
            {"name": "Opakowanie", "id_checkout": 51, "price": Decimal("2.00")},
        ],
        "id_checkout": 7,
        "price": Decimal("29.00"),
    },
    {
        "menu": MenuType.MAIN,
        "preparation_location": Location.KITCHEN,
        "name": "Maślane Tosty Francuskie",
        "description": "jogurt grecki / owoce sezonowe / syrop klonowy / mięta",
        "additions": [
            {"name": "Opakowanie", "id_checkout": 51, "price": Decimal("2.00")},
        ],
        "id_checkout": 8,
        "price": Decimal("28.00"),
    },
    {
        "menu": MenuType.MAIN,
        "preparation_location": Location.KITCHEN,
        "name": "Ruchanki Kaszubskie",
        "description": "drożdżowe placki z jabłkiem / kwaśna śmietana / domowa konfitura z borówek / maliny / mięta",
        "additions": [
            {"name": "Opakowanie", "id_checkout": 51, "price": Decimal("2.00")},
        ],
        "id_checkout": 9,
        "price": Decimal("28.00"),
    },
    # MenuType.MENU_FOR_CHILDREN
    {
        "menu": MenuType.MENU_FOR_CHILDREN,
        "preparation_location": Location.KITCHEN,
        "name": "Śniadanie małego pirata",
        "description": "jajecznica / naturalne parówki ośmiorniczki / pomidory / ogórki / bułka",
        "additions": [
            {"name": "Opakowanie", "id_checkout": 51, "price": Decimal("2.00")},
        ],
        "id_checkout": 10,
        "price": Decimal("22.00"),
    },
    {
        "menu": MenuType.MENU_FOR_CHILDREN,
        "preparation_location": Location.KITCHEN,
        "name": "Śniadaniowy Żagiel",
        "description": "chleb / masło / szynka / ser żółty / ogórek / pomidor",
        "additions": [
            {"name": "Opakowanie", "id_checkout": 51, "price": Decimal("2.00")},
        ],
        "id_checkout": 11,
        "price": Decimal("18.00"),
    },
    {
        "menu": MenuType.MENU_FOR_CHILDREN,
        "preparation_location": Location.KITCHEN,
        "name": "Skarb Słodkiego Pirata",
        "description": "pancakes / nutella / truskawki / borówki",
        "additions": [
            {"name": "Opakowanie", "id_checkout": 51, "price": Decimal("2.00")},
        ],
        "id_checkout": 12,
        "price": Decimal("21.00"),
    },
    {
        "menu": MenuType.MENU_FOR_CHILDREN,
        "preparation_location": Location.KITCHEN,
        "name": "Słodki Krab",
        "description": "croissant / domowy dżem truskawkowy / truskawki / banan / borówki",
        "additions": [
            {"name": "Opakowanie", "id_checkout": 51, "price": Decimal("2.00")},
        ],
        "id_checkout": 13,
        "price": Decimal("22.00"),
    },
    # MenuType.DRINK
    {
        "menu": MenuType.DRINK,
        "preparation_location": Location.BAR,
        "sub_menu": SubMenuType.COFFEE,
        "name": "Espresso",
        "description": "",
        "additions": [
            {"name": "Opakowanie", "id_checkout": 51, "price": Decimal("2.00")},
        ],
        "id_checkout": 20,
        "price": Decimal("9.00"),
    },
    {
        "menu": MenuType.DRINK,
        "preparation_location": Location.BAR,
        "sub_menu": SubMenuType.COFFEE,
        "name": "Americano",
        "description": "",
        "additions": [
            {"name": "Opakowanie", "id_checkout": 51, "price": Decimal("2.00")},
        ],
        "id_checkout": 22,
        "price": Decimal("12.00"),
    },
    {
        "menu": MenuType.DRINK,
        "preparation_location": Location.BAR,
        "sub_menu": SubMenuType.COFFEE,
        "name": "Cappucino",
        "description": "",
        "additions": [
            {"name": "Opakowanie", "id_checkout": 51, "price": Decimal("2.00")},
        ],
        "id_checkout": 21,
        "price": Decimal("14.00"),
    },
    {
        "menu": MenuType.DRINK,
        "preparation_location": Location.BAR,
        "sub_menu": SubMenuType.COFFEE,
        "name": "Latte Macchiato",
        "description": "",
        "additions": [
            {"name": "Opakowanie", "id_checkout": 51, "price": Decimal("2.00")},
        ],
        "id_checkout": 23,
        "price": Decimal("16.00"),
    },
    {
        "menu": MenuType.DRINK,
        "preparation_location": Location.BAR,
        "sub_menu": SubMenuType.COFFEE,
        "name": "Fusiara Kaszubska",
        "description": "",
        "additions": [
            {"name": "Opakowanie", "id_checkout": 51, "price": Decimal("2.00")},
        ],
        "id_checkout": 24,
        "price": Decimal("9.00"),
    },
    {
        "menu": MenuType.DRINK,
        "preparation_location": Location.BAR,
        "sub_menu": SubMenuType.COFFEE,
        "name": "Kawa Mrożona",
        "description": "",
        "additions": [
            {"name": "Opakowanie", "id_checkout": 51, "price": Decimal("2.00")},
        ],
        "id_checkout": 25,
        "price": Decimal("19.00"),
    },
    {
        "menu": MenuType.DRINK,
        "preparation_location": Location.BAR,
        "sub_menu": SubMenuType.TEA,
        "name": "Czarna",
        "description": "",
        "additions": [
            {"name": "Opakowanie", "id_checkout": 51, "price": Decimal("2.00")},
        ],
        "id_checkout": 26,
        "price": Decimal("10.00"),
    },
    {
        "menu": MenuType.DRINK,
        "preparation_location": Location.BAR,
        "sub_menu": SubMenuType.TEA,
        "name": "Earl Grey",
        "description": "",
        "additions": [
            {"name": "Opakowanie", "id_checkout": 51, "price": Decimal("2.00")},
        ],
        "id_checkout": 26,
        "price": Decimal("10.00"),
    },
    {
        "menu": MenuType.DRINK,
        "preparation_location": Location.BAR,
        "sub_menu": SubMenuType.TEA,
        "name": "Zielona",
        "description": "",
        "additions": [
            {"name": "Opakowanie", "id_checkout": 51, "price": Decimal("2.00")},
        ],
        "id_checkout": 26,
        "price": Decimal("10.00"),
    },
    {
        "menu": MenuType.DRINK,
        "preparation_location": Location.BAR,
        "sub_menu": SubMenuType.TEA,
        "name": "Jaśminowa",
        "description": "",
        "additions": [
            {"name": "Opakowanie", "id_checkout": 51, "price": Decimal("2.00")},
        ],
        "id_checkout": 26,
        "price": Decimal("10.00"),
    },
    {
        "menu": MenuType.DRINK,
        "preparation_location": Location.BAR,
        "sub_menu": SubMenuType.TEA,
        "name": "Owocowa",
        "description": "",
        "additions": [
            {"name": "Opakowanie", "id_checkout": 51, "price": Decimal("2.00")},
        ],
        "id_checkout": 26,
        "price": Decimal("10.00"),
    },
    {
        "menu": MenuType.DRINK,
        "preparation_location": Location.BAR,
        "sub_menu": SubMenuType.TEA,
        "name": "Jabłkowa",
        "description": "",
        "additions": [
            {"name": "Opakowanie", "id_checkout": 51, "price": Decimal("2.00")},
        ],
        "id_checkout": 26,
        "price": Decimal("10.00"),
    },
    {
        "menu": MenuType.DRINK,
        "preparation_location": Location.BAR,
        "sub_menu": SubMenuType.TEA,
        "name": "Miętowa",
        "description": "",
        "additions": [
            {"name": "Opakowanie", "id_checkout": 51, "price": Decimal("2.00")},
        ],
        "id_checkout": 26,
        "price": Decimal("10.00"),
    },
    {
        "menu": MenuType.DRINK,
        "preparation_location": Location.BAR,
        "sub_menu": SubMenuType.MATCHA,
        "name": "Matcha latte (na ciepło)",
        "description": "",
        "additions": [
            {"name": "Opakowanie", "id_checkout": 51, "price": Decimal("2.00")},
        ],
        "id_checkout": 27,
        "price": Decimal("18.00"),
    },
    {
        "menu": MenuType.DRINK,
        "preparation_location": Location.BAR,
        "sub_menu": SubMenuType.MATCHA,
        "name": "Matcha latte truskawkowa (na zimno)",
        "description": "",
        "additions": [
            {"name": "Opakowanie", "id_checkout": 51, "price": Decimal("2.00")},
        ],
        "id_checkout": 28,
        "price": Decimal("24.00"),
    },
    {
        "menu": MenuType.DRINK,
        "preparation_location": Location.BAR,
        "sub_menu": SubMenuType.MATCHA,
        "name": "Matcha latte pistacja-wanilia (na zimno)",
        "description": "",
        "additions": [
            {"name": "Opakowanie", "id_checkout": 51, "price": Decimal("2.00")},
        ],
        "id_checkout": 29,
        "price": Decimal("26.00"),
    },
    {
        "menu": MenuType.DRINK,
        "preparation_location": Location.BAR,
        "sub_menu": SubMenuType.MATCHA,
        "name": "Matcha latte mango (na zimno)",
        "description": "",
        "additions": [
            {"name": "Opakowanie", "id_checkout": 51, "price": Decimal("2.00")},
        ],
        "id_checkout": 30,
        "price": Decimal("25.00"),
    },
    # MenuType.COLD_DRINK
    {
        "menu": MenuType.COLD_DRINK,
        "preparation_location": Location.BAR,
        "name": "Pepsi",
        "description": "",
        "additions": [],
        "id_checkout": 31,
        "price": Decimal("9.00"),
    },
    {
        "menu": MenuType.COLD_DRINK,
        "preparation_location": Location.BAR,
        "name": "Pepsi Max",
        "description": "",
        "additions": [],
        "id_checkout": 32,
        "price": Decimal("9.00"),
    },
    {
        "menu": MenuType.COLD_DRINK,
        "preparation_location": Location.BAR,
        "name": "Fanta",
        "description": "",
        "additions": [],
        "id_checkout": 33,
        "price": Decimal("9.00"),
    },
    {
        "menu": MenuType.COLD_DRINK,
        "preparation_location": Location.BAR,
        "name": "Sprite",
        "description": "",
        "additions": [],
        "id_checkout": 34,
        "price": Decimal("9.00"),
    },
    {
        "menu": MenuType.COLD_DRINK,
        "preparation_location": Location.BAR,
        "name": "Sok Jabłkowy",
        "description": "",
        "additions": [],
        "id_checkout": 35,
        "price": Decimal("9.00"),
        "is_available": False,
    },
    {
        "menu": MenuType.COLD_DRINK,
        "preparation_location": Location.BAR,
        "name": "Sok Pomarańczowy",
        "description": "",
        "additions": [],
        "id_checkout": 35,
        "price": Decimal("9.00"),
        "is_available": False,
    },
    {
        "menu": MenuType.COLD_DRINK,
        "preparation_location": Location.BAR,
        "name": "Lipton",
        "description": "",
        "additions": [],
        "id_checkout": 35,
        "price": Decimal("9.00"),
        "is_available": False,
    },
    {
        "menu": MenuType.COLD_DRINK,
        "preparation_location": Location.BAR,
        "name": "Woda Niegazowana",
        "description": "",
        "additions": [],
        "id_checkout": 100,
        "price": Decimal("9.00"),
        "is_available": False,
    },
    {
        "menu": MenuType.COLD_DRINK,
        "preparation_location": Location.BAR,
        "name": "Woda Gazowana",
        "description": "",
        "additions": [],
        "id_checkout": 100,
        "price": Decimal("9.00"),
        "is_available": False,
    },
    {
        "menu": MenuType.COLD_DRINK,
        "preparation_location": Location.BAR,
        "name": "Aqua Carpatica",
        "description": "",
        "additions": [],
        "id_checkout": 52,
        "price": Decimal("10.00"),
        "is_available": False,
    },
    {
        "menu": MenuType.COLD_DRINK,
        "preparation_location": Location.BAR,
        "name": "Lemoniada Cytrynowa",
        "description": "",
        "additions": [
            {"name": "Opakowanie", "id_checkout": 51, "price": Decimal("2.00")},
        ],
        "id_checkout": 38,
        "price": Decimal("13.00"),
    },
    {
        "menu": MenuType.COLD_DRINK,
        "preparation_location": Location.BAR,
        "name": "Lemoniada Truskawkowa",
        "description": "",
        "additions": [
            {"name": "Opakowanie", "id_checkout": 51, "price": Decimal("2.00")},
        ],
        "id_checkout": 39,
        "price": Decimal("14.00"),
    },
    {
        "menu": MenuType.COLD_DRINK,
        "preparation_location": Location.BAR,
        "name": "Lemoniada Mango",
        "description": "",
        "additions": [
            {"name": "Opakowanie", "id_checkout": 51, "price": Decimal("2.00")},
        ],
        "id_checkout": 40,
        "price": Decimal("15.00"),
    },
    {
        "menu": MenuType.COLD_DRINK,
        "preparation_location": Location.BAR,
        "name": "Karawka Wody",
        "description": "",
        "additions": [],
        "id_checkout": 37,
        "price": Decimal("15.00"),
        "is_available": False,
    },
    {
        "menu": MenuType.COLD_DRINK,
        "preparation_location": Location.BAR,
        "sub_menu": SubMenuType.COCKTAIL,
        "name": "Kremowa Truskawka",
        "description": "truskawki / jogurt / śmietana",
        "additions": [
            {"name": "Opakowanie", "id_checkout": 51, "price": Decimal("2.00")},
        ],
        "id_checkout": 42,
        "price": Decimal("18.00"),
    },
    {
        "menu": MenuType.COLD_DRINK,
        "preparation_location": Location.BAR,
        "sub_menu": SubMenuType.COCKTAIL,
        "name": "Zielona Energia",
        "description": "szpinak / banan / mango / cytryna / pomarańcz ",
        "additions": [
            {"name": "Opakowanie", "id_checkout": 51, "price": Decimal("2.00")},
        ],
        "id_checkout": 43,
        "price": Decimal("20.00"),
    },
    {
        "menu": MenuType.COLD_DRINK,
        "preparation_location": Location.BAR,
        "sub_menu": SubMenuType.COCKTAIL,
        "name": "Dodający Energii",
        "description": "banan / płatki owsiane / masło orzechowe / mleko / gorzka czekolada",
        "additions": [
            {"name": "Opakowanie", "id_checkout": 51, "price": Decimal("2.00")},
        ],
        "id_checkout": 44,
        "price": Decimal("21.00"),
    },
    {
        "menu": MenuType.COLD_DRINK,
        "preparation_location": Location.BAR,
        "sub_menu": SubMenuType.SOFT_DRINK,
        "name": "Bezowe Pitku",
        "description": "limonka / syrop z kwiatów bzu / prosseco 0% / mięta",
        "additions": [
            {"name": "Opakowanie", "id_checkout": 51, "price": Decimal("2.00")},
        ],
        "id_checkout": 45,
        "price": Decimal("24.00"),
    },
    {
        "menu": MenuType.COLD_DRINK,
        "preparation_location": Location.BAR,
        "sub_menu": SubMenuType.SOFT_DRINK,
        "name": "Miętowe Pitku",
        "description": "limonka / mięta / rum 0%",
        "additions": [
            {"name": "Opakowanie", "id_checkout": 51, "price": Decimal("2.00")},
        ],
        "id_checkout": 46,
        "price": Decimal("24.00"),
    },
    {
        "menu": MenuType.COLD_DRINK,
        "preparation_location": Location.BAR,
        "sub_menu": SubMenuType.SOFT_DRINK,
        "name": "Pomarańczowe Pitku",
        "description": "pomarańcza / aperitivo 0% / prosseco 0%",
        "additions": [
            {"name": "Opakowanie", "id_checkout": 51, "price": Decimal("2.00")},
        ],
        "id_checkout": 47,
        "price": Decimal("24.00"),
    },
    {
        "menu": MenuType.COLD_DRINK,
        "preparation_location": Location.BAR,
        "sub_menu": SubMenuType.SOFT_DRINK,
        "name": "Lawendowe Pitku",
        "description": "syrop lawendowy / gin 0% / białko",
        "additions": [
            {"name": "Opakowanie", "id_checkout": 51, "price": Decimal("2.00")},
        ],
        "id_checkout": 48,
        "price": Decimal("24.00"),
    },
    # MenuType.DESSERT
    {
        "menu": MenuType.DESSERT,
        "name": "Ciasto 1",
        "description": "",
        "sub_menu": SubMenuType.CAKE,
        "preparation_location": Location.BAR,
        "additions": [
            {"name": "Opakowanie", "id_checkout": 51, "price": Decimal("2.00")},
        ],
        "id_checkout": 19,
        "price": Decimal("22.00"),
    },
    {
        "menu": MenuType.DESSERT,
        "name": "Ciasto 2",
        "description": "",
        "sub_menu": SubMenuType.CAKE,
        "preparation_location": Location.BAR,
        "additions": [
            {"name": "Opakowanie", "id_checkout": 51, "price": Decimal("2.00")},
        ],
        "id_checkout": 19,
        "price": Decimal("24.00"),
    },
    {
        "menu": MenuType.DESSERT,
        "name": "Ciasto 3",
        "description": "",
        "sub_menu": SubMenuType.CAKE,
        "preparation_location": Location.BAR,
        "additions": [
            {"name": "Opakowanie", "id_checkout": 51, "price": Decimal("2.00")},
        ],
        "id_checkout": 49,
        "price": Decimal("25.00"),
    },
    {
        "menu": MenuType.DESSERT,
        "name": "Ciasto 4",
        "description": "",
        "sub_menu": SubMenuType.CAKE,
        "preparation_location": Location.BAR,
        "additions": [
            {"name": "Opakowanie", "id_checkout": 51, "price": Decimal("2.00")},
        ],
        "id_checkout": 50,
        "price": Decimal("16.00"),
    },
    {
        "menu": MenuType.DESSERT,
        "name": "Owoce z Białą Czekoladą",
        "description": "",
        "preparation_location": Location.BAR,
        "additions": [
            {"name": "Opakowanie", "id_checkout": 51, "price": Decimal("2.00")},
        ],
        "id_checkout": 60,
        "price": Decimal("16.00"),
    },
    {
        "menu": MenuType.DESSERT,
        "name": "Cake Pop",
        "description": "",
        "preparation_location": Location.BAR,
        "additions": [
            {"name": "Opakowanie", "id_checkout": 51, "price": Decimal("2.00")},
        ],
        "id_checkout": 58,
        "price": Decimal("12.00"),
    },
    {
        "menu": MenuType.DESSERT,
        "name": "Gofry Suche",
        "sub_menu": SubMenuType.WAFFLE,
        "description": "",
        "preparation_location": Location.BAR,
        "additions": [
            {"name": "Bita Śmietana", "id_checkout": 54, "price": Decimal("2.00")},
            {"name": "Owoce", "id_checkout": 55, "price": Decimal("4.00")},
            {"name": "Posypka", "id_checkout": 56, "price": Decimal("1.00")},
            {"name": "Nutella", "id_checkout": 57, "price": Decimal("4.00")},
            {"name": "Opakowanie", "id_checkout": 51, "price": Decimal("2.00")},
        ],
        "id_checkout": 53,
        "price": Decimal("12.00"),
    },
]

addition_collection = [
    {"name": "Mleko roślinne", "id_checkout": 59, "price": Decimal("2.00")},
    {"name": "Jajko", "id_checkout": 61, "price": Decimal("4.00")},
    {"name": "Koszyk Pieczywa", "id_checkout": 62, "price": Decimal("10.00")},
    {"name": "Bułka", "id_checkout": 63, "price": Decimal("3.00")},
    {"name": "Dodatek", "id_checkout": 64, "price": Decimal("4.00")},
    {"name": "Opakowanie", "id_checkout": 0, "price": Decimal("4.00")},
]


class Command(BaseCommand):
    help = "Create default menu for Frisztek restaurant"

    def handle(self, *args, **options):
        for item in default_menu:
            additions = []
            for addition in item.pop("additions"):
                obj, _ = Addition.objects.get_or_create(**addition)
                if _:
                    print("\t\tSaved addition:", obj.name)
                else:
                    print(f"\t\tAdd existing additions ({obj})")
                additions.append(obj)
            obj, _ = Item.objects.get_or_create(**item)
            obj.additions.set(additions)
            print("Saved item:", obj.name)

        # add additions
        for addition in addition_collection:
            obj, _ = Addition.objects.get_or_create(**addition)
            if _:
                print("\t\tSaved addition:", obj.name)
            else:
                print(f"\t\tSkipp addition: ({obj})")
