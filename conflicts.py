from utils import normalize_list, safe_date, overlaps, weather_ok


def detect_conflicts_for_mission(mission_row, pilots_df, drones_df, missions_df):
    issues = []

    # Your missions use project_id
    mission_id = str(mission_row.get("project_id", "")).strip()

    m_start = safe_date(mission_row.get("start_date"))
    m_end = safe_date(mission_row.get("end_date"))
    m_loc = str(mission_row.get("location", "")).strip().lower()

    required_skills = normalize_list(mission_row.get("required_skills", ""))
    required_certs = normalize_list(mission_row.get("required_certs", ""))

    mission_weather = str(mission_row.get("weather_forecast", "")).strip()
    budget = mission_row.get("mission_budget_inr", None)

    # Optional columns (only if you add them in missions sheet)
    assigned_pilots = normalize_list(mission_row.get("assigned_pilots", ""))
    assigned_drones = normalize_list(mission_row.get("assigned_drones", ""))

    # ---------- PILOT CHECKS ----------
    for pid in assigned_pilots:
        p = pilots_df[pilots_df["pilot_id"].astype(str).str.lower() == pid.lower()]
        if p.empty:
            issues.append(f"Pilot {pid} not found in roster.")
            continue

        p = p.iloc[0]
        p_loc = str(p.get("location", "")).strip().lower()
        p_status = str(p.get("status", "")).strip().lower()

        if p_status in ["on leave", "unavailable"]:
            issues.append(f"Pilot {pid} is {p.get('status')} but assigned to mission {mission_id}.")

        if p_loc != m_loc:
            issues.append(
                f"Location mismatch: Pilot {pid} is in {p.get('location')} but mission is in {mission_row.get('location')}."
            )

        p_skills = normalize_list(p.get("skills", ""))
        p_certs = normalize_list(p.get("certifications", ""))

        missing_skills = [s for s in required_skills if s not in p_skills]
        missing_certs = [c for c in required_certs if c not in p_certs]

        if missing_skills:
            issues.append(f"Skill mismatch: Pilot {pid} missing skills: {', '.join(missing_skills)}")

        if missing_certs:
            issues.append(f"Certification mismatch: Pilot {pid} missing certs: {', '.join(missing_certs)}")

        # Double booking (pilot)
        if assigned_pilots and not missions_df.empty:
            for _, other in missions_df.iterrows():
                if str(other.get("project_id", "")).strip() == mission_id:
                    continue
                other_pilots = normalize_list(other.get("assigned_pilots", ""))
                if pid.lower() in [x.lower() for x in other_pilots]:
                    o_start = safe_date(other.get("start_date"))
                    o_end = safe_date(other.get("end_date"))
                    if overlaps(m_start, m_end, o_start, o_end):
                        issues.append(f"Double booking: Pilot {pid} overlaps with mission {other.get('project_id')}.")

    # ---------- DRONE CHECKS ----------
    for did in assigned_drones:
        d = drones_df[drones_df["drone_id"].astype(str).str.lower() == did.lower()]
        if d.empty:
            issues.append(f"Drone {did} not found in fleet.")
            continue

        d = d.iloc[0]
        d_loc = str(d.get("location", "")).strip().lower()
        d_status = str(d.get("status", "")).strip().lower()

        if d_status == "maintenance":
            issues.append(f"Drone {did} is in Maintenance but assigned to mission {mission_id}.")

        if d_loc != m_loc:
            issues.append(
                f"Location mismatch: Drone {did} is in {d.get('location')} but mission is in {mission_row.get('location')}."
            )

        resistance = d.get("weather_resistance", "")
        if not weather_ok(resistance, mission_weather):
            issues.append(
                f"Weather risk: Drone {did} resistance={resistance} not safe for {mission_weather} mission."
            )

        # Double booking (drone)
        if assigned_drones and not missions_df.empty:
            for _, other in missions_df.iterrows():
                if str(other.get("project_id", "")).strip() == mission_id:
                    continue
                other_drones = normalize_list(other.get("assigned_drones", ""))
                if did.lower() in [x.lower() for x in other_drones]:
                    o_start = safe_date(other.get("start_date"))
                    o_end = safe_date(other.get("end_date"))
                    if overlaps(m_start, m_end, o_start, o_end):
                        issues.append(f"Double booking: Drone {did} overlaps with mission {other.get('project_id')}.")

    # ---------- BUDGET OVERRUN ----------
    try:
        budget_val = float(budget) if budget not in [None, ""] else None
    except:
        budget_val = None

    if budget_val is not None and assigned_pilots:
        total_days = (m_end - m_start).days + 1 if m_start and m_end else 0
        total_cost = 0

        for pid in assigned_pilots:
            p = pilots_df[pilots_df["pilot_id"].astype(str).str.lower() == pid.lower()]
            if p.empty:
                continue
            try:
                rate = float(p.iloc[0].get("daily_rate_inr", 0))
                total_cost += rate * total_days
            except:
                pass

        if total_cost > budget_val:
            issues.append(
                f"Budget warning: Pilot cost ₹{total_cost:.0f} exceeds mission budget ₹{budget_val:.0f}."
            )

    # If missions sheet has no assignments, we still return something helpful
    if not assigned_pilots and not assigned_drones:
        issues.append(
            "Note: Missions sheet has no assigned_pilots/assigned_drones columns, so double-booking checks are skipped."
        )

    return issues