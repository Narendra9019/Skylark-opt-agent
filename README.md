# Skylark Drones - Drone Operations Coordinator AI Agent

This project is a conversational AI assistant that helps coordinate pilots, drones, and missions for Skylark Drones.

It reads operational data from Google Sheets (Pilot roster, Drone fleet, Missions) and supports pilot status updates with write-back sync.

---

## Features Implemented

### 1) Roster Management
- Query pilots by skill / certification / location / status
- View current pilot assignments
- Calculate pilot cost for a mission duration
- Update pilot status (Available / On Leave / Unavailable) with Google Sheets sync

### 2) Drone Inventory
- Query drones by capability / location / status
- Filter drones by weather resistance
- Flag drones in maintenance

### 3) Assignment Tracking (Recommendation)
- Suggest best pilots for a mission based on:
  - availability
  - location
  - required skills
  - required certifications
- Suggest best drones based on:
  - availability
  - location
  - weather compatibility

### 4) Conflict Detection
- Skill mismatch warnings
- Certification mismatch warnings
- Location mismatch alerts
- Maintenance conflicts
- Weather risk alerts
- Budget overrun warnings (pilot cost > mission budget)
- Double booking checks (only if missions sheet includes assigned_pilots and assigned_drones columns)

### 5) Urgent Reassignments
- Provides replacement recommendations for urgent missions
- Shows conflicts + best alternatives

---

## Data Sources 

This agent reads from 3 Google Sheets (3 separate spreadsheet files):

- Pilot roster spreadsheet
- Drone fleet spreadsheet
- Missions spreadsheet

Write-back sync is implemented for:
- Pilot status updates (pilot_roster sheet)

---

## Commands Supported 

### Pilot queries
- show pilots status=available
- show pilots location=mumbai
- show pilots skill=mapping location=bangalore
- show pilots cert=dgca
- 
Update pilot status (sync back)
- update pilot P001 status=On Leave
- update pilot P001 status=Available
- 
Pilot cost
- pilot cost P001 start=2026-02-06 end=2026-02-08

Drone queries
- show drones status=available
- show drones location=mumbai
- show drones capability=thermal
- show drones weather=rainy
- 
Conflicts
- check conflicts mission=PRJ001
- 
Assignment recommendation
- assign mission PRJ001
- 
Urgent reassignment
- urgent replacement mission=PRJ002
- 
Tech Stack
- Python
- Gradio
- Pandas
- gspread + google-auth
- 
Repository Structure
- app.py
- sheets_client.py
- ops_agent.py
- matcher.py
- conflicts.py
- utils.py
- requirements.txt
- README.md
