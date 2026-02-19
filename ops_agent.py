import pandas as pd
from utils import normalize_list, safe_date, weather_ok
from matcher import score_pilot, score_drone
from conflicts import detect_conflicts_for_mission


class OpsAgent:
    def __init__(self, sheets_client):
        self.sheets = sheets_client

    def load_all(self):
        pilots = self.sheets.read_pilots_df()
        drones = self.sheets.read_drones_df()
        missions = self.sheets.read_missions_df()
        return pilots, drones, missions

    # ---------------- PILOTS ----------------
    def query_pilots(self, skill=None, certification=None, location=None, status=None):
        pilots, _, _ = self.load_all()

        if pilots.empty:
            return "No pilot roster data found."

        df = pilots.copy()

        if status:
            df = df[df["status"].astype(str).str.lower() == status.lower()]

        if location:
            df = df[df["location"].astype(str).str.lower() == location.lower()]

        if skill:
            df = df[df["skills"].apply(lambda x: skill.lower() in normalize_list(x))]

        if certification:
            df = df[df["certifications"].apply(lambda x: certification.lower() in normalize_list(x))]

        if df.empty:
            return "No matching pilots found."

        cols = ["pilot_id", "name", "location", "status", "skills", "certifications", "daily_rate_inr"]
        return df[cols].head(20)

    def calc_pilot_cost(self, pilot_id: str, start_date: str, end_date: str):
        pilots, _, _ = self.load_all()
        p = pilots[pilots["pilot_id"].astype(str).str.strip() == str(pilot_id).strip()]

        if p.empty:
            return f"Pilot {pilot_id} not found."

        p = p.iloc[0]
        rate = float(p.get("daily_rate_inr", 0))

        s = safe_date(start_date)
        e = safe_date(end_date)

        if not s or not e:
            return "Invalid start/end dates. Use YYYY-MM-DD."

        days = (e - s).days + 1
        cost = rate * days

        return {
            "pilot_id": pilot_id,
            "daily_rate_inr": rate,
            "days": days,
            "total_cost_inr": cost,
        }

    def update_pilot_status(self, pilot_id: str, new_status: str):
        return self.sheets.update_pilot_status(pilot_id, new_status)

    # ---------------- DRONES ----------------
    def query_drones(self, capability=None, location=None, status=None, mission_weather=None):
        _, drones, _ = self.load_all()

        if drones.empty:
            return "No drone fleet data found."

        df = drones.copy()

        if status:
            df = df[df["status"].astype(str).str.lower() == status.lower()]

        if location:
            df = df[df["location"].astype(str).str.lower() == location.lower()]

        if capability:
            df = df[df["capabilities"].apply(lambda x: capability.lower() in normalize_list(x))]

        if mission_weather:
            df = df[df.apply(lambda r: weather_ok(r.get("weather_resistance", ""), mission_weather), axis=1)]

        if df.empty:
            return "No matching drones found."

        cols = ["drone_id", "model", "location", "status", "weather_resistance", "capabilities", "maintenance_due"]
        return df[cols].head(20)

    # ---------------- MISSIONS ----------------
    def get_mission(self, mission_id: str):
        _, _, missions = self.load_all()
        if missions.empty:
            return None

        # Your sheet uses project_id
        m = missions[missions["project_id"].astype(str).str.strip() == str(mission_id).strip()]
        if m.empty:
            return None
        return m.iloc[0].to_dict()

    def check_conflicts(self, mission_id: str):
        pilots, drones, missions = self.load_all()
        mission = self.get_mission(mission_id)
        if not mission:
            return f"Mission {mission_id} not found."

        issues = detect_conflicts_for_mission(mission, pilots, drones, missions)

        if not issues:
            return f"No conflicts detected for mission {mission_id}."

        return issues

    # ---------------- ASSIGNMENT SUGGESTION ----------------
    def recommend_assignment(self, mission_id: str):
        pilots, drones, missions = self.load_all()
        mission = self.get_mission(mission_id)

        if not mission:
            return f"Mission {mission_id} not found."

        m_loc = str(mission.get("location", "")).strip().lower()
        m_weather = str(mission.get("weather_forecast", "")).strip()

        # --- filter eligible pilots ---
        p_df = pilots.copy()
        p_df = p_df[p_df["status"].astype(str).str.lower() == "available"]
        p_df = p_df[p_df["location"].astype(str).str.lower() == m_loc]

        required_skills = normalize_list(mission.get("required_skills", ""))
        required_certs = normalize_list(mission.get("required_certs", ""))

        for s in required_skills:
            p_df = p_df[p_df["skills"].apply(lambda x: s in normalize_list(x))]

        for c in required_certs:
            p_df = p_df[p_df["certifications"].apply(lambda x: c in normalize_list(x))]

        if p_df.empty:
            return "No eligible pilots found for this mission (availability/location/skills/certs)."

        # --- filter eligible drones ---
        d_df = drones.copy()
        d_df = d_df[d_df["status"].astype(str).str.lower() == "available"]
        d_df = d_df[d_df["location"].astype(str).str.lower() == m_loc]
        d_df = d_df[d_df.apply(lambda r: weather_ok(r.get("weather_resistance", ""), m_weather), axis=1)]

        if d_df.empty:
            return "No eligible drones found for this mission (availability/location/weather)."

        # scoring
        p_df = p_df.copy()
        p_df["score"] = p_df.apply(lambda r: score_pilot(r, mission), axis=1)
        p_df = p_df.sort_values("score", ascending=False)

        d_df = d_df.copy()
        d_df["score"] = d_df.apply(lambda r: score_drone(r, mission), axis=1)
        d_df = d_df.sort_values("score", ascending=False)

        required_pilots = int(mission.get("required_pilots", 1) or 1)
        required_drones = int(mission.get("required_drones", 1) or 1)

        best_pilots = p_df.head(required_pilots)[["pilot_id", "name", "daily_rate_inr", "score"]]
        best_drones = d_df.head(required_drones)[["drone_id", "model", "weather_resistance", "score"]]

        return {
            "project_id": mission_id,
            "recommended_pilots": best_pilots.to_dict(orient="records"),
            "recommended_drones": best_drones.to_dict(orient="records"),
        }

    # ---------------- URGENT REASSIGNMENT ----------------
    def urgent_reassignment(self, mission_id: str):
        mission = self.get_mission(mission_id)
        if not mission:
            return f"Mission {mission_id} not found."

        issues = self.check_conflicts(mission_id)
        rec = self.recommend_assignment(mission_id)

        return {
            "project_id": mission_id,
            "conflicts": issues,
            "replacement_recommendations": rec,
        }
