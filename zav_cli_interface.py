#!/usr/bin/env python3
"""
Zav Hospital Management System - Claude CLI Interface
======================================================

This module provides a unified CLI interface for Claude to manage hospital workflows.
It acts as the main entry point that transforms Claude into a Zav system with:
- Consistent output formatting (tables, alerts, summaries)
- State management (current patient, filters, view mode)
- Command parsing (natural language → tool calls)
- Formatted results (hospital-optimized presentation)

Usage:
    User: "Show me patients at risk of overstay"
    Claude: [Calls overstay detection tool, formats results as table, provides recommendations]

    User: "What's the bed occupancy today?"
    Claude: [Calls throughput report, shows bed metrics]

    User: "List equipment ready for removal"
    Claude: [Calls equipment tracking, filters by status, shows formatted list]
"""

import sys
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from textwrap import wrap

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

# Import all Zav engines
from zav_phase_1_dashboard import Phase1Dashboard
from zav_phase_2_core import Phase2Engine
from zav_phase_3_advanced_workflows import Phase3Engine
from zav_phase_3b_complete_workflows import Phase3BEngine

# Import security modules
from zav_authorization import User, UserRole, create_test_doctor, create_system_user
from zav_persistence import initialize_persistence, get_global_data_store, SQLiteDataStore

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ZavCLI")


class ViewMode(Enum):
    """Output display mode for Zav CLI."""
    TABLE = "table"        # Formatted table output
    SUMMARY = "summary"    # Executive summary
    DETAILED = "detailed"  # Full details with all fields
    JSON = "json"          # JSON output for machine reading
    ALERT = "alert"        # Alert-style output with urgency colors
    CHART = "chart"        # ASCII chart representation


@dataclass
class ZavCLIState:
    """Manages state across CLI sessions."""
    current_patient_id: Optional[str] = None
    current_user: Optional[User] = None
    view_mode: ViewMode = ViewMode.TABLE
    filters: Dict[str, Any] = field(default_factory=dict)
    alert_filter: Optional[str] = None  # "critical", "warning", "all"
    timestamp: datetime = field(default_factory=datetime.now)

    def update_timestamp(self):
        """Update to current time."""
        self.timestamp = datetime.now()


class ZavOutputFormatter:
    """Formats output consistently for CLI display."""

    # ANSI color codes
    COLORS = {
        "RED": "\033[91m",
        "GREEN": "\033[92m",
        "YELLOW": "\033[93m",
        "BLUE": "\033[94m",
        "MAGENTA": "\033[95m",
        "CYAN": "\033[96m",
        "WHITE": "\033[97m",
        "RESET": "\033[0m",
        "BOLD": "\033[1m",
        "DIM": "\033[2m",
    }

    @staticmethod
    def header(text: str, level: int = 1) -> str:
        """Format header with underline."""
        colors = {
            1: ZavOutputFormatter.COLORS["BOLD"] + ZavOutputFormatter.COLORS["CYAN"],
            2: ZavOutputFormatter.COLORS["BOLD"] + ZavOutputFormatter.COLORS["BLUE"],
            3: ZavOutputFormatter.COLORS["CYAN"],
        }
        color = colors.get(level, "")
        reset = ZavOutputFormatter.COLORS["RESET"]

        if level == 1:
            underline = "=" * len(text)
        elif level == 2:
            underline = "-" * len(text)
        else:
            underline = "• " * (len(text) // 2)

        return f"{color}{text}\n{underline}{reset}"

    @staticmethod
    def alert(message: str, urgency: str = "info") -> str:
        """Format alert message with urgency indicator."""
        urgency_indicators = {
            "critical": f"{ZavOutputFormatter.COLORS['RED']}🔴 CRITICAL{ZavOutputFormatter.COLORS['RESET']}",
            "warning": f"{ZavOutputFormatter.COLORS['YELLOW']}🟠 WARNING{ZavOutputFormatter.COLORS['RESET']}",
            "info": f"{ZavOutputFormatter.COLORS['BLUE']}ℹ️  INFO{ZavOutputFormatter.COLORS['RESET']}",
            "success": f"{ZavOutputFormatter.COLORS['GREEN']}✅ SUCCESS{ZavOutputFormatter.COLORS['RESET']}",
        }

        indicator = urgency_indicators.get(urgency, urgency_indicators["info"])
        return f"{indicator} {message}"

    @staticmethod
    def table(headers: List[str], rows: List[List[str]], max_width: int = 100) -> str:
        """Format data as ASCII table."""
        # Calculate column widths
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(cell)))

        # Build table
        lines = []

        # Header
        header_line = " | ".join(f"{h:<{w}}" for h, w in zip(headers, col_widths))
        lines.append(header_line)
        lines.append("-" * len(header_line))

        # Rows
        for row in rows:
            row_line = " | ".join(f"{str(cell):<{w}}" for cell, w in zip(row, col_widths))
            lines.append(row_line)

        return "\n".join(lines)

    @staticmethod
    def key_value_pair(key: str, value: Any, indent: int = 0) -> str:
        """Format key-value pair."""
        prefix = " " * indent
        return f"{prefix}{ZavOutputFormatter.COLORS['BOLD']}{key}:{ZavOutputFormatter.COLORS['RESET']} {value}"

    @staticmethod
    def section(title: str, content: str, indent: int = 0) -> str:
        """Format section with title and content."""
        prefix = " " * indent
        title_formatted = f"{prefix}{ZavOutputFormatter.COLORS['BOLD']}• {title}{ZavOutputFormatter.COLORS['RESET']}"
        content_lines = [f"{prefix}  {line}" for line in content.split("\n")]
        return f"{title_formatted}\n" + "\n".join(content_lines)

    @staticmethod
    def metric(label: str, value: Any, unit: str = "", threshold: Optional[float] = None) -> str:
        """Format metric with optional threshold coloring."""
        if threshold is not None and isinstance(value, (int, float)):
            if value >= threshold:
                color = ZavOutputFormatter.COLORS["RED"]
            else:
                color = ZavOutputFormatter.COLORS["GREEN"]
        else:
            color = ""

        reset = ZavOutputFormatter.COLORS["RESET"] if color else ""
        return f"{label}: {color}{value}{reset} {unit}".strip()

    @staticmethod
    def list_items(items: List[str], bullet: str = "•", indent: int = 0) -> str:
        """Format list of items."""
        prefix = " " * indent
        return "\n".join(f"{prefix}{bullet} {item}" for item in items)


class ZavCLI:
    """Main Zav CLI interface for Claude."""

    def __init__(self, user: Optional[User] = None, db_path: Optional[str] = None):
        """Initialize Zav CLI."""
        logger.info("🏥 Initializing Zav Hospital Management System CLI...")

        # User and persistence
        self.user = user or create_test_doctor()
        self.db_path = db_path

        # Initialize all engines
        self.phase1 = Phase1Dashboard(user=self.user, db_path=db_path)
        self.phase2 = Phase2Engine(user=self.user, db_path=db_path)
        self.phase3 = Phase3Engine(user=self.user, db_path=db_path)
        self.phase3b = Phase3BEngine(user=self.user, db_path=db_path)

        # CLI state
        self.state = ZavCLIState(current_user=self.user)

        # Command history
        self.history: List[Dict[str, Any]] = []

        logger.info("✅ Zav CLI Ready")

    # ==================== PHASE 1: VISIBILITY ====================

    def show_alerts(self, severity: str = "all", limit: int = 10) -> str:
        """Show current alerts with formatting."""
        logger.info(f"📋 Fetching alerts (severity={severity}, limit={limit})...")

        # Get alerts (simulated for demo)
        alerts = self._simulate_alerts(limit)

        output_lines = [ZavOutputFormatter.header("🚨 CURRENT ALERTS", level=1)]
        output_lines.append(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        if not alerts:
            output_lines.append(ZavOutputFormatter.alert("No alerts", "success"))
            return "\n".join(output_lines)

        # Format alerts by severity
        critical = [a for a in alerts if a["severity"] == "critical"]
        warning = [a for a in alerts if a["severity"] == "warning"]
        info = [a for a in alerts if a["severity"] == "info"]

        if critical:
            output_lines.append(ZavOutputFormatter.header("Critical Alerts", level=2))
            for alert in critical:
                output_lines.append(ZavOutputFormatter.alert(
                    f"{alert['patient_id']}: {alert['message']}",
                    "critical"
                ))
            output_lines.append("")

        if warning:
            output_lines.append(ZavOutputFormatter.header("Warnings", level=2))
            for alert in warning:
                output_lines.append(ZavOutputFormatter.alert(
                    f"{alert['patient_id']}: {alert['message']}",
                    "warning"
                ))
            output_lines.append("")

        if info:
            output_lines.append(ZavOutputFormatter.header("Information", level=2))
            for alert in info[:5]:  # Limit info alerts
                output_lines.append(ZavOutputFormatter.alert(
                    f"{alert['patient_id']}: {alert['message']}",
                    "info"
                ))

        return "\n".join(output_lines)

    # ==================== PHASE 2: PREVENTION ====================

    def show_bed_forecast(self, days_ahead: int = 7) -> str:
        """Show bed availability forecast."""
        logger.info(f"🛏️  Forecasting bed availability for {days_ahead} days...")

        output_lines = [ZavOutputFormatter.header("📊 BED AVAILABILITY FORECAST", level=1)]

        try:
            forecast = self.phase2.forecast_bed_availability(days_ahead)

            # Format as table
            headers = ["Date", "Total Beds", "Available", "Occupancy %", "Status"]
            rows = []

            for f in forecast[:days_ahead]:
                occupancy_pct = (f.occupied / f.total_beds * 100) if f.total_beds > 0 else 0
                status = "🟢 Low" if occupancy_pct < 70 else "🟠 Medium" if occupancy_pct < 85 else "🔴 High"
                rows.append([
                    f.date.strftime("%a %m/%d"),
                    str(f.total_beds),
                    str(f.available),
                    f"{occupancy_pct:.0f}%",
                    status
                ])

            output_lines.append("")
            output_lines.append(ZavOutputFormatter.table(headers, rows))

        except Exception as e:
            output_lines.append(ZavOutputFormatter.alert(f"Error: {e}", "warning"))

        return "\n".join(output_lines)

    def show_discharge_ready(self) -> str:
        """Show patients ready for discharge."""
        logger.info("👋 Finding discharge-ready patients...")

        output_lines = [ZavOutputFormatter.header("✅ DISCHARGE READY PATIENTS", level=1)]

        try:
            patients = self.phase2.assess_discharge_readiness()

            if not patients:
                output_lines.append(ZavOutputFormatter.alert("No discharge-ready patients", "success"))
                return "\n".join(output_lines)

            # Format as table
            headers = ["Patient ID", "Name", "Days Admitted", "Readiness Score", "Recommendation"]
            rows = []

            for patient, score in patients[:10]:
                recommendation = "DISCHARGE NOW" if score > 0.8 else "REVIEW SOON" if score > 0.5 else "NOT READY"
                rows.append([
                    patient.patient_id,
                    patient.name,
                    str(patient.days_admitted),
                    f"{score:.0%}",
                    recommendation
                ])

            output_lines.append("")
            output_lines.append(ZavOutputFormatter.table(headers, rows))
            output_lines.append(f"\nTotal: {len(patients)} patients assessed")

        except Exception as e:
            output_lines.append(ZavOutputFormatter.alert(f"Error: {e}", "warning"))

        return "\n".join(output_lines)

    def show_operation_schedule(self) -> str:
        """Show weekly operation schedule."""
        logger.info("🏥 Fetching operation schedule...")

        output_lines = [ZavOutputFormatter.header("📅 WEEKLY OPERATION SCHEDULE", level=1)]

        try:
            ops, metrics = self.phase2.plan_weekly_operations()

            if not ops:
                output_lines.append(ZavOutputFormatter.alert("No operations scheduled", "info"))
                return "\n".join(output_lines)

            # Format as table
            headers = ["Time", "Patient ID", "Operation", "Duration", "OR", "Priority"]
            rows = []

            for op in ops[:15]:
                rows.append([
                    op.scheduled_time.strftime("%a %H:%M"),
                    op.patient_id,
                    op.operation_type[:20],
                    f"{op.duration_minutes} min",
                    f"OR-{op.operating_room_id}",
                    op.priority
                ])

            output_lines.append("")
            output_lines.append(ZavOutputFormatter.table(headers, rows))

            # Add metrics
            output_lines.append("\n" + ZavOutputFormatter.header("Metrics", level=2))
            output_lines.append(ZavOutputFormatter.metric("Total Operations", len(ops)))
            output_lines.append(ZavOutputFormatter.metric("OR Utilization", f"{metrics.get('or_utilization', 0):.0%}"))
            output_lines.append(ZavOutputFormatter.metric("Average Duration", f"{metrics.get('avg_duration', 0):.0f} min"))

        except Exception as e:
            output_lines.append(ZavOutputFormatter.alert(f"Error: {e}", "warning"))

        return "\n".join(output_lines)

    # ==================== PHASE 3: CONTROL ====================

    def show_overstay_patients(self, threshold: int = 60) -> str:
        """Show patients at risk of overstay."""
        logger.info(f"⏰ Detecting patients with stays > {threshold} days...")

        output_lines = [ZavOutputFormatter.header("⚠️  OVERSTAY DETECTION", level=1)]
        output_lines.append(f"Alert Threshold: {threshold} days\n")

        try:
            overstays = self.phase3.detect_patient_overstays(alert_threshold_days=threshold)

            if not overstays:
                output_lines.append(ZavOutputFormatter.alert("No overstay patients detected", "success"))
                return "\n".join(output_lines)

            # Group by urgency
            by_urgency = {}
            for overstay in overstays:
                urgency = overstay.urgency_level
                if urgency not in by_urgency:
                    by_urgency[urgency] = []
                by_urgency[urgency].append(overstay)

            # Format each urgency level
            urgency_order = ["red", "orange", "yellow", "green"]
            for urgency in urgency_order:
                if urgency in by_urgency:
                    overstays_list = by_urgency[urgency]

                    urgency_label = {
                        "red": "🔴 CRITICAL",
                        "orange": "🟠 WARNING",
                        "yellow": "🟡 CAUTION",
                        "green": "🟢 NORMAL"
                    }.get(urgency, urgency)

                    output_lines.append(ZavOutputFormatter.header(urgency_label, level=2))

                    headers = ["Patient ID", "Days In", "Stage", "Likely Reason", "Action"]
                    rows = []

                    for os in overstays_list[:10]:
                        rows.append([
                            os.patient_id,
                            str(os.days_in_hospital),
                            f"Stage {os.current_stage}",
                            os.likely_reason.value[:20],
                            os.recommended_action[:30]
                        ])

                    output_lines.append("")
                    output_lines.append(ZavOutputFormatter.table(headers, rows))
                    output_lines.append("")

            output_lines.append(f"Total At-Risk: {len(overstays)} patients")

        except Exception as e:
            output_lines.append(ZavOutputFormatter.alert(f"Error: {e}", "warning"))

        return "\n".join(output_lines)

    def show_consultation_queue(self) -> str:
        """Show consultation queue and doctor availability."""
        logger.info("📞 Checking consultation queue...")

        output_lines = [ZavOutputFormatter.header("📞 CONSULTATION QUEUE", level=1)]

        try:
            queue_status = self.phase3.manage_consultation_queue()

            output_lines.append(ZavOutputFormatter.metric("Total in Queue", queue_status.get("total_in_queue", 0)))
            output_lines.append(ZavOutputFormatter.metric("Assigned", queue_status.get("assigned", 0)))
            output_lines.append(ZavOutputFormatter.metric("Pending", queue_status.get("pending", 0)))

        except Exception as e:
            output_lines.append(ZavOutputFormatter.alert(f"Error: {e}", "warning"))

        return "\n".join(output_lines)

    # ==================== PHASE 3B: OPTIMIZATION ====================

    def show_milestones(self) -> str:
        """Show 120-day milestone tracking."""
        logger.info("⏰ Tracking 120-day milestones...")

        output_lines = [ZavOutputFormatter.header("📍 120-DAY MILESTONES", level=1)]

        try:
            milestones = self.phase3b.track_120_day_milestones()

            status_colors = {
                "normal": "🟢 Normal",
                "approaching": "🟡 Approaching",
                "warning": "🟠 Warning",
                "critical": "🔴 Critical"
            }

            for status, color in status_colors.items():
                count = len(milestones.get(status, []))
                if count > 0:
                    output_lines.append(ZavOutputFormatter.header(f"{color} ({count})", level=2))

                    for patient in milestones[status][:5]:
                        output_lines.append(ZavOutputFormatter.section(
                            f"Patient {patient['patient_id']}",
                            f"Days in Hospital: {patient['days_in_hospital']}\n"
                            f"Action: {patient['action']}"
                        ))
                    output_lines.append("")

        except Exception as e:
            output_lines.append(ZavOutputFormatter.alert(f"Error: {e}", "warning"))

        return "\n".join(output_lines)

    def show_equipment_status(self) -> str:
        """Show medical equipment tracking."""
        logger.info("🔧 Checking equipment status...")

        output_lines = [ZavOutputFormatter.header("🔧 EQUIPMENT TRACKING", level=1)]

        try:
            equipment = self.phase3b.track_medical_equipment()

            output_lines.append(ZavOutputFormatter.metric("Total In Use", equipment.get("total_in_use", 0)))

            if equipment.get("by_type"):
                output_lines.append("\n" + ZavOutputFormatter.header("By Type", level=2))
                for eq_type, details in equipment["by_type"].items():
                    output_lines.append(f"  • {eq_type}: {details['count']} items")

            if equipment.get("ready_for_removal"):
                output_lines.append("\n" + ZavOutputFormatter.alert(
                    f"Equipment Ready for Removal: {len(equipment['ready_for_removal'])} items",
                    "warning"
                ))

            if equipment.get("maintenance_needed"):
                output_lines.append("\n" + ZavOutputFormatter.alert(
                    f"Maintenance Needed: {len(equipment['maintenance_needed'])} items",
                    "warning"
                ))

        except Exception as e:
            output_lines.append(ZavOutputFormatter.alert(f"Error: {e}", "warning"))

        return "\n".join(output_lines)

    def show_throughput_report(self, period: str = "daily") -> str:
        """Show throughput and bottleneck analysis."""
        logger.info(f"📊 Generating {period} throughput report...")

        output_lines = [ZavOutputFormatter.header(f"📊 {period.upper()} THROUGHPUT REPORT", level=1)]
        output_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        try:
            report = self.phase3b.generate_throughput_report(period)

            # Key metrics
            output_lines.append(ZavOutputFormatter.header("Key Metrics", level=2))
            output_lines.append(ZavOutputFormatter.metric("Admissions", report.total_admissions))
            output_lines.append(ZavOutputFormatter.metric("Discharges", report.total_discharges))
            output_lines.append(ZavOutputFormatter.metric("Avg Length of Stay", f"{report.average_length_of_stay:.1f} days"))
            output_lines.append(ZavOutputFormatter.metric("Patients In Hospital", report.patients_in_hospital))

            # Utilization
            output_lines.append("\n" + ZavOutputFormatter.header("Utilization", level=2))
            output_lines.append(ZavOutputFormatter.metric(
                "Bed Occupancy",
                f"{report.bed_occupancy_percent:.0f}%",
                threshold=85
            ))
            output_lines.append(ZavOutputFormatter.metric(
                "OR Utilization",
                f"{report.or_utilization_percent:.0f}%"
            ))

            # Findings and recommendations
            if report.key_findings:
                output_lines.append("\n" + ZavOutputFormatter.header("Key Findings", level=2))
                output_lines.append(ZavOutputFormatter.list_items(report.key_findings, bullet="→"))

            if report.recommendations:
                output_lines.append("\n" + ZavOutputFormatter.header("Recommendations", level=2))
                output_lines.append(ZavOutputFormatter.list_items(report.recommendations, bullet="→"))

        except Exception as e:
            output_lines.append(ZavOutputFormatter.alert(f"Error: {e}", "warning"))

        return "\n".join(output_lines)

    # ==================== HELPER METHODS ====================

    def _simulate_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Simulate alert data for demo."""
        alerts = [
            {
                "patient_id": "patient-001",
                "severity": "critical",
                "message": "Patient at risk of overstay - 75 days hospitalized"
            },
            {
                "patient_id": "patient-002",
                "severity": "warning",
                "message": "Antibiotic course exceeded 30 days - review needed"
            },
            {
                "patient_id": "patient-003",
                "severity": "warning",
                "message": "Equipment ready for removal - VAC drain"
            },
            {
                "patient_id": "patient-004",
                "severity": "info",
                "message": "Patient consultation queued"
            },
        ]
        return alerts[:limit]

    def set_view_mode(self, mode: str):
        """Change output view mode."""
        try:
            self.state.view_mode = ViewMode[mode.upper()]
            return f"View mode changed to: {mode}"
        except KeyError:
            return f"Invalid view mode. Options: {', '.join([m.value for m in ViewMode])}"

    def set_current_patient(self, patient_id: str):
        """Set the current patient context."""
        self.state.current_patient_id = patient_id
        return f"Current patient set to: {patient_id}"

    # ==================== EXTERNAL PATIENT APPROVAL (Cloud Server) ====================

    def show_pending_patients(self) -> str:
        """Show pending external patient requests from Telegram."""
        logger.info("📋 Fetching pending external patients...")

        import requests

        try:
            resp = requests.get("http://127.0.0.1:8080/api/patients/pending", timeout=5)

            if resp.status_code != 200:
                return f"❌ Error fetching pending patients: {resp.status_code}"

            patients = resp.json()

            if not patients:
                return "✅ No pending external patient requests"

            output_lines = [ZavOutputFormatter.header("📋 PENDING EXTERNAL PATIENTS", level=1)]
            output_lines.append("")

            for p in patients:
                output_lines.append(f"ID: {ZavOutputFormatter.COLORS['BOLD']}{p['patient_id']}{ZavOutputFormatter.COLORS['RESET']}")
                output_lines.append(f"  👤 Name: {p['name']}, Age: {p['age']}")
                output_lines.append(f"  🏥 Operation: {p['operation']}")
                output_lines.append(f"  📝 Notes: {p['notes']}")
                output_lines.append(f"  📅 Submitted: {p['created_at']}")
                output_lines.append("")

            return "\n".join(output_lines)

        except Exception as e:
            logger.error(f"Error fetching pending patients: {e}")
            return f"❌ Error: {str(e)}"

    def approve_patient(self, patient_id: str, hospitalization_date: str, doctor_id: str, slot_id: str) -> str:
        """Approve external patient with scheduling info."""
        logger.info(f"✅ Approving patient {patient_id} for {hospitalization_date}")

        import requests

        try:
            resp = requests.put(
                f"http://127.0.0.1:8080/api/patients/{patient_id}/approve",
                json={
                    "hospitalization_date": hospitalization_date,
                    "assigned_doctor_id": doctor_id,
                    "operation_slot_id": slot_id,
                    "approved_by": self.user.name if self.user else "admin"
                },
                timeout=5
            )

            if resp.status_code != 200:
                return f"❌ Error approving patient: {resp.text}"

            return f"✅ Patient {patient_id} approved!\n📅 Date: {hospitalization_date}\n🏥 Doctor: {doctor_id}\n⏰ Slot: {slot_id}"

        except Exception as e:
            logger.error(f"Error approving patient: {e}")
            return f"❌ Error: {str(e)}"

    def reject_patient(self, patient_id: str, reason: str) -> str:
        """Reject external patient request."""
        logger.info(f"❌ Rejecting patient {patient_id}: {reason}")

        import requests

        try:
            resp = requests.put(
                f"http://127.0.0.1:8080/api/patients/{patient_id}/reject",
                json={"rejection_reason": reason},
                timeout=5
            )

            if resp.status_code != 200:
                return f"❌ Error rejecting patient: {resp.text}"

            return f"✅ Patient {patient_id} rejected\n❌ Reason: {reason}"

        except Exception as e:
            logger.error(f"Error rejecting patient: {e}")
            return f"❌ Error: {str(e)}"

    def show_operation_slots(self, date: Optional[str] = None) -> str:
        """Show available operation slots."""
        logger.info(f"🏥 Fetching operation slots for {date or 'all dates'}...")

        import requests

        try:
            url = "http://127.0.0.1:8080/api/operation-slots"
            if date:
                url += f"?date={date}"

            resp = requests.get(url, timeout=5)

            if resp.status_code != 200:
                return f"❌ Error fetching slots: {resp.status_code}"

            slots = resp.json()

            if not slots:
                return "✅ No operation slots available"

            output_lines = [ZavOutputFormatter.header("🏥 OPERATION SLOTS", level=1)]

            # Group by date and OR room
            by_date = {}
            for slot in slots:
                slot_date = slot['date']
                if slot_date not in by_date:
                    by_date[slot_date] = {}

                or_room = slot['or_room']
                if or_room not in by_date[slot_date]:
                    by_date[slot_date][or_room] = []

                by_date[slot_date][or_room].append(slot)

            for slot_date in sorted(by_date.keys()):
                output_lines.append(f"\n📅 {slot_date}")

                for or_room in sorted(by_date[slot_date].keys()):
                    output_lines.append(f"  {or_room}:")
                    for slot in by_date[slot_date][or_room]:
                        status = "✅" if slot['status'] == "available" else "🔴"
                        output_lines.append(f"    {status} {slot['time_start']}-{slot['time_end']} (ID: {slot['slot_id']})")

            return "\n".join(output_lines)

        except Exception as e:
            logger.error(f"Error fetching slots: {e}")
            return f"❌ Error: {str(e)}"

    def show_help(self) -> str:
        """Show help menu."""
        help_text = """
ZAV HOSPITAL MANAGEMENT SYSTEM - COMMANDS
===========================================

VISIBILITY (Phase 1):
  • alerts          - Show current alerts and warnings
  • patient <id>    - Show patient details

PREVENTION (Phase 2):
  • beds            - Show bed availability forecast
  • discharge       - Show discharge-ready patients
  • schedule        - Show weekly operation schedule
  • workload        - Show doctor workload analysis

CONTROL (Phase 3):
  • overstay        - Find patients stuck in system
  • consultations   - Show consultation queue status
  • treatments      - Show staged treatment tracking

OPTIMIZATION (Phase 3B):
  • milestones      - Show 120-day milestone tracking
  • equipment       - Show medical equipment status
  • antibiotics     - Show antibiotic monitoring
  • report          - Show throughput analysis

UTILITY:
  • mode <mode>     - Change output mode (table/summary/json)
  • set <patient>   - Set current patient context
  • help            - Show this help menu
  • exit            - Exit the CLI
"""
        return help_text


def main():
    """Main entry point for Zav CLI."""
    cli = ZavCLI()

    print(cli.show_help())
    print("\nStarting interactive mode...")
    print("Type 'help' for commands or 'exit' to quit.\n")

    while True:
        try:
            user_input = input("zav> ").strip()

            if not user_input:
                continue

            if user_input.lower() == "exit":
                print("Goodbye!")
                break

            # Route commands
            if user_input.lower() == "alerts":
                print(cli.show_alerts())
            elif user_input.lower() == "beds":
                print(cli.show_bed_forecast())
            elif user_input.lower() == "discharge":
                print(cli.show_discharge_ready())
            elif user_input.lower() == "schedule":
                print(cli.show_operation_schedule())
            elif user_input.lower() == "overstay":
                print(cli.show_overstay_patients())
            elif user_input.lower() == "consultations":
                print(cli.show_consultation_queue())
            elif user_input.lower() == "milestones":
                print(cli.show_milestones())
            elif user_input.lower() == "equipment":
                print(cli.show_equipment_status())
            elif user_input.lower() == "report":
                print(cli.show_throughput_report())
            elif user_input.lower() == "help":
                print(cli.show_help())
            else:
                print(ZavOutputFormatter.alert(f"Unknown command: {user_input}", "warning"))
                print("Type 'help' for available commands")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(ZavOutputFormatter.alert(f"Error: {e}", "warning"))


if __name__ == "__main__":
    main()
