#!/usr/bin/env python3
"""
Zav Daily Patient Sync Job
Syncs active patients from Cyberintern + planned patients from Google Sheets
Runs at 5 AM daily on Railway
"""

import os
import sys
import logging
from datetime import datetime
import requests
import json
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ZavSyncJob")

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "")
CYBERINTERN_API = os.getenv("CYBERINTERN_API", "http://localhost:8082")
GOOGLE_SHEETS_ID = os.getenv("GOOGLE_SHEETS_ID", "1uMRrf8INgFp8WMOSWgobWOQ9W4KrlLw_NR3BtnlLUqA")
GOOGLE_SHEETS_KEY = os.getenv("GOOGLE_SHEETS_KEY", "")

# Import psycopg for database
try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:
    logger.error("psycopg not installed")
    sys.exit(1)


class PatientSync:
    """Sync patients from multiple sources to Zav database"""

    def __init__(self):
        """Initialize sync job"""
        self.conn = None
        self._init_db_connection()
        self.sync_stats = {
            "cyberintern_synced": 0,
            "cyberintern_errors": 0,
            "sheets_synced": 0,
            "sheets_errors": 0,
            "total_patients": 0,
        }

    def _init_db_connection(self):
        """Initialize database connection"""
        try:
            self.conn = psycopg.connect(DATABASE_URL, autocommit=True)
            logger.info("✅ Database connection established")
        except Exception as e:
            logger.error(f"❌ Failed to connect to database: {e}")
            raise

    def sync_cyberintern_patients(self) -> int:
        """
        Sync active patients from Cyberintern EMR system

        Returns: Number of patients synced
        """
        logger.info("🔄 Starting Cyberintern patient sync...")
        synced_count = 0

        try:
            # Try multiple ways to get active patients from Cyberintern

            # Method 1: Direct API call (if available)
            try:
                response = requests.get(
                    f"{CYBERINTERN_API}/api/patients/active",
                    timeout=10
                )
                if response.status_code == 200:
                    patients = response.json()
                    logger.info(f"📥 Retrieved {len(patients)} active patients from Cyberintern API")
                    synced_count = self._process_cyberintern_patients(patients)
                    self.sync_stats["cyberintern_synced"] = synced_count
                    return synced_count
            except Exception as e:
                logger.warning(f"⚠️ Cyberintern API not available: {e}")

            # Method 2: MCP-based access (when MCP is configured)
            logger.info("💡 Cyberintern MCP method: Coming in next deployment")
            logger.info("   MCP endpoint: cyberintern.get_active_patients()")

            return synced_count

        except Exception as e:
            logger.error(f"❌ Error syncing Cyberintern patients: {e}")
            self.sync_stats["cyberintern_errors"] += 1
            return synced_count

    def _process_cyberintern_patients(self, patients: List[Dict]) -> int:
        """Process and store Cyberintern patients"""
        synced = 0
        cursor = self.conn.cursor()

        for patient in patients:
            try:
                # Extract key fields (adjust based on actual Cyberintern schema)
                patient_id = patient.get("id") or patient.get("patient_id")
                name = patient.get("name") or patient.get("full_name")
                admission_date = patient.get("admission_date") or patient.get("admitted_at")
                status = patient.get("status") or "active"

                if not patient_id or not name:
                    logger.warning(f"⚠️ Skipping patient with missing ID or name: {patient}")
                    continue

                # Check if patient already exists
                cursor.execute(
                    "SELECT id FROM patients WHERE patient_id = %s",
                    (str(patient_id),)
                )
                existing = cursor.fetchone()

                if existing:
                    # Update existing patient
                    cursor.execute(
                        """UPDATE patients SET
                           name = %s,
                           status = %s,
                           source = %s,
                           external_id = %s,
                           last_synced_at = NOW()
                        WHERE patient_id = %s""",
                        (name, status, "cyberintern", str(patient_id), str(patient_id))
                    )
                    logger.debug(f"♻️  Updated patient: {name} ({patient_id})")
                else:
                    # Create new patient
                    cursor.execute(
                        """INSERT INTO patients
                           (patient_id, name, admission_date, status, source, external_id, last_synced_at)
                        VALUES (%s, %s, %s, %s, %s, %s, NOW())""",
                        (str(patient_id), name, admission_date, status, "cyberintern", str(patient_id))
                    )
                    logger.debug(f"✨ Created new patient: {name} ({patient_id})")

                synced += 1

            except Exception as e:
                logger.error(f"❌ Error processing patient {patient.get('id')}: {e}")
                self.sync_stats["cyberintern_errors"] += 1

        cursor.close()
        return synced

    def sync_planned_patients_from_sheets(self) -> int:
        """
        Sync planned patients from Google Sheets

        Returns: Number of patients synced
        """
        logger.info("🔄 Starting Google Sheets planned patients sync...")
        synced_count = 0

        try:
            # Method 1: Using gspread library (requires credentials)
            try:
                import gspread
                from google.oauth2.service_account import Credentials

                if not GOOGLE_SHEETS_KEY:
                    logger.warning("⚠️ GOOGLE_SHEETS_KEY not set, skipping sheets sync")
                    return 0

                # Parse credentials from environment variable
                creds_dict = json.loads(GOOGLE_SHEETS_KEY)
                creds = Credentials.from_service_account_info(creds_dict)
                gc = gspread.authorize(creds)

                # Open spreadsheet
                sheet = gc.open_by_key(GOOGLE_SHEETS_ID)

                # Get "Planned Patients" sheet
                planned_sheet = sheet.worksheet("Planned Patients")
                planned_records = planned_sheet.get_all_records()

                logger.info(f"📥 Retrieved {len(planned_records)} planned patients from Google Sheets")
                synced_count = self._process_planned_patients(planned_records)
                self.sync_stats["sheets_synced"] = synced_count

            except ImportError:
                logger.warning("⚠️ gspread library not installed")
                logger.info("   Install with: pip install gspread google-auth-oauthlib")
            except Exception as e:
                logger.warning(f"⚠️ Error with gspread method: {e}")

            # Method 2: MCP-based access (when sheets MCP is configured)
            logger.info("💡 Google Sheets MCP method: Configure authentication")
            logger.info("   MCP endpoint: google_sheets.read_sheet('Planned Patients')")

            return synced_count

        except Exception as e:
            logger.error(f"❌ Error syncing planned patients from sheets: {e}")
            self.sync_stats["sheets_errors"] += 1
            return synced_count

    def _process_planned_patients(self, patients: List[Dict]) -> int:
        """Process and store planned patients from sheets"""
        synced = 0
        cursor = self.conn.cursor()

        for patient in patients:
            try:
                # Extract fields from Google Sheets
                patient_id = patient.get("Patient ID") or f"PL{datetime.now().timestamp()}"
                name = patient.get("Name")
                operation_type = patient.get("Operation")
                planned_date = patient.get("Planned Date")
                priority = patient.get("Priority") or "routine"
                status = patient.get("Status") or "planned"

                if not name:
                    logger.warning(f"⚠️ Skipping sheet row with missing name: {patient}")
                    continue

                # Check if patient already exists
                cursor.execute(
                    "SELECT id FROM patients WHERE patient_id = %s OR (name = %s AND source = %s)",
                    (str(patient_id), name, "external")
                )
                existing = cursor.fetchone()

                if existing:
                    # Update existing planned patient
                    cursor.execute(
                        """UPDATE patients SET
                           operation_type = %s,
                           planned_admission_date = %s,
                           priority = %s,
                           status = %s,
                           source = %s,
                           last_synced_at = NOW()
                        WHERE id = %s""",
                        (operation_type, planned_date, priority, status, "external", existing[0])
                    )
                    logger.debug(f"♻️  Updated planned patient: {name}")
                else:
                    # Create new planned patient
                    cursor.execute(
                        """INSERT INTO patients
                           (patient_id, name, operation_type, planned_admission_date, priority, status, source, last_synced_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())""",
                        (str(patient_id), name, operation_type, planned_date, priority, status, "external")
                    )
                    logger.debug(f"✨ Created planned patient: {name}")

                synced += 1

            except Exception as e:
                logger.error(f"❌ Error processing planned patient {patient.get('Name')}: {e}")
                self.sync_stats["sheets_errors"] += 1

        cursor.close()
        return synced

    def get_summary(self) -> Dict:
        """Get sync job summary statistics"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM patients WHERE source = 'cyberintern' AND status = 'active'")
            active_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM patients WHERE source = 'external' AND status = 'planned'")
            planned_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM patients")
            total_count = cursor.fetchone()[0]

            cursor.close()

            return {
                "timestamp": datetime.now().isoformat(),
                "active_patients": active_count,
                "planned_patients": planned_count,
                "total_patients": total_count,
                "sync_stats": self.sync_stats,
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Error getting summary: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "status": "error",
                "error": str(e),
                "sync_stats": self.sync_stats
            }

    def run(self):
        """Execute full sync job"""
        logger.info("=" * 60)
        logger.info("🏥 ZAV DAILY PATIENT SYNC JOB STARTED")
        logger.info(f"⏰ Time: {datetime.now().isoformat()}")
        logger.info("=" * 60)

        try:
            # Sync from both sources
            cyberintern_count = self.sync_cyberintern_patients()
            sheets_count = self.sync_planned_patients_from_sheets()

            # Get summary
            summary = self.get_summary()

            logger.info("=" * 60)
            logger.info("✅ SYNC JOB COMPLETED")
            logger.info(f"   Cyberintern synced: {cyberintern_count}")
            logger.info(f"   Sheets synced: {sheets_count}")
            logger.info(f"   Total patients in system: {summary['total_patients']}")
            logger.info(f"   Active (from EMR): {summary['active_patients']}")
            logger.info(f"   Planned (external): {summary['planned_patients']}")
            logger.info("=" * 60)

            return summary

        except Exception as e:
            logger.error(f"❌ SYNC JOB FAILED: {e}")
            raise
        finally:
            if self.conn:
                self.conn.close()


if __name__ == "__main__":
    sync = PatientSync()
    result = sync.run()
    print(json.dumps(result, indent=2))
