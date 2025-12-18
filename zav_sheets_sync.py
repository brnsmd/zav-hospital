#!/usr/bin/env python3
"""
Zav Google Sheets Sync Module
==============================

This module provides bidirectional synchronization between PostgreSQL database
and Google Sheets, allowing:

1. Database → Google Sheets: Automatic sync of patient data for viewing
2. Google Sheets → Database: Manual updates from staff through sheets

The sync is useful for:
- Doctors/nurses viewing patient data in familiar spreadsheet format
- Non-technical staff managing data without complex UI
- Backup of patient data in Google Drive
- Real-time collaboration through Google Sheets comments

Usage:
    from zav_sheets_sync import GoogleSheetsSync

    sync = GoogleSheetsSync(db, sheets_url, credentials_dict)
    sync.sync_to_sheets()      # Push DB data to Sheets
    sync.sync_from_sheets()    # Pull Sheets data to DB
    sync.setup_schedule()      # Auto-sync every 5 minutes

Environment Variables:
    GOOGLE_SHEETS_KEY: Base64-encoded service account JSON credentials
    GOOGLE_SHEETS_URL: URL of the Google Sheets document
"""

import json
import logging
import base64
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import gspread
from google.oauth2.service_account import Credentials

logger = logging.getLogger("ZavSheetsSync")

class GoogleSheetsSync:
    """Bidirectional sync between PostgreSQL and Google Sheets."""

    # Google Sheets scope
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets',
              'https://www.googleapis.com/auth/drive']

    def __init__(self, db, sheets_url: str, credentials_dict: Optional[Dict] = None):
        """
        Initialize Google Sheets sync.

        Args:
            db: DatabaseManager instance with query() and insert() methods
            sheets_url: URL of the Google Sheets document
            credentials_dict: Google service account credentials dict
                             If not provided, reads from GOOGLE_SHEETS_KEY env var
        """
        self.db = db
        self.sheets_url = sheets_url
        self.client = None

        # Get credentials
        if credentials_dict is None:
            credentials_dict = self._load_credentials_from_env()

        # Authenticate with Google
        if credentials_dict:
            try:
                credentials = Credentials.from_service_account_info(
                    credentials_dict,
                    scopes=self.SCOPES
                )
                self.client = gspread.authorize(credentials)
                self.sheet = self.client.open_by_url(sheets_url)
                logger.info(f"✅ Connected to Google Sheets: {self.sheet.title}")
            except Exception as e:
                logger.error(f"Failed to authenticate with Google Sheets: {e}")
                self.client = None
        else:
            logger.warning("⚠️  No Google Sheets credentials provided")
            self.client = None

    @staticmethod
    def _load_credentials_from_env() -> Optional[Dict]:
        """Load credentials from environment variable."""
        try:
            creds_b64 = os.getenv("GOOGLE_SHEETS_KEY")
            if not creds_b64:
                return None

            # Decode from base64
            creds_json = base64.b64decode(creds_b64).decode('utf-8')
            return json.loads(creds_json)
        except Exception as e:
            logger.error(f"Failed to load credentials from env: {e}")
            return None

    def sync_to_sheets(self) -> bool:
        """Sync database data to Google Sheets."""
        if not self.client:
            logger.warning("⚠️  Google Sheets client not available")
            return False

        try:
            logger.info("📤 Starting sync: Database → Google Sheets...")

            # Sync each data type
            self._sync_patients()
            self._sync_equipment()
            self._sync_antibiotics()
            self._sync_consultations()
            self._sync_alerts()

            # Sync operation schedules
            self._sync_daily_operations()
            self._sync_weekly_operations()

            logger.info("✅ Sync complete: Database → Google Sheets")
            return True
        except Exception as e:
            logger.error(f"Sync error: {e}")
            return False

    def sync_from_sheets(self) -> bool:
        """Sync updates from Google Sheets back to database."""
        if not self.client:
            logger.warning("⚠️  Google Sheets client not available")
            return False

        try:
            logger.info("📥 Starting sync: Google Sheets → Database...")

            # Sync each data type
            self._sync_patients_from_sheets()
            self._sync_equipment_from_sheets()

            logger.info("✅ Sync complete: Google Sheets → Database")
            return True
        except Exception as e:
            logger.error(f"Sync error: {e}")
            return False

    # ==================== PATIENTS ====================

    def _sync_patients(self):
        """Sync patients to Google Sheets 'Patients' tab."""
        try:
            # Get patients from database
            patients = self.db.query("SELECT * FROM patients ORDER BY patient_id")

            if not patients:
                logger.info("No patients to sync")
                return

            # Get or create worksheet
            ws = self._get_or_create_worksheet("Patients")

            # Clear existing data
            ws.clear()

            # Add headers
            headers = ["Patient ID", "Name", "Admission Date", "Discharge Date",
                      "Stage", "Status", "Created At", "Updated At"]
            ws.append_row(headers)

            # Add patient data
            rows = []
            for patient in patients:
                rows.append([
                    patient.get("patient_id", ""),
                    patient.get("name", ""),
                    str(patient.get("admission_date", "")),
                    str(patient.get("discharge_date", "")),
                    str(patient.get("current_stage", "")),
                    patient.get("status", ""),
                    str(patient.get("created_at", "")),
                    str(patient.get("updated_at", ""))
                ])

            if rows:
                ws.append_rows(rows, value_input_option="RAW")

            logger.info(f"✅ Synced {len(rows)} patients to Sheets")
        except Exception as e:
            logger.error(f"Error syncing patients: {e}")

    def _sync_patients_from_sheets(self):
        """Pull updated patient data from Sheets to database."""
        try:
            ws = self._get_worksheet("Patients")
            if not ws:
                return

            # Get all records
            records = ws.get_all_records()

            for record in records:
                patient_id = record.get("Patient ID")
                if not patient_id:
                    continue

                # Check if patient exists
                existing = self.db.query(
                    "SELECT id FROM patients WHERE patient_id = %s",
                    (patient_id,)
                )

                update_data = {
                    "name": record.get("Name", ""),
                    "current_stage": int(record.get("Stage", 1)) if record.get("Stage") else 1,
                    "status": record.get("Status", "active")
                }

                if existing:
                    # Update existing
                    self.db.update("patients", existing[0]["id"], update_data)
                else:
                    # Insert new
                    update_data["patient_id"] = patient_id
                    self.db.insert("patients", update_data)

            logger.info(f"✅ Synced {len(records)} patients from Sheets")
        except Exception as e:
            logger.error(f"Error syncing patients from Sheets: {e}")

    # ==================== EQUIPMENT ====================

    def _sync_equipment(self):
        """Sync equipment to Google Sheets 'Equipment' tab."""
        try:
            equipment = self.db.query(
                "SELECT * FROM equipment ORDER BY patient_id, placed_date"
            )

            ws = self._get_or_create_worksheet("Equipment")
            ws.clear()

            headers = ["Equipment ID", "Patient ID", "Type", "Placed Date",
                      "Expected Removal", "Status", "Created At"]
            ws.append_row(headers)

            rows = []
            for eq in equipment:
                rows.append([
                    eq.get("equipment_id", ""),
                    eq.get("patient_id", ""),
                    eq.get("equipment_type", ""),
                    str(eq.get("placed_date", "")),
                    str(eq.get("expected_removal_date", "")),
                    eq.get("status", ""),
                    str(eq.get("created_at", ""))
                ])

            if rows:
                ws.append_rows(rows, value_input_option="RAW")

            logger.info(f"✅ Synced {len(rows)} equipment to Sheets")
        except Exception as e:
            logger.error(f"Error syncing equipment: {e}")

    def _sync_equipment_from_sheets(self):
        """Pull updated equipment data from Sheets to database."""
        try:
            ws = self._get_worksheet("Equipment")
            if not ws:
                return

            records = ws.get_all_records()

            for record in records:
                equipment_id = record.get("Equipment ID")
                if not equipment_id:
                    continue

                existing = self.db.query(
                    "SELECT id FROM equipment WHERE equipment_id = %s",
                    (equipment_id,)
                )

                update_data = {
                    "status": record.get("Status", "active")
                }

                if existing:
                    self.db.update("equipment", existing[0]["id"], update_data)
                else:
                    update_data["equipment_id"] = equipment_id
                    update_data["patient_id"] = record.get("Patient ID", "")
                    update_data["equipment_type"] = record.get("Type", "")
                    self.db.insert("equipment", update_data)

            logger.info(f"✅ Synced {len(records)} equipment from Sheets")
        except Exception as e:
            logger.error(f"Error syncing equipment from Sheets: {e}")

    # ==================== ANTIBIOTICS ====================

    def _sync_antibiotics(self):
        """Sync antibiotics to Google Sheets 'Antibiotics' tab."""
        try:
            antibiotics = self.db.query(
                "SELECT * FROM antibiotics ORDER BY patient_id, start_date"
            )

            ws = self._get_or_create_worksheet("Antibiotics")
            ws.clear()

            headers = ["Course ID", "Patient ID", "Name", "Start Date",
                      "End Date", "Days in Course", "Effectiveness", "Created At"]
            ws.append_row(headers)

            rows = []
            for ab in antibiotics:
                rows.append([
                    ab.get("course_id", ""),
                    ab.get("patient_id", ""),
                    ab.get("antibiotic_name", ""),
                    str(ab.get("start_date", "")),
                    str(ab.get("end_date", "")),
                    str(ab.get("days_in_course", "")),
                    ab.get("effectiveness", ""),
                    str(ab.get("created_at", ""))
                ])

            if rows:
                ws.append_rows(rows, value_input_option="RAW")

            logger.info(f"✅ Synced {len(rows)} antibiotics to Sheets")
        except Exception as e:
            logger.error(f"Error syncing antibiotics: {e}")

    # ==================== CONSULTATIONS ====================

    def _sync_consultations(self):
        """Sync consultations to Google Sheets 'Consultations' tab."""
        try:
            consultations = self.db.query(
                "SELECT * FROM consultations ORDER BY patient_id, scheduled_date"
            )

            ws = self._get_or_create_worksheet("Consultations")
            ws.clear()

            headers = ["Consultation ID", "Patient ID", "Doctor ID", "Scheduled Date",
                      "Status", "Notes", "Created At"]
            ws.append_row(headers)

            rows = []
            for cons in consultations:
                rows.append([
                    cons.get("consultation_id", ""),
                    cons.get("patient_id", ""),
                    cons.get("doctor_id", ""),
                    str(cons.get("scheduled_date", "")),
                    cons.get("status", ""),
                    cons.get("notes", ""),
                    str(cons.get("created_at", ""))
                ])

            if rows:
                ws.append_rows(rows, value_input_option="RAW")

            logger.info(f"✅ Synced {len(rows)} consultations to Sheets")
        except Exception as e:
            logger.error(f"Error syncing consultations: {e}")

    # ==================== ALERTS ====================

    def _sync_alerts(self):
        """Sync alerts to Google Sheets 'Alerts' tab."""
        try:
            alerts = self.db.query(
                "SELECT * FROM alerts ORDER BY created_at DESC LIMIT 100"
            )

            ws = self._get_or_create_worksheet("Alerts")
            ws.clear()

            headers = ["Alert ID", "Patient ID", "Severity", "Message",
                      "Created At", "Resolved At"]
            ws.append_row(headers)

            rows = []
            for alert in alerts:
                rows.append([
                    alert.get("alert_id", ""),
                    alert.get("patient_id", ""),
                    alert.get("severity", ""),
                    alert.get("message", ""),
                    str(alert.get("created_at", "")),
                    str(alert.get("resolved_at", ""))
                ])

            if rows:
                ws.append_rows(rows, value_input_option="RAW")

            logger.info(f"✅ Synced {len(rows)} alerts to Sheets")
        except Exception as e:
            logger.error(f"Error syncing alerts: {e}")

    # ==================== WORKSHEET MANAGEMENT ====================

    def _get_or_create_worksheet(self, title: str) -> Optional[Any]:
        """Get existing worksheet or create new one."""
        try:
            # Try to get existing
            try:
                return self.sheet.worksheet(title)
            except gspread.exceptions.WorksheetNotFound:
                # Create new
                ws = self.sheet.add_worksheet(title=title, rows=1000, cols=10)
                logger.info(f"Created new worksheet: {title}")
                return ws
        except Exception as e:
            logger.error(f"Error getting/creating worksheet {title}: {e}")
            return None

    def _get_worksheet(self, title: str) -> Optional[Any]:
        """Get existing worksheet without creating."""
        try:
            return self.sheet.worksheet(title)
        except gspread.exceptions.WorksheetNotFound:
            logger.warning(f"Worksheet not found: {title}")
            return None
        except Exception as e:
            logger.error(f"Error getting worksheet {title}: {e}")
            return None

    # ==================== DAILY OPERATIONS ====================

    def _sync_daily_operations(self):
        """Sync today's approved operations to 'Щоденний План' (Daily Plan) sheet."""
        try:
            from datetime import date
            today = date.today().isoformat()

            # Get approved patients scheduled for today
            approved_today = self.db.query(
                "SELECT p.*, d.name as doctor_name, s.or_room, s.time_start "
                "FROM patients p "
                "LEFT JOIN doctors d ON p.assigned_doctor_id = d.doctor_id "
                "LEFT JOIN operation_slots s ON p.id = s.patient_id "
                "WHERE p.status = 'approved' AND DATE(p.hospitalization_date) = %s "
                "ORDER BY s.time_start",
                (today,)
            )

            ws = self._get_or_create_worksheet("Щоденний План")
            if not ws:
                logger.warning("Could not access daily operations worksheet")
                return

            # Header row with Ukrainian columns
            headers = [
                "#",
                "Відділення",
                "Прізвище ім'я по батькові",
                "Кімната",
                "Вік",
                "№ історії хвороби",
                "Діагноз",
                "Операція",
                "Операційна",
                "Черга",
                "Тривалість операції",
                "Операційна бригада"
            ]

            ws.clear()
            ws.append_row(headers)

            # Add patient data rows
            for idx, patient in enumerate(approved_today, 1):
                row = [
                    str(idx),
                    patient.get("department", "N/A"),
                    patient.get("name", ""),
                    patient.get("or_room", ""),
                    str(patient.get("age", "")),
                    patient.get("patient_id", ""),
                    patient.get("diagnosis", ""),
                    patient.get("operation", ""),
                    patient.get("or_room", ""),
                    str(idx),
                    "120 min",  # Default, would come from slot duration
                    patient.get("doctor_name", "")
                ]
                ws.append_row(row)

            logger.info(f"✅ Synced {len(approved_today)} operations to daily plan")
        except Exception as e:
            logger.error(f"Error syncing daily operations: {e}")

    def _sync_weekly_operations(self):
        """Sync weekly operation schedule to 'Тижневий План' (Weekly Plan) sheet."""
        try:
            from datetime import date, timedelta
            today = date.today()
            week_end = today + timedelta(days=7)

            # Get all approved operations for the week
            week_ops = self.db.query(
                "SELECT p.*, d.name as doctor_name, s.or_room, s.date, s.time_start "
                "FROM patients p "
                "LEFT JOIN doctors d ON p.assigned_doctor_id = d.doctor_id "
                "LEFT JOIN operation_slots s ON p.id = s.patient_id "
                "WHERE p.status IN ('approved', 'hospitalized') "
                "AND DATE(p.hospitalization_date) BETWEEN %s AND %s "
                "ORDER BY DATE(p.hospitalization_date), s.time_start",
                (today, week_end)
            )

            ws = self._get_or_create_worksheet("Тижневий План")
            if not ws:
                logger.warning("Could not access weekly operations worksheet")
                return

            # Weekly summary headers
            headers = [
                "Дата",
                "День",
                "Операцій",
                "Операційна залі",
                "Лікарні",
                "Пацієнти"
            ]

            ws.clear()
            ws.append_row(headers)

            # Group by date
            ops_by_date = {}
            for op in week_ops:
                op_date = op.get("date", today).isoformat() if op.get("date") else today.isoformat()
                if op_date not in ops_by_date:
                    ops_by_date[op_date] = []
                ops_by_date[op_date].append(op)

            # Add rows
            day_names = {0: "Пн", 1: "Вт", 2: "Ср", 3: "Чт", 4: "Пт", 5: "Сб", 6: "Нд"}
            for op_date in sorted(ops_by_date.keys()):
                ops = ops_by_date[op_date]
                date_obj = date.fromisoformat(op_date)
                day_name = day_names[date_obj.weekday()]
                or_rooms = set(op.get("or_room", "") for op in ops if op.get("or_room"))
                doctors = set(op.get("doctor_name", "") for op in ops if op.get("doctor_name"))
                patients = ", ".join(op.get("name", "") for op in ops)

                row = [
                    op_date,
                    day_name,
                    str(len(ops)),
                    ", ".join(or_rooms),
                    ", ".join(doctors),
                    patients
                ]
                ws.append_row(row)

            logger.info(f"✅ Synced {len(ops_by_date)} days to weekly plan")
        except Exception as e:
            logger.error(f"Error syncing weekly operations: {e}")


# ==================== UTILITY FUNCTIONS ====================

def create_sync_schedule(sync_interval_minutes: int = 5):
    """
    Create a schedule for periodic sync.

    Usage:
        from apscheduler.schedulers.background import BackgroundScheduler
        from zav_sheets_sync import create_sync_schedule

        db = DatabaseManager(DATABASE_URL)
        sync = GoogleSheetsSync(db, sheets_url)

        scheduler = BackgroundScheduler()
        create_sync_schedule(5)  # Sync every 5 minutes
        scheduler.start()
    """
    try:
        from apscheduler.schedulers.background import BackgroundScheduler

        scheduler = BackgroundScheduler()

        def scheduled_sync():
            sync.sync_to_sheets()

        scheduler.add_job(scheduled_sync, 'interval', minutes=sync_interval_minutes)
        scheduler.start()
        logger.info(f"✅ Scheduled sync every {sync_interval_minutes} minutes")
        return scheduler
    except ImportError:
        logger.error("APScheduler not installed. Install with: pip install apscheduler")
        return None
