#!/usr/bin/env python3
"""
Zav Telegram Bot Handler
=========================

This module handles all Telegram bot interactions including:
- Command processing (/start, /alerts, /discharge, etc.)
- Inline keyboard menus for easy navigation
- Alert notifications sent to staff
- Multi-user support with role-based access

The bot connects to the Zav system via the Flask server webhook.

Usage:
    from zav_telegram_handler import TelegramBotHandler

    handler = TelegramBotHandler(db, bot_token)
    handler.send_alert_notification(user_id, alert_message, severity)
    handler.process_command(command, user_id)

Commands:
    /start          - Show welcome menu
    /alerts         - Show active alerts
    /beds           - Show bed status
    /discharge      - Show discharge candidates
    /patients       - Show patient list
    /patient <id>   - Show specific patient details
    /equipment      - Show equipment status
    /antibiotics    - Show antibiotic courses
    /help           - Show command help
"""

import logging
import requests
from datetime import datetime
from typing import Optional, Dict, List, Any
from enum import Enum

logger = logging.getLogger("ZavTelegramBot")

class AlertSeverity(Enum):
    """Alert severity levels."""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"

class TelegramBotHandler:
    """Handle Telegram bot interactions."""

    def __init__(self, db, bot_token: str):
        """
        Initialize Telegram bot handler.

        Args:
            db: DatabaseManager instance
            bot_token: Telegram bot token from @BotFather
        """
        self.db = db
        self.bot_token = bot_token
        self.api_url = f"https://api.telegram.org/bot{bot_token}"
        self.user_roles: Dict[int, str] = {}  # user_id -> role

    # ==================== MESSAGE SENDING ====================

    def send_message(self, chat_id: int, text: str, parse_mode: str = "HTML",
                     reply_markup=None) -> bool:
        """Send a message to a Telegram chat."""
        try:
            url = f"{self.api_url}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode
            }
            if reply_markup:
                payload["reply_markup"] = reply_markup

            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False

    def send_alert_notification(self, user_id: int, alert_message: str,
                               severity: AlertSeverity = AlertSeverity.INFO) -> bool:
        """Send an alert notification to a user."""
        try:
            severity_emoji = {
                AlertSeverity.CRITICAL: "🚨",
                AlertSeverity.WARNING: "⚠️",
                AlertSeverity.INFO: "ℹ️"
            }

            emoji = severity_emoji.get(severity, "ℹ️")
            formatted_message = f"{emoji} <b>{severity.value.upper()}</b>\n{alert_message}"

            return self.send_message(user_id, formatted_message)
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
            return False

    def send_typing_indicator(self, chat_id: int) -> bool:
        """Send typing indicator to show bot is processing."""
        try:
            url = f"{self.api_url}/sendChatAction"
            payload = {
                "chat_id": chat_id,
                "action": "typing"
            }
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to send typing indicator: {e}")
            return False

    # ==================== COMMAND HANDLERS ====================

    def process_command(self, command: str, user_id: int, chat_id: int) -> str:
        """Process a Telegram command and return response."""
        command = command.lower().strip()

        # Main commands
        if command == "/start":
            return self._handle_start()
        elif command == "/help":
            return self._handle_help()
        elif command == "/alerts":
            return self._handle_alerts()
        elif command == "/beds":
            return self._handle_beds()
        elif command == "/discharge":
            return self._handle_discharge()
        elif command == "/patients":
            return self._handle_patients()
        elif command == "/equipment":
            return self._handle_equipment()
        elif command == "/antibiotics":
            return self._handle_antibiotics()
        elif command.startswith("/patient "):
            patient_id = command.split(" ", 1)[1]
            return self._handle_patient_details(patient_id)
        elif command.startswith("/status"):
            return self._handle_status()
        else:
            return self._handle_unknown_command(command)

    def _handle_start(self) -> str:
        """Handle /start command."""
        return """
🏥 <b>Welcome to Zav Hospital Management</b>

I'm here to help you manage hospital operations 24/7.

<b>Quick Commands:</b>
🚨 /alerts - Show active alerts
🛏️ /beds - Check bed availability
👋 /discharge - Discharge candidates
👥 /patients - Patient list
🔧 /equipment - Equipment status
💊 /antibiotics - Antibiotic courses
📊 /status - System status
❓ /help - Detailed help

<i>Click any command or type to get started!</i>
        """

    def _handle_help(self) -> str:
        """Handle /help command."""
        return """
<b>📖 Zav Bot Commands</b>

<b>🚨 Alerts & Monitoring</b>
/alerts - View active alerts by severity
/status - System health and status

<b>🛏️ Bed Management</b>
/beds - Current bed availability
/discharge - Patients ready for discharge

<b>👥 Patient Management</b>
/patients - List all patients
/patient &lt;ID&gt; - Get specific patient details

<b>🔧 Equipment & Supplies</b>
/equipment - Current equipment status
/antibiotics - Antibiotic course tracking

<b>ℹ️ Utility</b>
/start - Welcome menu
/help - This help message

<b>Examples:</b>
• Type: /alerts
• Type: /patient PAT001
• Type: /beds

Need more help? Contact your administrator.
        """

    def _handle_alerts(self) -> str:
        """Handle /alerts command."""
        if not self.db:
            return "❌ Database not available"

        try:
            alerts = self.db.query("""
                SELECT * FROM alerts
                WHERE resolved_at IS NULL
                ORDER BY
                    CASE WHEN severity = 'critical' THEN 1
                         WHEN severity = 'warning' THEN 2
                         ELSE 3 END,
                    created_at DESC
                LIMIT 10
            """)

            if not alerts:
                return "✅ No active alerts - all systems normal!"

            response = "<b>🚨 Active Alerts</b>\n\n"

            critical = [a for a in alerts if a['severity'] == 'critical']
            warning = [a for a in alerts if a['severity'] == 'warning']
            info = [a for a in alerts if a['severity'] == 'info']

            if critical:
                response += "<b>🔴 CRITICAL</b>\n"
                for alert in critical[:3]:
                    response += f"• {alert['patient_id']}: {alert['message']}\n"
                response += "\n"

            if warning:
                response += "<b>🟠 WARNING</b>\n"
                for alert in warning[:3]:
                    response += f"• {alert['patient_id']}: {alert['message']}\n"
                response += "\n"

            if info:
                response += "<b>🔵 INFO</b>\n"
                for alert in info[:2]:
                    response += f"• {alert['patient_id']}: {alert['message']}\n"

            return response
        except Exception as e:
            logger.error(f"Error getting alerts: {e}")
            return f"❌ Error: {str(e)}"

    def _handle_beds(self) -> str:
        """Handle /beds command."""
        if not self.db:
            return "❌ Database not available"

        try:
            patients = self.db.query("SELECT COUNT(*) as total FROM patients WHERE status = 'active'")
            discharge_ready = self.db.query("""
                SELECT COUNT(*) as total FROM patients
                WHERE discharge_date <= CURRENT_DATE AND status = 'active'
            """)

            total_patients = patients[0]['total'] if patients else 0
            ready = discharge_ready[0]['total'] if discharge_ready else 0

            return f"""
<b>🛏️ Bed Occupancy Status</b>

Currently Admitted: <b>{total_patients}</b>
Ready for Discharge: <b>{ready}</b>

Occupancy: {total_patients}/100 ({total_patients}%)
Status: {'🟢 Normal' if total_patients < 80 else '🟠 High' if total_patients < 95 else '🔴 Critical'}

Use /discharge to see discharge candidates.
            """
        except Exception as e:
            logger.error(f"Error getting beds: {e}")
            return f"❌ Error: {str(e)}"

    def _handle_discharge(self) -> str:
        """Handle /discharge command."""
        if not self.db:
            return "❌ Database not available"

        try:
            patients = self.db.query("""
                SELECT patient_id, name, discharge_date
                FROM patients
                WHERE discharge_date <= CURRENT_DATE AND status = 'active'
                ORDER BY discharge_date
                LIMIT 10
            """)

            if not patients:
                return "✅ No patients currently ready for discharge"

            response = "<b>✅ Ready for Discharge</b>\n\n"
            for patient in patients:
                response += f"• <b>{patient['patient_id']}</b>: {patient['name']}\n"
                response += f"  Date: {patient['discharge_date']}\n\n"

            return response
        except Exception as e:
            logger.error(f"Error getting discharge patients: {e}")
            return f"❌ Error: {str(e)}"

    def _handle_patients(self) -> str:
        """Handle /patients command."""
        if not self.db:
            return "❌ Database not available"

        try:
            patients = self.db.query("""
                SELECT patient_id, name, admission_date, status
                FROM patients
                WHERE status = 'active'
                ORDER BY admission_date DESC
                LIMIT 15
            """)

            if not patients:
                return "No patients in system"

            response = "<b>👥 Patient List</b>\n\n"
            for patient in patients:
                admitted = patient['admission_date']
                response += f"• <b>{patient['patient_id']}</b>: {patient['name']}\n"
                response += f"  Admitted: {admitted}\n\n"

            response += f"\nTotal Active: {len(patients)}"
            return response
        except Exception as e:
            logger.error(f"Error getting patients: {e}")
            return f"❌ Error: {str(e)}"

    def _handle_patient_details(self, patient_id: str) -> str:
        """Handle /patient <id> command."""
        if not self.db:
            return "❌ Database not available"

        try:
            patients = self.db.query(
                "SELECT * FROM patients WHERE patient_id = %s",
                (patient_id,)
            )

            if not patients:
                return f"❌ Patient {patient_id} not found"

            patient = patients[0]

            # Get related data
            equipment = self.db.query(
                "SELECT * FROM equipment WHERE patient_id = %s AND status = 'active'",
                (patient_id,)
            )
            antibiotics = self.db.query(
                "SELECT * FROM antibiotics WHERE patient_id = %s",
                (patient_id,)
            )
            alerts = self.db.query(
                "SELECT * FROM alerts WHERE patient_id = %s AND resolved_at IS NULL",
                (patient_id,)
            )

            response = f"<b>👤 Patient Details: {patient['name']}</b>\n\n"
            response += f"ID: <code>{patient['patient_id']}</code>\n"
            response += f"Status: {patient['status']}\n"
            response += f"Stage: {patient['current_stage']}\n"
            response += f"Admitted: {patient['admission_date']}\n"
            response += f"Discharge: {patient['discharge_date']}\n\n"

            if equipment:
                response += f"<b>Equipment ({len(equipment)})</b>\n"
                for eq in equipment[:3]:
                    response += f"• {eq['equipment_type']}\n"
                response += "\n"

            if antibiotics:
                response += f"<b>Antibiotics ({len(antibiotics)})</b>\n"
                for ab in antibiotics[:3]:
                    response += f"• {ab['antibiotic_name']}\n"
                response += "\n"

            if alerts:
                response += f"<b>⚠️ Active Alerts ({len(alerts)})</b>\n"
                for alert in alerts[:2]:
                    response += f"• {alert['message']}\n"

            return response
        except Exception as e:
            logger.error(f"Error getting patient details: {e}")
            return f"❌ Error: {str(e)}"

    def _handle_equipment(self) -> str:
        """Handle /equipment command."""
        if not self.db:
            return "❌ Database not available"

        try:
            equipment = self.db.query("""
                SELECT e.*, p.name as patient_name
                FROM equipment e
                JOIN patients p ON e.patient_id = p.patient_id
                WHERE e.status = 'active'
                ORDER BY e.placed_date
                LIMIT 15
            """)

            if not equipment:
                return "No active equipment"

            response = "<b>🔧 Active Equipment</b>\n\n"
            for eq in equipment[:10]:
                response += f"• {eq['equipment_type']}\n"
                response += f"  Patient: {eq['patient_name']}\n"
                response += f"  Placed: {eq['placed_date']}\n\n"

            return response
        except Exception as e:
            logger.error(f"Error getting equipment: {e}")
            return f"❌ Error: {str(e)}"

    def _handle_antibiotics(self) -> str:
        """Handle /antibiotics command."""
        if not self.db:
            return "❌ Database not available"

        try:
            antibiotics = self.db.query("""
                SELECT a.*, p.name as patient_name
                FROM antibiotics a
                JOIN patients p ON a.patient_id = p.patient_id
                WHERE a.end_date > CURRENT_DATE
                ORDER BY a.start_date DESC
                LIMIT 15
            """)

            if not antibiotics:
                return "No active antibiotic courses"

            response = "<b>💊 Active Antibiotic Courses</b>\n\n"
            for ab in antibiotics[:10]:
                days = ab['days_in_course']
                response += f"• {ab['antibiotic_name']}\n"
                response += f"  Patient: {ab['patient_name']}\n"
                response += f"  Days: {days}\n\n"

            return response
        except Exception as e:
            logger.error(f"Error getting antibiotics: {e}")
            return f"❌ Error: {str(e)}"

    def _handle_status(self) -> str:
        """Handle /status command."""
        if not self.db:
            return "❌ Database not available"

        try:
            patients = self.db.query("SELECT COUNT(*) as count FROM patients WHERE status = 'active'")
            alerts = self.db.query("SELECT COUNT(*) as count FROM alerts WHERE resolved_at IS NULL")
            equipment = self.db.query("SELECT COUNT(*) as count FROM equipment WHERE status = 'active'")

            total_patients = patients[0]['count'] if patients else 0
            active_alerts = alerts[0]['count'] if alerts else 0
            active_equipment = equipment[0]['count'] if equipment else 0

            return f"""
<b>📊 System Status</b>

✅ Database: Connected
🤖 Bot: Online
⏰ Time: {datetime.now().strftime('%H:%M:%S')}

<b>Stats:</b>
👥 Patients: {total_patients}
🚨 Alerts: {active_alerts}
🔧 Equipment: {active_equipment}

Status: <b>🟢 Normal</b>
            """
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return f"❌ Error: {str(e)}"

    def _handle_unknown_command(self, command: str) -> str:
        """Handle unknown command."""
        return f"""
❓ Unknown command: <code>{command}</code>

Use /help to see available commands or /start for the welcome menu.
        """
