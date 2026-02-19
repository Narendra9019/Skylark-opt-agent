import gradio as gr
from sheets_client import SheetsClient
from ops_agent import OpsAgent

PILOT_SHEET_ID = "1BomCw1LpYq_12AE8b8ox04ZQyT2q-hB39baQn49kYh4"
DRONE_SHEET_ID = "1yCnzT7Hdp8MHCIyUNSDClGw3XLsTyyy21NCQgSLIIYs"
MISSIONS_SHEET_ID = "1Zyxh3jJfZ4gIvFvMtemiKRXR6c6ABhhu9OCJ2dkBVyU"

sheets = SheetsClient(PILOT_SHEET_ID, DRONE_SHEET_ID, MISSIONS_SHEET_ID)
agent = OpsAgent(sheets)


def handle_message(message, history):
    msg = message.strip()

    # ---------------- PILOT QUERY ----------------
    if msg.lower().startswith("show pilots"):
        # Example:
        # show pilots skill=mapping location=mumbai status=available cert=dgca
        skill = None
        location = None
        status = None
        cert = None

        for token in msg.split():
            if token.startswith("skill="):
                skill = token.split("=", 1)[1]
            elif token.startswith("location="):
                location = token.split("=", 1)[1]
            elif token.startswith("status="):
                status = token.split("=", 1)[1]
            elif token.startswith("cert="):
                cert = token.split("=", 1)[1]

        result = agent.query_pilots(skill=skill, certification=cert, location=location, status=status)
        return str(result)

    # ---------------- PILOT STATUS UPDATE ----------------
    if msg.lower().startswith("update pilot"):
        # update pilot P001 status=On Leave
        parts = msg.split()
        if len(parts) < 3:
            return "Format: update pilot P001 status=On Leave"

        pilot_id = parts[2].strip()

        if "status=" not in msg.lower():
            return "Format: update pilot P001 status=On Leave"

        new_status = msg.split("status=", 1)[1].strip()
        result = agent.update_pilot_status(pilot_id, new_status)
        return str(result)

    # ---------------- PILOT COST ----------------
    if msg.lower().startswith("pilot cost"):
        # pilot cost P001 start=2026-02-05 end=2026-02-07
        parts = msg.split()
        if len(parts) < 3:
            return "Format: pilot cost P001 start=YYYY-MM-DD end=YYYY-MM-DD"

        pilot_id = parts[2].strip()
        start = None
        end = None

        for token in parts:
            if token.startswith("start="):
                start = token.split("=", 1)[1]
            if token.startswith("end="):
                end = token.split("=", 1)[1]

        return str(agent.calc_pilot_cost(pilot_id, start, end))

    # ---------------- DRONE QUERY ----------------
    if msg.lower().startswith("show drones"):
        # show drones capability=thermal location=bangalore status=available weather=rainy
        capability = None
        location = None
        status = None
        weather = None

        for token in msg.split():
            if token.startswith("capability="):
                capability = token.split("=", 1)[1]
            elif token.startswith("location="):
                location = token.split("=", 1)[1]
            elif token.startswith("status="):
                status = token.split("=", 1)[1]
            elif token.startswith("weather="):
                weather = token.split("=", 1)[1]

        result = agent.query_drones(capability=capability, location=location, status=status, mission_weather=weather)
        return str(result)

    # ---------------- CONFLICTS ----------------
    if msg.lower().startswith("check conflicts"):
        # check conflicts mission=M001
        mission_id = None
        for token in msg.split():
            if token.startswith("mission="):
                mission_id = token.split("=", 1)[1]
        if not mission_id:
            return "Format: check conflicts mission=M001"
        return str(agent.check_conflicts(mission_id))

    # ---------------- ASSIGNMENT RECOMMENDATION ----------------
    if msg.lower().startswith("assign mission"):
        # assign mission M001
        parts = msg.split()
        if len(parts) < 3:
            return "Format: assign mission M001"
        mission_id = parts[2].strip()
        return str(agent.recommend_assignment(mission_id))

    # ---------------- URGENT REASSIGNMENT ----------------
    if msg.lower().startswith("urgent replacement"):
        # urgent replacement mission=M001
        mission_id = None
        for token in msg.split():
            if token.startswith("mission="):
                mission_id = token.split("=", 1)[1]
        if not mission_id:
            return "Format: urgent replacement mission=M001"
        return str(agent.urgent_reassignment(mission_id))

    # ---------------- HELP ----------------
    return (
        "Commands:\n"
        "1) show pilots skill=mapping location=mumbai status=available cert=dgca\n"
        "2) update pilot P001 status=On Leave\n"
        "3) pilot cost P001 start=2026-02-05 end=2026-02-07\n"
        "4) show drones capability=thermal location=bangalore status=available weather=rainy\n"
        "5) check conflicts mission=M001\n"
        "6) assign mission M001\n"
        "7) urgent replacement mission=M001\n"
    )


demo = gr.ChatInterface(handle_message, title="Skylark Drone Ops Agent (Google Sheets Synced)")
demo.launch()
