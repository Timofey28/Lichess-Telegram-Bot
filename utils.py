from datetime import date


no2month = {
    1: 'января',
    2: 'февраля',
    3: 'марта',
    4: 'апреля',
    5: 'мая',
    6: 'июня',
    7: 'июля',
    8: 'августа',
    9: 'сентября',
    10: 'октября',
    11: 'ноября',
    12: 'декабря',
}


def prettify_date(dt: date) -> str:
    return f'{dt.day} {no2month[dt.month]}'

def prettify_interval(start_date, end_date) -> str:
    if start_date.year == end_date.year:
        return f'{start_date.day} {no2month[start_date.month]} — {end_date.day} {no2month[end_date.month]} {start_date.year} года'
    else:
        return f'{start_date.day} {no2month[start_date.month]} {start_date.year} года - {end_date.day} {no2month[end_date.month]} {end_date.year} года'