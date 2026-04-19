from datetime import date, timedelta


def _easter_date(year: int) -> date:
    # Algoritmo di Meeus/Jones/Butcher (calendario gregoriano).
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def italy_holidays(year: int) -> dict[date, str]:
    easter = _easter_date(year)
    easter_monday = easter + timedelta(days=1)

    fixed = {
        date(year, 1, 1): "Capodanno",
        date(year, 1, 6): "Epifania",
        date(year, 4, 25): "Liberazione",
        date(year, 5, 1): "Festa del Lavoro",
        date(year, 6, 2): "Festa della Repubblica",
        date(year, 8, 15): "Ferragosto",
        date(year, 11, 1): "Ognissanti",
        date(year, 12, 8): "Immacolata",
        date(year, 12, 25): "Natale",
        date(year, 12, 26): "Santo Stefano",
    }
    fixed[easter] = "Pasqua"
    fixed[easter_monday] = "Lunedi dell'Angelo"
    return fixed
