import os
import json
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials


class SheetsClient:
    def __init__(self, pilot_sheet_id: str, drone_sheet_id: str, missions_sheet_id: str):
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]

        creds_json = os.getenv("GOOGLE_CREDS_JSON")

        # Local fallback
        if not creds_json and os.path.exists("service_account.json"):
            creds = Credentials.from_service_account_file("service_account.json", scopes=scopes)
        else:
            if not creds_json:
                raise ValueError("Missing GOOGLE_CREDS_JSON secret.")
            creds_dict = json.loads(creds_json)
            creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)

        self.client = gspread.authorize(creds)

        # Open 3 separate spreadsheets
        self.pilot_spreadsheet = self.client.open_by_key(pilot_sheet_id)
        self.drone_spreadsheet = self.client.open_by_key(drone_sheet_id)
        self.missions_spreadsheet = self.client.open_by_key(missions_sheet_id)

    def read_pilots_df(self) -> pd.DataFrame:
        ws = self.pilot_spreadsheet.sheet1
        rows = ws.get_all_records()
        df = pd.DataFrame(rows)
        if not df.empty:
            df.columns = [c.strip() for c in df.columns]
        return df

    def read_drones_df(self) -> pd.DataFrame:
        ws = self.drone_spreadsheet.worksheet("drone_fleet")  # change here
        rows = ws.get_all_records()
        df = pd.DataFrame(rows)
        if not df.empty:
            df.columns = [c.strip() for c in df.columns]
        return df

    def read_missions_df(self) -> pd.DataFrame:
        ws = self.missions_spreadsheet.sheet1
        rows = ws.get_all_records()
        df = pd.DataFrame(rows)
        if not df.empty:
            df.columns = [c.strip() for c in df.columns]
        return df

    def update_pilot_status(self, pilot_id: str, new_status: str) -> dict:
        ws = self.pilot_spreadsheet.sheet1
        records = ws.get_all_records()

        headers = ws.row_values(1)
        headers = [h.strip() for h in headers]

        if "pilot_id" not in headers or "status" not in headers:
            return {"success": False, "error": "Pilot sheet must contain pilot_id and status columns"}

        status_col = headers.index("status") + 1

        for i, row in enumerate(records, start=2):
            if str(row.get("pilot_id", "")).strip() == str(pilot_id).strip():
                ws.update_cell(i, status_col, new_status)
                return {"success": True, "pilot_id": pilot_id, "new_status": new_status}

        return {"success": False, "error": f"Pilot not found: {pilot_id}"}