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
                    source VARCHAR DEFAULT 'manual',
                    operation VARCHAR,
                    age VARCHAR,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                );

                -- Add columns to existing table if missing
                ALTER TABLE patients ADD COLUMN IF NOT EXISTS source VARCHAR DEFAULT 'manual';
                ALTER TABLE patients ADD COLUMN IF NOT EXISTS operation VARCHAR;
                ALTER TABLE patients ADD COLUMN IF NOT EXISTS age VARCHAR;
                ALTER TABLE patients ADD COLUMN IF NOT EXISTS notes TEXT;
                ALTER TABLE patients ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP;
                ALTER TABLE patients ADD COLUMN IF NOT EXISTS approved_by VARCHAR;
                ALTER TABLE patients ADD COLUMN IF NOT EXISTS assigned_doctor_id VARCHAR;
                ALTER TABLE patients ADD COLUMN IF NOT EXISTS assigned_doctor_name VARCHAR;
                ALTER TABLE patients ADD COLUMN IF NOT EXISTS hospitalization_date DATE;
                ALTER TABLE patients ADD COLUMN IF NOT EXISTS rejection_reason TEXT;
                ALTER TABLE patients ADD COLUMN IF NOT EXISTS external_doctor_chat_id BIGINT;

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

                CREATE TABLE IF NOT EXISTS webhook_log (
                    id SERIAL PRIMARY KEY,
                    received_at TIMESTAMP DEFAULT NOW(),
                    raw_data TEXT
                );

                CREATE TABLE IF NOT EXISTS doctors (
                    id SERIAL PRIMARY KEY,
                    doctor_id VARCHAR UNIQUE NOT NULL,
                    name VARCHAR NOT NULL,
                    specialization VARCHAR,
                    telegram_id BIGINT,
                    available BOOLEAN DEFAULT TRUE,
                    max_patients INT DEFAULT 12,
                    current_load INT DEFAULT 0,
                    created_at TIMESTAMP DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS operation_slots (
                    id SERIAL PRIMARY KEY,
                    slot_id VARCHAR UNIQUE NOT NULL,
                    date DATE NOT NULL,
                    time_start TIME NOT NULL,
                    time_end TIME NOT NULL,
                    or_room VARCHAR NOT NULL,
                    doctor_id VARCHAR,
                    patient_id VARCHAR,
                    operation_type VARCHAR,
                    status VARCHAR DEFAULT 'available',
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                );
            """)

            cursor.close()
            logger.info("✅ Database schema initialized")

            # Seed initial doctors if table is empty
            self._seed_doctors()

        except Exception as e:
            logger.error(f"Error initializing schema: {e}")
            raise

    def _seed_doctors(self):
        """Seed initial doctors if table is empty."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Check if doctors table is empty
            cursor.execute("SELECT COUNT(*) FROM doctors")
            count = cursor.fetchone()[0]

            if count == 0:
                logger.info("Seeding initial doctors...")
                doctors = [
                    {
                        "doctor_id": "DOC001",
                        "name": "Др. Петрова Олена",
                        "specialization": "Травматолог-ортопед",
                        "available": True,
                        "max_patients": 12,
                        "current_load": 0
                    },
                    {
                        "doctor_id": "DOC002",
                        "name": "Др. Іванов Петро",
                        "specialization": "Хірург",
                        "available": True,
                        "max_patients": 10,
                        "current_load": 0
                    },
                    {
                        "doctor_id": "DOC003",
                        "name": "Др. Коваленко Марія",
                        "specialization": "Травматолог",
                        "available": True,
                        "max_patients": 12,
                        "current_load": 0
                    }
                ]

                for doctor in doctors:
                    self.insert("doctors", doctor)

                logger.info(f"✅ Seeded {len(doctors)} doctors")

            cursor.close()
        except Exception as e:
            logger.error(f"Error seeding doctors: {e}")

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
# Main webhook handler is handle_telegram() below in TELEGRAM INTEGRATION section

# ==================== REST API ENDPOINTS ====================

@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    status = {
        "status": "ok",
        "version": "2.5-approval-workflow",  # Added approval workflow schema
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

@app.route("/api/patients/pending", methods=["GET"])
def list_pending_patients():
    """List all pending external patients."""
    try:
        if not db:
            return jsonify({"error": "Database not available"}), 503

        patients = db.query("""
            SELECT * FROM patients
            WHERE status = 'pending' AND source = 'telegram'
            ORDER BY created_at DESC
        """)
        return jsonify(patients)
    except Exception as e:
        logger.error(f"Error listing pending patients: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/patients/<patient_id>/approve", methods=["PUT"])
def approve_patient(patient_id: str):
    """Approve a pending patient with scheduling information."""
    try:
        if not db:
            return jsonify({"error": "Database not available"}), 503

        data = request.get_json()
        required_fields = ["hospitalization_date", "assigned_doctor_id", "operation_slot_id"]

        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields: hospitalization_date, assigned_doctor_id, operation_slot_id"}), 400

        # Get patient
        patient = db.query("SELECT * FROM patients WHERE patient_id = %s", (patient_id,))
        if not patient:
            return jsonify({"error": "Patient not found"}), 404

        if patient[0]["status"] != "pending":
            return jsonify({"error": "Patient is not pending"}), 400

        # Get doctor name
        doctor = db.query("SELECT name FROM doctors WHERE doctor_id = %s", (data["assigned_doctor_id"],))
        doctor_name = doctor[0]["name"] if doctor else None

        # Reserve operation slot
        slot = db.query("SELECT id FROM operation_slots WHERE slot_id = %s", (data["operation_slot_id"],))
        if slot:
            db.update("operation_slots", slot[0]["id"], {
                "patient_id": patient_id,
                "doctor_id": data["assigned_doctor_id"],
                "operation_type": patient[0].get("operation"),
                "status": "reserved"
            })

        # Update patient
        update_data = {
            "status": "approved",
            "approved_at": datetime.now(),
            "approved_by": data.get("approved_by", "admin"),
            "assigned_doctor_id": data["assigned_doctor_id"],
            "assigned_doctor_name": doctor_name,
            "hospitalization_date": data["hospitalization_date"]
        }

        success = db.update("patients", patient[0]["id"], update_data)

        logger.info(f"✅ Approved patient {patient_id} for {data['hospitalization_date']}")

        return jsonify({"success": success, "patient_id": patient_id})
    except Exception as e:
        logger.error(f"Error approving patient: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/patients/<patient_id>/reject", methods=["PUT"])
def reject_patient(patient_id: str):
    """Reject a pending patient request."""
    try:
        if not db:
            return jsonify({"error": "Database not available"}), 503

        data = request.get_json()
        if not data.get("rejection_reason"):
            return jsonify({"error": "rejection_reason required"}), 400

        # Get patient
        patient = db.query("SELECT * FROM patients WHERE patient_id = %s", (patient_id,))
        if not patient:
            return jsonify({"error": "Patient not found"}), 404

        if patient[0]["status"] != "pending":
            return jsonify({"error": "Patient is not pending"}), 400

        # Update patient
        update_data = {
            "status": "rejected",
            "rejection_reason": data["rejection_reason"]
        }

        success = db.update("patients", patient[0]["id"], update_data)

        logger.info(f"❌ Rejected patient {patient_id}: {data['rejection_reason']}")

        return jsonify({"success": success, "patient_id": patient_id})
    except Exception as e:
        logger.error(f"Error rejecting patient: {e}")
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

# ==================== DOCTOR MANAGEMENT ENDPOINTS ====================

@app.route("/api/doctors", methods=["GET"])
def list_doctors():
    """List all doctors."""
    try:
        if not db:
            return jsonify({"error": "Database not available"}), 503

        doctors = db.query("SELECT * FROM doctors ORDER BY name")
        return jsonify(doctors)
    except Exception as e:
        logger.error(f"Error listing doctors: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/doctors/<doctor_id>", methods=["GET"])
def get_doctor(doctor_id: str):
    """Get doctor details."""
    try:
        if not db:
            return jsonify({"error": "Database not available"}), 503

        doctor = db.query("SELECT * FROM doctors WHERE doctor_id = %s", (doctor_id,))
        if not doctor:
            return jsonify({"error": "Doctor not found"}), 404

        return jsonify(doctor[0])
    except Exception as e:
        logger.error(f"Error getting doctor: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/doctors", methods=["POST"])
def create_doctor():
    """Create a new doctor."""
    try:
        if not db:
            return jsonify({"error": "Database not available"}), 503

        data = request.get_json()
        required_fields = ["doctor_id", "name"]

        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400

        doctor_id = db.insert("doctors", data)
        return jsonify({"id": doctor_id, "doctor_id": data.get("doctor_id")}), 201
    except Exception as e:
        logger.error(f"Error creating doctor: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/doctors/<int:doctor_db_id>", methods=["PUT"])
def update_doctor(doctor_db_id: int):
    """Update doctor information."""
    try:
        if not db:
            return jsonify({"error": "Database not available"}), 503

        data = request.get_json()
        success = db.update("doctors", doctor_db_id, data)
        return jsonify({"success": success})
    except Exception as e:
        logger.error(f"Error updating doctor: {e}")
        return jsonify({"error": str(e)}), 500

# ==================== OPERATION SLOT ENDPOINTS ====================

@app.route("/api/operation-slots", methods=["GET"])
def list_operation_slots():
    """List operation slots with optional date filter."""
    try:
        if not db:
            return jsonify({"error": "Database not available"}), 503

        date_filter = request.args.get("date")
        status_filter = request.args.get("status", "available")

        if date_filter:
            sql = "SELECT * FROM operation_slots WHERE date = %s AND status = %s ORDER BY date, time_start"
            slots = db.query(sql, (date_filter, status_filter))
        else:
            sql = "SELECT * FROM operation_slots WHERE status = %s ORDER BY date, time_start LIMIT 50"
            slots = db.query(sql, (status_filter,))

        return jsonify(slots)
    except Exception as e:
        logger.error(f"Error listing operation slots: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/operation-slots/<slot_id>", methods=["GET"])
def get_operation_slot(slot_id: str):
    """Get operation slot details."""
    try:
        if not db:
            return jsonify({"error": "Database not available"}), 503

        slot = db.query("SELECT * FROM operation_slots WHERE slot_id = %s", (slot_id,))
        if not slot:
            return jsonify({"error": "Slot not found"}), 404

        return jsonify(slot[0])
    except Exception as e:
        logger.error(f"Error getting operation slot: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/operation-slots", methods=["POST"])
def create_operation_slot():
    """Create a new operation slot."""
    try:
        if not db:
            return jsonify({"error": "Database not available"}), 503

        data = request.get_json()
        required_fields = ["slot_id", "date", "time_start", "time_end", "or_room"]

        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400

        slot_id = db.insert("operation_slots", data)
        return jsonify({"id": slot_id, "slot_id": data.get("slot_id")}), 201
    except Exception as e:
        logger.error(f"Error creating operation slot: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/operation-slots/<int:slot_db_id>/reserve", methods=["PUT"])
def reserve_operation_slot(slot_db_id: int):
    """Reserve an operation slot for a patient."""
    try:
        if not db:
            return jsonify({"error": "Database not available"}), 503

        data = request.get_json()
        if not data.get("patient_id"):
            return jsonify({"error": "patient_id required"}), 400

        update_data = {
            "patient_id": data.get("patient_id"),
            "doctor_id": data.get("doctor_id"),
            "operation_type": data.get("operation_type"),
            "status": "reserved"
        }

        success = db.update("operation_slots", slot_db_id, update_data)
        return jsonify({"success": success})
    except Exception as e:
        logger.error(f"Error reserving operation slot: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/operation-slots/generate-weekly", methods=["POST"])
def generate_weekly_slots():
    """Generate operation slots for a week."""
    try:
        if not db:
            return jsonify({"error": "Database not available"}), 503

        data = request.get_json()
        start_date = data.get("start_date")  # YYYY-MM-DD

        if not start_date:
            return jsonify({"error": "start_date required"}), 400

        from datetime import datetime, timedelta

        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        created_count = 0

        # Generate slots for 5 weekdays
        for day_offset in range(5):
            slot_date = start + timedelta(days=day_offset)

            # OR-1 and OR-2: Morning (08:00-12:00)
            for or_room in ["OR-1", "OR-2"]:
                slot_id = f"SLOT_{slot_date.strftime('%Y%m%d')}_{or_room}_AM"
                try:
                    db.insert("operation_slots", {
                        "slot_id": slot_id,
                        "date": slot_date,
                        "time_start": "08:00",
                        "time_end": "12:00",
                        "or_room": or_room,
                        "status": "available"
                    })
                    created_count += 1
                except:
                    pass  # Slot already exists

            # OR-3: Afternoon (13:00-17:00)
            slot_id = f"SLOT_{slot_date.strftime('%Y%m%d')}_OR-3_PM"
            try:
                db.insert("operation_slots", {
                    "slot_id": slot_id,
                    "date": slot_date,
                    "time_start": "13:00",
                    "time_end": "17:00",
                    "or_room": "OR-3",
                    "status": "available"
                })
                created_count += 1
            except:
                pass  # Slot already exists

        return jsonify({"created": created_count, "start_date": start_date}), 201
    except Exception as e:
        logger.error(f"Error generating weekly slots: {e}")
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

        # Log raw request for debugging
        raw_data = request.get_data(as_text=True)
        logger.info(f"📋 Raw request: {raw_data[:500]}")
        _last_webhook_result["raw_data"] = raw_data[:200]

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

        # Handle /start command (match /start, /start@botname, /start anything)
        if text.lower().startswith("/start"):
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

        # Handle /help command (match /help, /help@botname)
        if text.lower().startswith("/help"):
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

        # Handle /pending command - list pending patients (for department head)
        if text.lower().startswith("/pending"):
            logger.info("⚙️ Matched /pending command")
            _last_webhook_result["matched_handler"] = "pending"
            pending = db.query("SELECT * FROM patients WHERE status = 'pending' AND source = 'telegram' ORDER BY created_at DESC")

            if not pending:
                msg = "✅ No pending external patient requests"
            else:
                msg = "<b>📋 Pending Patient Requests</b>\n\n"
                for p in pending:
                    msg += f"ID: <code>{p['patient_id']}</code>\n"
                    msg += f"👤 {p['name']}, Вік: {p['age']}\n"
                    msg += f"🏥 Операція: {p['operation']}\n"
                    msg += f"📝 Примітки: {p['notes']}\n\n"

            result = send_telegram_reply(chat_id, msg)
            logger.info(f"💬 Sent pending list: {result}")
            return jsonify({"ok": True}), 200

        # Handle /addpatient command without data - show help
        if text.lower().startswith("/addpatient") and "," not in text:
            logger.info("⚙️ Matched /addpatient without data")
            _last_webhook_result["matched_handler"] = "addpatient_help"
            help_msg = ("<b>📝 Add Patient</b>\n\n"
                       "To submit a patient, send:\n"
                       "<code>Name, Age, Operation, Details</code>\n\n"
                       "<b>Example:</b>\n"
                       "<code>Ahmed Ali, 45, Appendectomy, urgent</code>")
            result = send_telegram_reply(chat_id, help_msg)
            logger.info(f"💬 Sent addpatient help: {result}")
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
                        "INSERT INTO patients (patient_id, name, age, operation, notes, status, source, created_at, updated_at) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())",
                        (pid, name, age, op, notes, "pending", "telegram")
                    )
                    logger.info(f"✅ Stored patient: {name}, {age}, {op}")
                except Exception as e:
                    logger.error(f"❌ DB error storing patient: {e}")

                reply = f"✅ <b>Patient Request Recorded</b>\n👤 {name}, Age {age}\n🏥 Operation: {op}\n📋 Notes: {notes}\n\n⏰ Review: 5 AM sync"
                result = send_telegram_reply(chat_id, reply)
                logger.info(f"💬 Sent patient response: {result}")
                return jsonify({"ok": True}), 200

        # Handle /approve command - approve patient with scheduling
        if text.lower().startswith("/approve "):
            logger.info("⚙️ Matched /approve command")
            _last_webhook_result["matched_handler"] = "approve"
            parts = text.split()
            if len(parts) < 4:
                msg = "❌ Format: /approve <patient_id> <date> <doctor_id>"
                result = send_telegram_reply(chat_id, msg)
                return jsonify({"ok": True}), 200

            patient_id = parts[1]
            approval_date = parts[2]
            doctor_id = parts[3]

            # Get pending slots for that date
            slots = db.query("SELECT * FROM operation_slots WHERE date = %s AND status = 'available' LIMIT 5", (approval_date,))

            if not slots:
                msg = f"❌ No available slots for {approval_date}"
                result = send_telegram_reply(chat_id, msg)
                return jsonify({"ok": True}), 200

            # Use first available slot
            slot_id = slots[0]['slot_id']

            # Call API to approve
            try:
                approve_resp = requests.put(
                    f"http://127.0.0.1:{PORT}/api/patients/{patient_id}/approve",
                    json={
                        "hospitalization_date": approval_date,
                        "assigned_doctor_id": doctor_id,
                        "operation_slot_id": slot_id
                    },
                    timeout=5
                )

                if approve_resp.status_code == 200:
                    msg = f"✅ Patient {patient_id} approved!\n📅 Date: {approval_date}\n🏥 Slot: {slot_id}"
                else:
                    msg = f"❌ Error approving: {approve_resp.text[:100]}"

            except Exception as e:
                logger.error(f"Error calling approve API: {e}")
                msg = f"❌ Error: {str(e)}"

            result = send_telegram_reply(chat_id, msg)
            return jsonify({"ok": True}), 200

        # Handle /reject command
        if text.lower().startswith("/reject "):
            logger.info("⚙️ Matched /reject command")
            _last_webhook_result["matched_handler"] = "reject"
            parts = text.split(None, 2)
            if len(parts) < 3:
                msg = "❌ Format: /reject <patient_id> <reason>"
                result = send_telegram_reply(chat_id, msg)
                return jsonify({"ok": True}), 200

            patient_id = parts[1]
            reason = parts[2]

            try:
                reject_resp = requests.put(
                    f"http://127.0.0.1:{PORT}/api/patients/{patient_id}/reject",
                    json={"rejection_reason": reason},
                    timeout=5
                )

                if reject_resp.status_code == 200:
                    msg = f"✅ Patient {patient_id} rejected\n❌ Reason: {reason}"
                else:
                    msg = f"❌ Error rejecting: {reject_resp.text[:100]}"

            except Exception as e:
                logger.error(f"Error calling reject API: {e}")
                msg = f"❌ Error: {str(e)}"

            result = send_telegram_reply(chat_id, msg)
            return jsonify({"ok": True}), 200

        # Handle /status or "status" command (match /status, /status@botname, status)
        _last_webhook_result["handlers_checked"].append("status")
        if text.lower().startswith("/status") or text.lower() == "status":
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

@app.route("/debug/send-test/<int:chat_id>", methods=["GET"])
def debug_send_test(chat_id):
    """Send a test message to verify send_telegram_reply works."""
    test_msg = f"🧪 Test at {datetime.now().isoformat()}"
    result = send_telegram_reply(chat_id, test_msg)
    return jsonify({
        "send_result": result,
        "chat_id": chat_id,
        "message": test_msg,
        "token_set": bool(TELEGRAM_BOT_TOKEN),
        "api_url_preview": TELEGRAM_API_URL[:40] if TELEGRAM_API_URL else "EMPTY"
    }), 200

@app.route("/debug/webhook-logs", methods=["GET"])
def debug_webhook_logs():
    """Get recent webhook log entries from database."""
    try:
        cursor = db.get_connection().cursor()
        cursor.execute("SELECT * FROM webhook_log ORDER BY received_at DESC LIMIT 10")
        rows = cursor.fetchall()
        cursor.close()
        return jsonify({
            "count": len(rows),
            "logs": [{"id": r[0], "received_at": str(r[1]), "raw_data": r[2]} for r in rows]
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/debug/telegram-test", methods=["GET"])
def debug_telegram():
    """Test Telegram API connectivity."""
    try:
        logger.info(f"Testing Telegram API with token: {TELEGRAM_BOT_TOKEN[:20]}...")
        logger.info(f"Token is empty: {not TELEGRAM_BOT_TOKEN}")

        # Test sending a message via Telegram API
        test_url = f"{TELEGRAM_API_URL}/sendMessage"
        test_payload = {"chat_id": 227230975, "text": "🧪 Test message from Railway"}

        logger.info(f"Sending test to {test_url[:50]}...")
        test_response = requests.post(test_url, json=test_payload, timeout=5)

        logger.info(f"Response status: {test_response.status_code}")
        response_data = test_response.json()
        logger.info(f"Response: {response_data}")

        return jsonify({
            "token_set": bool(TELEGRAM_BOT_TOKEN),
            "token_preview": TELEGRAM_BOT_TOKEN[:20] + "..." if TELEGRAM_BOT_TOKEN else "EMPTY",
            "telegram_api_url": TELEGRAM_API_URL[:50] + "...",
            "status_code": test_response.status_code,
            "response": response_data
        }), 200
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        return jsonify({
            "error": str(e),
            "token_set": bool(TELEGRAM_BOT_TOKEN),
            "error_type": type(e).__name__
        }), 500

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
