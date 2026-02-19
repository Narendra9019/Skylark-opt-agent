from dateutil.parser import parse

WEATHER_RANK = {
    "generic": 0,
    "ip43": 1,
    "ip54": 2,
    "ip67": 3,
}

WEATHER_MIN_REQUIRED = {
    "clear": "generic",
    "windy": "generic",
    "rainy": "ip43",
}


def safe_date(x):
    if x is None or str(x).strip() == "":
        return None
    try:
        return parse(str(x)).date()
    except:
        return None


def normalize_list(x):
    if x is None:
        return []
    s = str(x).strip()
    if not s or s == "-":
        return []
    return [t.strip().lower() for t in s.split(",") if t.strip()]


def overlaps(a_start, a_end, b_start, b_end):
    if not a_start or not a_end or not b_start or not b_end:
        return False
    return a_start <= b_end and b_start <= a_end


def weather_ok(drone_resistance: str, mission_weather: str) -> bool:
    if not mission_weather:
        return True

    mission_weather = str(mission_weather).strip().lower()
    drone_resistance = str(drone_resistance).strip().lower()

    # Rainy mission needs IP rating or rain support
    if mission_weather in ["rainy", "rain"]:
        return ("ip" in drone_resistance) or ("rain" in drone_resistance)

    return True