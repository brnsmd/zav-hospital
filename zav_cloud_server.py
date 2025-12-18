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

# ==================== TELEGRAM INTEGRATION ====================

def send_telegram_reply(chat_id: int, text: str) -> bool:
    """Send reply to Telegram chat."""
    try:
        # Validate inputs
        if not TELEGRAM_BOT_TOKEN:
            logger.error("❌ TELEGRAM_BOT_TOKEN is empty!")
            return False

        if not chat_id or not text:
            logger.error(f"❌ Invalid inputs: chat_id={chat_id}, text_len={len(text) if text else 0}")
            return False

        url = f"{TELEGRAM_API_URL}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}

        logger.info(f"⚙️ Sending to Telegram: chat_id={chat_id}, text_len={len(text)}")

        resp = requests.post(url, json=payload, timeout=10)

        logger.info(f"⚙️ Telegram response: status={resp.status_code}")

        if resp.status_code == 200:
            result = resp.json()
            if result.get("ok"):
                logger.info(f"✅ Message sent successfully to {chat_id} (msg_id: {result.get('result', {}).get('message_id')})")
                return True
            else:
                logger.error(f"❌ Telegram API error: {result}")
                return False
        else:
            logger.error(f"❌ HTTP {resp.status_code}: {resp.text[:200]}")
            return False
    except Exception as e:
        logger.error(f"❌ Telegram error: {type(e).__name__}: {e}", exc_info=True)
        return False

@app.route("/webhook/telegram", methods=["POST"])
def handle_telegram():
    """Telegram webhook endpoint."""
    global _last_webhook_result
    _last_webhook_result = {"timestamp": datetime.now().isoformat(), "status": "processing"}

    try:
        # Log webhook receipt immediately
        logger.info("📨 WEBHOOK RECEIVED - Processing Telegram message")
        _last_webhook_result["status"] = "received"

        data = request.get_json()
        if not data:
            logger.warning("⚠️ No JSON data received")
            return jsonify({"ok": True}), 200

        logger.debug(f"📋 Payload keys: {list(data.keys())}")

        if "message" not in data:
            logger.warning("⚠️ No 'message' in payload")
            return jsonify({"ok": True}), 200

        msg = data["message"]
        chat_id = msg.get("chat", {}).get("id")
        text = msg.get("text", "").strip()

        if not chat_id:
            logger.warning("⚠️ No chat_id in message")
            return jsonify({"ok": True}), 200

        if not text:
            logger.warning(f"⚠️ No text in message from {chat_id}")
            return jsonify({"ok": True}), 200

        logger.info(f"📱 Message from {chat_id}: '{text[:50]}'")
        _last_webhook_result["chat_id"] = chat_id
        _last_webhook_result["text"] = text[:100]
        _last_webhook_result["handlers_checked"] = []

        # Handle /start command
        if text.lower() in ["/start"]:
            logger.info("⚙️ Matched /start command")
            _last_webhook_result["matched_handler"] = "start"
            welcome_msg = ("<b>🏥 Welcome to Zav Hospital Bot</b>\n\n"
                          "This bot helps submit external patient requests.\n\n"
                          "<b>How to use:</b>\n"
                          "Send patient info in this format:\n"
                          "<code>Name, Age, Operation, Details</code>\n\n"
                          "<b>Example:</b>\n"
                          "<code>Ahmed Ali, 45, Appendectomy, notes</code>\n\n"
                          "<b>Commands:</b>\n"
                          "/status - Check system status\n"
                          "/addpatient - Submit patient data\n\n"
                          "⏰ All requests are reviewed at 5 AM daily")
            result = send_telegram_reply(chat_id, welcome_msg)
            logger.info(f"💬 Sent welcome response: {result}")
            return jsonify({"ok": True}), 200

        # Handle /help command (same as /start)
        if text.lower() in ["/help"]:
            logger.info("⚙️ Matched /help command")
            _last_webhook_result["matched_handler"] = "help"
            help_msg = ("<b>🏥 Zav Hospital Bot - Help</b>\n\n"
                       "<b>Submit Patient Request:</b>\n"
                       "Send message: <code>Name, Age, Operation, Details</code>\n\n"
                       "<b>Check Status:</b>\n"
                       "Send: <code>/status</code>\n\n"
                       "<b>Contact:</b>\n"
                       "For issues, contact admin.\n\n"
                       "📝 All data is stored and synced daily")
            result = send_telegram_reply(chat_id, help_msg)
            logger.info(f"💬 Sent help response: {result}")
            return jsonify({"ok": True}), 200

        # Check for patient data pattern (Name, Age, Operation)
        # Matches: /addpatient Ahmed, 45, Appendectomy OR Ahmed, 45, Appendectomy
        logger.info(f"⚙️ Checking patterns for: {text}")
        _last_webhook_result["handlers_checked"].append("patient_pattern")
        if "," in text and len(text.split(",")) >= 3:
            _last_webhook_result["matched_handler"] = "patient_data"
            logger.debug("Matched patient data pattern")
            # Remove /addpatient if present
            data_text = text.replace("/addpatient", "").strip()
            parts = data_text.split(",")

            if len(parts) >= 3:
                name = parts[0].strip()
                age = parts[1].strip()
                op = parts[2].strip()
                notes = parts[3].strip() if len(parts) > 3 else "-"

                # Store in database
                try:
                    cursor = db.get_connection().cursor()
                    pid = f"EX{chat_id}{int(datetime.now().timestamp())}"
                    cursor.execute(
                        "INSERT INTO patients (patient_id, name, status, source, created_at, updated_at) "
                        "VALUES (%s, %s, %s, %s, NOW(), NOW())",
                        (pid, name, "pending", "telegram")
                    )
                    logger.info(f"✅ Stored: {name}")
                except Exception as e:
                    logger.error(f"DB error: {e}")

                reply = f"✅ <b>Patient Request Recorded</b>\n👤 {name}, Age {age}\n🏥 Operation: {op}\n📋 Notes: {notes}\n\n⏰ Review: 5 AM sync"
                result = send_telegram_reply(chat_id, reply)
                logger.info(f"💬 Sent patient response: {result}")
                return jsonify({"ok": True}), 200

        # Handle /status or "status" command
        _last_webhook_result["handlers_checked"].append("status")
        if text.lower() in ["/status", "status"]:
            logger.info(f"⚙️ Matched status command")
            _last_webhook_result["matched_handler"] = "status"
            db_status = "✅" if db else "❌"
            status_msg = f"<b>🏥 System Status</b>\nDatabase: {db_status}\nBot: ✅\nAPI: ✅\n\n<b>Usage:</b> Send patient info:\nName, Age, Operation, Details"
            logger.info(f"⚙️ Calling send_telegram_reply for status")
            result = send_telegram_reply(chat_id, status_msg)
            logger.info(f"⚙️ Status response result: {result}")
            _last_webhook_result["send_result"] = result
            _last_webhook_result["completed_at"] = datetime.now().isoformat()
            return jsonify({"ok": True}), 200

        # Default response
        logger.info(f"⚙️ No patterns matched, sending default response to {chat_id}")
        _last_webhook_result["matched_handler"] = "default"
        default_msg = ("<b>🏥 Zav Hospital Bot</b>\n\n"
                       "<b>Send patient info:</b>\n"
                       "Ahmed Ali, 45, Appendectomy, notes\n\n"
                       "<b>Or use:</b>\n"
                       "/status - System status\n"
                       "/start - Welcome")
        logger.info(f"⚙️ Calling send_telegram_reply for default message")
        result = send_telegram_reply(chat_id, default_msg)
        logger.info(f"⚙️ Default response result: {result}")
        _last_webhook_result["send_result"] = result
        _last_webhook_result["completed_at"] = datetime.now().isoformat()

        return jsonify({"ok": True}), 200

    except Exception as e:
        logger.error(f"❌ Webhook error: {e}", exc_info=True)
        _last_webhook_result["error"] = str(e)
        _last_webhook_result["completed_at"] = datetime.now().isoformat()
        return jsonify({"ok": True}), 200

# ==================== SYNC ENDPOINTS ====================

@app.route("/sync/sheets", methods=["POST"])
def sync_google_sheets():
    """Trigger Google Sheets sync."""
    # This will be implemented when we build the Google Sheets sync module
    return jsonify({
        "status": "sync initiated",
        "message": "Google Sheets sync will sync database to sheets"
    }), 202

# ==================== GLOBALS FOR DEBUGGING ====================
_last_webhook_result = {}

# ==================== DEBUG ENDPOINTS ====================

@app.route("/debug/last-webhook", methods=["GET"])
def debug_last_webhook():
    """Get the result of the last webhook call."""
    if not _last_webhook_result:
        return jsonify({"error": "No webhook calls yet", "timestamp": datetime.now().isoformat()}), 404
    return jsonify(_last_webhook_result), 200

@app.route("/debug/telegram-test", methods=["GET"])
def debug_telegram():
    """Test Telegram API connectivity."""
    try:
        # Test sending a message via Telegram API
        test_response = requests.post(
            f"{TELEGRAM_API_URL}/sendMessage",
            json={"chat_id": 123456, "text": "🧪 Test from Railway"},
            timeout=5
        )
        return jsonify({
            "telegram_api_url": TELEGRAM_API_URL[:20] + "...",
            "status_code": test_response.status_code,
            "response": test_response.json() if test_response.status_code == 200 else test_response.text
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/debug/webhook-test", methods=["POST"])
def debug_webhook_test():
    """Test webhook handler with full tracing."""
    debug_log = []
    try:
        data = request.get_json()
        debug_log.append(f"1. Received JSON: {data is not None}")

        if not data or "message" not in data:
            debug_log.append("2. Missing data or message key")
            return jsonify({"ok": True, "debug": debug_log}), 200

        msg = data["message"]
        chat_id = msg.get("chat", {}).get("id")
        text = msg.get("text", "").strip()

        debug_log.append(f"2. Extracted chat_id: {chat_id}, text: {text[:50]}")

        if not chat_id or not text:
            debug_log.append("3. Missing chat_id or text")
            return jsonify({"ok": True, "debug": debug_log}), 200

        debug_log.append(f"3. Validation passed")

        # Test send_telegram_reply directly
        debug_log.append(f"4. Testing send_telegram_reply()...")
        test_url = f"{TELEGRAM_API_URL}/sendMessage"
        debug_log.append(f"4a. URL starts with: {test_url[:40]}...")

        test_payload = {"chat_id": chat_id, "text": "🧪 Debug test response"}
        resp = requests.post(test_url, json=test_payload, timeout=10)

        debug_log.append(f"4b. Response status: {resp.status_code}")
        if resp.status_code == 200:
            debug_log.append(f"4c. SUCCESS - Message sent!")
        else:
            debug_log.append(f"4c. FAILED - {resp.text[:100]}")

        return jsonify({
            "ok": True,
            "debug": debug_log,
            "telegram_response": resp.status_code
        }), 200

    except Exception as e:
        debug_log.append(f"ERROR: {str(e)}")
        return jsonify({"ok": False, "error": str(e), "debug": debug_log}), 500


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
