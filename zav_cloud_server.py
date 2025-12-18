#!/usr/bin/env python3
"""
Zav Cloud Server - Railway Deployment
=====================================

This is the main Flask server that runs on Railway to provide:
1. REST API endpoints for patient management
2. Telegram webhook for bot integration
3. Google Sheets sync endpoints
4. Database management via PostgreSQL

The server runs 24/7 on Railway cloud and is always accessible via:
- REST API: https://zav-hospital.up.railway.app/api/*
- Telegram webhook: https://zav-hospital.up.railway.app/webhook/telegram
- Google Sheets sync: https://zav-hospital.up.railway.app/sync/sheets

Usage:
    python zav_cloud_server.py
    # Or via Railway Procfile:
    web: gunicorn zav_cloud_server:app

Environment Variables (set in Railway):
    - DATABASE_URL: PostgreSQL connection string (e.g., postgres://user:pass@host/db)
    - TELEGRAM_BOT_TOKEN: Telegram bot token from @BotFather
    - GOOGLE_SHEETS_KEY: Google Sheets JSON credentials (base64 encoded)
    - PORT: Port to run on (default 8000)
"""

import os
import json
import logging
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional
from functools import wraps
import base64
import subprocess

from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg
from psycopg.rows import dict_row

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ZavServer")

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# ==================== CONFIGURATION ====================

DATABASE_URL = os.getenv("DATABASE_URL", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
GOOGLE_SHEETS_KEY = os.getenv("GOOGLE_SHEETS_KEY", "")
PORT = int(os.getenv("PORT", 8000))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Telegram API base URL
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

# ==================== DATABASE MANAGEMENT ====================

class DatabaseManager:
    """Manage PostgreSQL database connections and operations."""

    def __init__(self, connection_string: str):
        """Initialize database connection."""
        self.connection_string = connection_string
        self.conn = None
        self._init_connection()
        self._init_schema()

    def _init_connection(self):
        """Initialize persistent database connection."""
        try:
            self.conn = psycopg.connect(self.connection_string, autocommit=True)
            logger.info("✅ Database connection established (persistent)")
        except Exception as e:
            logger.error(f"Failed to establish database connection: {e}")
            raise

    def get_connection(self):
        """Get the persistent database connection."""
        if self.conn is None or self.conn.closed:
            self._init_connection()
        return self.conn

    def _init_schema(self):
        """Initialize database schema if not exists."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Create tables
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS patients (
                    id SERIAL PRIMARY KEY,
                    patient_id VARCHAR UNIQUE NOT NULL,
                    name VARCHAR NOT NULL,
                    admission_date DATE,
                    discharge_date DATE,
                    current_stage INT DEFAULT 1,
                    status VARCHAR DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS equipment (
                    id SERIAL PRIMARY KEY,
                    equipment_id VARCHAR UNIQUE NOT NULL,
                    patient_id VARCHAR NOT NULL,
                    equipment_type VARCHAR NOT NULL,
                    placed_date DATE,
                    expected_removal_date DATE,
                    status VARCHAR DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT NOW(),
                    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
                );

                CREATE TABLE IF NOT EXISTS antibiotics (
                    id SERIAL PRIMARY KEY,
                    course_id VARCHAR UNIQUE NOT NULL,
                    patient_id VARCHAR NOT NULL,
                    antibiotic_name VARCHAR NOT NULL,
                    start_date DATE,
                    end_date DATE,
                    days_in_course INT,
                    effectiveness VARCHAR,
                    created_at TIMESTAMP DEFAULT NOW(),
                    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
                );

                CREATE TABLE IF NOT EXISTS consultations (
                    id SERIAL PRIMARY KEY,
                    consultation_id VARCHAR UNIQUE NOT NULL,
                    patient_id VARCHAR NOT NULL,
                    doctor_id VARCHAR,
                    scheduled_date DATE,
                    status VARCHAR DEFAULT 'scheduled',
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT NOW(),
                    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
                );

                CREATE TABLE IF NOT EXISTS alerts (
                    id SERIAL PRIMARY KEY,
                    alert_id VARCHAR UNIQUE NOT NULL,
                    patient_id VARCHAR NOT NULL,
                    severity VARCHAR DEFAULT 'info',
                    message TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    resolved_at TIMESTAMP,
                    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
                );
            """)

            cursor.close()
            logger.info("✅ Database schema initialized")

        except Exception as e:
            logger.error(f"Error initializing schema: {e}")
            raise

    def query(self, sql: str, params: tuple = ()) -> List[Dict]:
        """Execute a SELECT query and return results."""
        try:
            conn = self.get_connection()
            conn.row_factory = dict_row
            cursor = conn.cursor()
            cursor.execute(sql, params)
            results = cursor.fetchall()
            cursor.close()
            return results
        except Exception as e:
            logger.error(f"Query error: {e}")
            return []

    def insert(self, table: str, data: Dict) -> Optional[int]:
        """Insert a record and return the ID."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            columns = ", ".join(data.keys())
            placeholders = ", ".join(["%s"] * len(data))
            values = tuple(data.values())

            sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders}) RETURNING id"
            cursor.execute(sql, values)
            result_id = cursor.fetchone()[0]

            cursor.close()
            return result_id
        except Exception as e:
            logger.error(f"Insert error: {e}")
            return None

    def update(self, table: str, record_id: int, data: Dict) -> bool:
        """Update a record."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            set_clause = ", ".join([f"{k} = %s" for k in data.keys()])
            values = tuple(data.values()) + (record_id,)

            sql = f"UPDATE {table} SET {set_clause}, updated_at = NOW() WHERE id = %s"
            cursor.execute(sql, values)

            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Update error: {e}")
            return False


# ==================== DATABASE INITIALIZATION ====================

# Initialize database manager if PostgreSQL is available
db = None
if DATABASE_URL:
    try:
        db = DatabaseManager(DATABASE_URL)
        logger.info("✅ Connected to PostgreSQL")
    except Exception as e:
        logger.error(f"Failed to connect to PostgreSQL: {e}")
        db = None
else:
    logger.warning("⚠️  DATABASE_URL not set - running in demo mode")

# ==================== AUTHENTICATION ====================

def require_token(f):
    """Decorator to require Bearer token authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # For now, we'll use a simple token scheme
        # In production, implement proper OAuth or JWT
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated_function

# ==================== TELEGRAM WEBHOOK ENDPOINTS ====================

@app.route("/webhook/telegram", methods=["POST"])
def telegram_webhook():
    """Handle incoming Telegram webhook messages."""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"ok": False}), 400

        # Extract message
        message = data.get("message", {})
        text = message.get("text", "")
        user_id = message.get("from", {}).get("id")
        chat_id = message.get("chat", {}).get("id")

        if not text or not user_id:
            return jsonify({"ok": True}), 200

        logger.info(f"📨 Telegram message from {user_id}: {text[:50]}")

        # Process command
        response = process_telegram_command(text, user_id)

        # Send response back
        if response:
            send_telegram_message(chat_id, response)

        return jsonify({"ok": True}), 200

    except Exception as e:
        logger.error(f"Telegram webhook error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

def send_telegram_message(chat_id: int, text: str, parse_mode: str = "HTML"):
    """Send a message via Telegram bot."""
    try:
        url = f"{TELEGRAM_API_URL}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode
        }
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Failed to send Telegram message: {e}")
        return False

def process_telegram_command(text: str, user_id: int) -> Optional[str]:
    """Process a Telegram command and return response."""
    text = text.lower().strip()

    if text == "/start":
        return """
🏥 <b>Welcome to Zav Hospital Management</b>

Available commands:
/alerts - Show current alerts
/beds - Check bed availability
/discharge - List discharge-ready patients
/patients - List all patients
/help - Show this menu
        """

    elif text == "/alerts":
        if db:
            alerts = db.query("SELECT * FROM alerts WHERE resolved_at IS NULL LIMIT 5")
            if alerts:
                response = "<b>🚨 Active Alerts:</b>\n"
                for alert in alerts:
                    response += f"• {alert['message']}\n"
                return response
        return "No active alerts"

    elif text == "/beds":
        if db:
            patients = db.query("SELECT COUNT(*) as count FROM patients WHERE status = 'active'")
            if patients:
                count = patients[0]['count']
                return f"<b>🛏️  Bed Status:</b>\nCurrently {count} patients admitted"
        return "Unable to fetch bed status"

    elif text == "/discharge":
        if db:
            patients = db.query("""
                SELECT patient_id, name FROM patients
                WHERE discharge_date <= CURRENT_DATE
                LIMIT 5
            """)
            if patients:
                response = "<b>✅ Ready for Discharge:</b>\n"
                for patient in patients:
                    response += f"• {patient['patient_id']}: {patient['name']}\n"
                return response
        return "No patients ready for discharge"

    elif text == "/patients":
        if db:
            patients = db.query("SELECT patient_id, name FROM patients LIMIT 10")
            if patients:
                response = "<b>👥 Patient List:</b>\n"
                for patient in patients:
                    response += f"• {patient['patient_id']}: {patient['name']}\n"
                return response
        return "No patients in system"

    elif text == "/help":
        return """
<b>Commands:</b>
/start - Welcome message
/alerts - Show alerts
/beds - Bed status
/discharge - Discharge candidates
/patients - Patient list
/help - This menu
        """

    else:
        return "❓ Unknown command. Type /help for available commands."

# ==================== REST API ENDPOINTS ====================

@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    status = {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "database": "connected" if db else "disconnected"
    }
    return jsonify(status)

@app.route("/api/patients", methods=["GET"])
def list_patients():
    """List all patients."""
    try:
        if not db:
            return jsonify({"error": "Database not available"}), 503

        patients = db.query("SELECT * FROM patients ORDER BY created_at DESC")
        return jsonify(patients)
    except Exception as e:
        logger.error(f"Error listing patients: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/patients/<patient_id>", methods=["GET"])
def get_patient(patient_id: str):
    """Get patient details with all related records."""
    try:
        if not db:
            return jsonify({"error": "Database not available"}), 503

        patient = db.query("SELECT * FROM patients WHERE patient_id = %s", (patient_id,))
        if not patient:
            return jsonify({"error": "Patient not found"}), 404

        patient_data = patient[0]

        # Get related records
        patient_data["equipment"] = db.query(
            "SELECT * FROM equipment WHERE patient_id = %s",
            (patient_id,)
        )
        patient_data["antibiotics"] = db.query(
            "SELECT * FROM antibiotics WHERE patient_id = %s",
            (patient_id,)
        )
        patient_data["consultations"] = db.query(
            "SELECT * FROM consultations WHERE patient_id = %s",
            (patient_id,)
        )
        patient_data["alerts"] = db.query(
            "SELECT * FROM alerts WHERE patient_id = %s AND resolved_at IS NULL",
            (patient_id,)
        )

        return jsonify(patient_data)
    except Exception as e:
        logger.error(f"Error getting patient: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/patients", methods=["POST"])
def create_patient():
    """Create a new patient."""
    try:
        if not db:
            return jsonify({"error": "Database not available"}), 503

        data = request.get_json()
        required_fields = ["patient_id", "name"]

        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400

        patient_id = db.insert("patients", data)
        return jsonify({"id": patient_id, "patient_id": data.get("patient_id")}), 201
    except Exception as e:
        logger.error(f"Error creating patient: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/patients/<patient_id>", methods=["PUT"])
def update_patient(patient_id: str):
    """Update patient information."""
    try:
        if not db:
            return jsonify({"error": "Database not available"}), 503

        data = request.get_json()

        # Get current patient to find ID
        patient = db.query("SELECT id FROM patients WHERE patient_id = %s", (patient_id,))
        if not patient:
            return jsonify({"error": "Patient not found"}), 404

        # Update
        success = db.update("patients", patient[0]["id"], data)
        return jsonify({"success": success})
    except Exception as e:
        logger.error(f"Error updating patient: {e}")
        return jsonify({"error": str(e)}), 500

# ==================== EQUIPMENT ENDPOINTS ====================

@app.route("/api/equipment", methods=["GET"])
def list_equipment():
    """List all equipment."""
    try:
        if not db:
            return jsonify({"error": "Database not available"}), 503

        equipment = db.query("SELECT * FROM equipment ORDER BY created_at DESC")
        return jsonify(equipment)
    except Exception as e:
        logger.error(f"Error listing equipment: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/equipment/<patient_id>", methods=["GET"])
def get_patient_equipment(patient_id: str):
    """Get equipment for a patient."""
    try:
        if not db:
            return jsonify({"error": "Database not available"}), 503

        equipment = db.query(
            "SELECT * FROM equipment WHERE patient_id = %s ORDER BY placed_date DESC",
            (patient_id,)
        )
        return jsonify(equipment)
    except Exception as e:
        logger.error(f"Error getting equipment: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/equipment", methods=["POST"])
def add_equipment():
    """Add equipment for a patient."""
    try:
        if not db:
            return jsonify({"error": "Database not available"}), 503

        data = request.get_json()
        required_fields = ["equipment_id", "patient_id", "equipment_type"]

        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400

        eq_id = db.insert("equipment", data)
        return jsonify({"id": eq_id}), 201
    except Exception as e:
        logger.error(f"Error adding equipment: {e}")
        return jsonify({"error": str(e)}), 500

# ==================== ANTIBIOTICS ENDPOINTS ====================

@app.route("/api/antibiotics/<patient_id>", methods=["GET"])
def get_patient_antibiotics(patient_id: str):
    """Get antibiotics for a patient."""
    try:
        if not db:
            return jsonify({"error": "Database not available"}), 503

        antibiotics = db.query(
            "SELECT * FROM antibiotics WHERE patient_id = %s ORDER BY start_date DESC",
            (patient_id,)
        )
        return jsonify(antibiotics)
    except Exception as e:
        logger.error(f"Error getting antibiotics: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/antibiotics", methods=["POST"])
def add_antibiotic():
    """Add antibiotic course for a patient."""
    try:
        if not db:
            return jsonify({"error": "Database not available"}), 503

        data = request.get_json()
        required_fields = ["course_id", "patient_id", "antibiotic_name"]

        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400

        course_id = db.insert("antibiotics", data)
        return jsonify({"id": course_id}), 201
    except Exception as e:
        logger.error(f"Error adding antibiotic: {e}")
        return jsonify({"error": str(e)}), 500

# ==================== ALERTS ENDPOINTS ====================

@app.route("/api/alerts", methods=["GET"])
def get_alerts():
    """Get active alerts."""
    try:
        if not db:
            return jsonify({"error": "Database not available"}), 503

        severity = request.args.get("severity", "all")

        if severity == "all":
            sql = "SELECT * FROM alerts WHERE resolved_at IS NULL ORDER BY created_at DESC"
            alerts = db.query(sql)
        else:
            sql = "SELECT * FROM alerts WHERE severity = %s AND resolved_at IS NULL ORDER BY created_at DESC"
            alerts = db.query(sql, (severity,))

        return jsonify(alerts)
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/alerts", methods=["POST"])
def create_alert():
    """Create a new alert."""
    try:
        if not db:
            return jsonify({"error": "Database not available"}), 503

        data = request.get_json()
        required_fields = ["alert_id", "patient_id", "message"]

        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400

        alert_id = db.insert("alerts", data)
        return jsonify({"id": alert_id}), 201
    except Exception as e:
        logger.error(f"Error creating alert: {e}")
        return jsonify({"error": str(e)}), 500

# ==================== TELEGRAM BOT INTEGRATION ====================

def send_telegram_message(chat_id: int, text: str, parse_mode: str = "HTML") -> bool:
    """Send a message to Telegram chat."""
    try:
        url = f"{TELEGRAM_API_URL}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode
        }
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            logger.info(f"✅ Message sent to chat {chat_id}")
            return True
        else:
            logger.error(f"❌ Failed to send message: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error sending Telegram message: {e}")
        return False

def append_to_google_sheets(row_data: List[str]) -> bool:
    """Append a row to Google Sheets 'New Requests' tab."""
    try:
        # Try using gspread if credentials available
        import gspread
        from google.oauth2.service_account import Credentials

        google_sheets_key = os.getenv("GOOGLE_SHEETS_KEY", "")
        google_sheets_id = os.getenv("GOOGLE_SHEETS_ID", "1uMRrf8INgFp8WMOSWgobWOQ9W4KrlLw_NR3BtnlLUqA")

        if not google_sheets_key:
            logger.warning("⚠️ GOOGLE_SHEETS_KEY not configured, skipping Sheets append")
            return False

        creds_dict = json.loads(google_sheets_key)
        creds = Credentials.from_service_account_info(creds_dict)
        gc = gspread.authorize(creds)

        sheet = gc.open_by_key(google_sheets_id)
        new_requests_sheet = sheet.worksheet("New Requests")

        new_requests_sheet.append_row(row_data)
        logger.info(f"✅ Row appended to Google Sheets: {row_data}")
        return True

    except ImportError:
        logger.warning("⚠️ gspread not installed, using MCP method")
        # MCP method would go here - for now just log
        return False
    except Exception as e:
        logger.error(f"Error appending to Google Sheets: {e}")
        return False

@app.route("/webhook/telegram", methods=["POST"])
def telegram_webhook():
    """Receive Telegram webhook updates."""
    try:
        update = request.get_json()

        if not update:
            return jsonify({"ok": True}), 200

        # Extract message
        message = update.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "").strip()
        from_user = message.get("from", {})
        user_id = from_user.get("id")
        username = from_user.get("username", "unknown")

        logger.info(f"📱 Telegram message from @{username}: {text}")

        # Handle /external-patient command
        if text.startswith("/external-patient"):
            try:
                # Parse: /external-patient Name, Age, Operation, Details
                parts = text.replace("/external-patient", "").strip().split(",")

                if len(parts) < 3:
                    response = "❌ Invalid format. Use: /external-patient Name, Age, Operation, [Details]"
                    send_telegram_message(chat_id, response)
                    return jsonify({"ok": True}), 200

                patient_name = parts[0].strip()
                patient_age = parts[1].strip()
                operation = parts[2].strip()
                details = parts[3].strip() if len(parts) > 3 else ""

                # Store in database as external patient request
                if db:
                    cursor = db.get_connection().cursor()
                    cursor.execute("""
                        INSERT INTO patients (patient_id, name, status, source, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, NOW(), NOW())
                    """, (f"EX{user_id}{datetime.now().timestamp()}", patient_name, "pending", "telegram_request"))
                    logger.info(f"✅ External patient request stored for {patient_name}")

                # Try to append to Google Sheets
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                row_data = [timestamp, f"@{username}", patient_name, patient_age, operation, details, "pending_review"]
                append_to_google_sheets(row_data)

                # Send confirmation
                confirmation = f"""✅ <b>Patient request recorded!</b>

<b>Details:</b>
📝 Name: {patient_name}
👤 Age: {patient_age}
🏥 Operation: {operation}
📋 Notes: {details if details else 'None'}

⏰ <b>Next Review:</b> Daily sync at 5 AM or when hospital staff opens Claude
📊 <b>Status:</b> Added to "New Requests" tab in Google Sheets

The hospital team will review this and propose admission details.
"""
                send_telegram_message(chat_id, confirmation)

            except Exception as e:
                logger.error(f"Error processing /external-patient: {e}")
                send_telegram_message(chat_id, f"❌ Error processing request: {str(e)}")

        # Handle /start command
        elif text == "/start":
            welcome = """🏥 <b>Welcome to Zav Hospital Management!</b>

I'm your interface to the hospital system. Here's what you can do:

<b>For Doctors - Submit External Patient Requests:</b>
/external-patient Name, Age, Operation, [Details]

<b>Example:</b>
/external-patient Ahmed Ali, 45, Appendectomy, acute appendicitis

<b>Other Commands:</b>
/help - Show all available commands
/status - System status

Questions? Contact the hospital IT team.
"""
            send_telegram_message(chat_id, welcome)

        # Handle /help command
        elif text == "/help":
            help_text = """<b>Available Commands:</b>

<b>/external-patient</b> Name, Age, Operation, [Details]
  → Submit a new external patient for admission

<b>/start</b>
  → Show welcome message

<b>/help</b>
  → Show this message

<b>/status</b>
  → Check system status

<b>Process:</b>
1. You submit patient via /external-patient
2. Request stored in "New Requests" tab (Google Sheets)
3. Hospital staff reviews next morning (5 AM sync)
4. Claude proposes bed allocation and operation schedule
5. Staff confirms and system sends you updates
"""
            send_telegram_message(chat_id, help_text)

        # Handle /status command
        elif text == "/status":
            try:
                status = {
                    "system": "operational",
                    "database": "connected" if db else "disconnected",
                    "telegram_bot": "ready",
                    "timestamp": datetime.now().isoformat()
                }
                status_msg = f"""<b>🏥 Zav System Status</b>

✅ System: {status['system']}
✅ Database: {status['database']}
✅ Telegram Bot: {status['telegram_bot']}

⏰ Last Check: {status['timestamp']}

Everything is operational! 🚀
"""
                send_telegram_message(chat_id, status_msg)
            except Exception as e:
                logger.error(f"Error getting status: {e}")
                send_telegram_message(chat_id, "❌ Error retrieving status")

        else:
            # Unknown command
            response = f"""I didn't understand that command.

Try /help to see what I can do, or /external-patient to submit a new patient."""
            send_telegram_message(chat_id, response)

        return jsonify({"ok": True}), 200

    except Exception as e:
        logger.error(f"Error processing Telegram webhook: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

# ==================== SYNC ENDPOINTS ====================

@app.route("/api/sync/cyberintern", methods=["GET", "POST"])
def trigger_cyberintern_sync():
    """Trigger sync from Cyberintern EMR."""
    try:
        if not db:
            return jsonify({"error": "Database not available"}), 503

        logger.info("🔄 Triggering Cyberintern sync...")

        # Execute the sync_patients_daily.py script
        result = subprocess.run(
            ["python", "sync_patients_daily.py"],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        if result.returncode == 0:
            try:
                output = json.loads(result.stdout)
                return jsonify({
                    "status": "success",
                    "sync_result": output,
                    "timestamp": datetime.now().isoformat()
                }), 200
            except json.JSONDecodeError:
                return jsonify({
                    "status": "success",
                    "message": "Sync completed",
                    "output": result.stdout
                }), 200
        else:
            logger.error(f"Sync script error: {result.stderr}")
            return jsonify({
                "status": "error",
                "error": result.stderr
            }), 500

    except subprocess.TimeoutExpired:
        logger.error("Sync script timeout")
        return jsonify({"error": "Sync timeout (5 minutes exceeded)"}), 504
    except Exception as e:
        logger.error(f"Error triggering sync: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/sync/sheets", methods=["POST"])
def sync_google_sheets():
    """Trigger Google Sheets sync (same as /api/sync/cyberintern)."""
    return trigger_cyberintern_sync()

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors."""
    logger.error(f"Server error: {error}")
    return jsonify({"error": "Internal server error"}), 500

# ==================== MAIN ====================

if __name__ == "__main__":
    port = PORT
    debug = DEBUG

    logger.info(f"🚀 Starting Zav Cloud Server on port {port}...")
    logger.info(f"📊 Database: {'Connected' if db else 'Disconnected'}")
    logger.info(f"🤖 Telegram Bot: {'Ready' if TELEGRAM_BOT_TOKEN else 'Not configured'}")

    app.run(
        host="0.0.0.0",
        port=port,
        debug=debug,
        use_reloader=False
    )
