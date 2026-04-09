from datetime import datetime


def generate_summary_report(
    from_date: datetime | None, to_date: datetime | None, calculator_collection: list
):
    data = {}
    start, end = from_date, to_date
    for calc in calculator_collection:
        data[calc.name] = calc.calculate(start, end)
    data["date_from"] = from_date if from_date else None
    data["date_to"] = to_date if to_date else None

    return data
