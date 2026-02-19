from utils import normalize_list, weather_ok


def score_pilot(pilot_row, mission_row):
    score = 0

    mission_loc = str(mission_row.get("location", "")).strip().lower()
    pilot_loc = str(pilot_row.get("location", "")).strip().lower()

    if pilot_loc == mission_loc:
        score += 25
    else:
        score -= 10

    required_skills = normalize_list(mission_row.get("required_skills", ""))
    required_certs = normalize_list(mission_row.get("required_certs", ""))

    pilot_skills = normalize_list(pilot_row.get("skills", ""))
    pilot_certs = normalize_list(pilot_row.get("certifications", ""))

    # Skills
    for s in required_skills:
        if s in pilot_skills:
            score += 10
        else:
            score -= 30

    # Certs (hard)
    for c in required_certs:
        if c in pilot_certs:
            score += 20
        else:
            score -= 80

    # Cost preference
    try:
        cost = float(pilot_row.get("daily_rate_inr", 0))
        if cost <= 2000:
            score += 10
        elif cost <= 4000:
            score += 5
        else:
            score -= 5
    except:
        pass

    return score


def score_drone(drone_row, mission_row):
    score = 0

    mission_loc = str(mission_row.get("location", "")).strip().lower()
    drone_loc = str(drone_row.get("location", "")).strip().lower()

    if drone_loc == mission_loc:
        score += 20
    else:
        score -= 10

    mission_weather = mission_row.get("weather_forecast", "")
    resistance = drone_row.get("weather_resistance", "")

    if weather_ok(resistance, mission_weather):
        score += 25
    else:
        score -= 100

    return score
