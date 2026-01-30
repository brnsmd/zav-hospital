//! App state and logic - SIMPLIFIED: Temperature only

use chrono::Local;
use std::time::Instant;

use crate::emr::{EmrClient, Patient, Vitals, TemperatureRecord, generate_vitals};

/// Spinner frames for loading animation
const SPINNER_FRAMES: &[&str] = &["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"];

/// Toast message types
#[derive(Debug, Clone)]
pub enum ToastType {
    Success,
    Error,
}

/// Toast notification
#[derive(Debug, Clone)]
pub struct Toast {
    pub message: String,
    pub toast_type: ToastType,
    pub created_at: Instant,
}

impl Toast {
    pub fn success(message: impl Into<String>) -> Self {
        Self {
            message: message.into(),
            toast_type: ToastType::Success,
            created_at: Instant::now(),
        }
    }

    pub fn error(message: impl Into<String>) -> Self {
        Self {
            message: message.into(),
            toast_type: ToastType::Error,
            created_at: Instant::now(),
        }
    }

    /// Check if toast should still be visible (3 seconds for success, 5 for error)
    pub fn is_visible(&self) -> bool {
        let duration = match self.toast_type {
            ToastType::Error => std::time::Duration::from_secs(5),
            ToastType::Success => std::time::Duration::from_secs(3),
        };
        self.created_at.elapsed() < duration
    }
}

/// Main app state
pub struct App {
    pub mode: AppMode,
    pub last_sync: Option<String>,
    pub emr_status: EmrStatus,

    // EMR client (optional - created on login)
    pub emr_client: Option<EmrClient>,

    // Loading state
    pub is_loading: bool,
    pub loading_message: Option<String>,

    // Spinner animation
    pub spinner_frame: usize,

    // Toast notifications
    pub toast: Option<Toast>,

    // Temperature data
    pub temperature_data: Option<Vec<TemperatureRecord>>,
    pub temperature_selected: usize,

    // Submit progress
    pub submit_total: usize,
    pub submit_current: usize,

    // Nurse profiles (up to 10)
    pub nurses: Vec<NurseProfile>,
    pub selected_nurse: usize,
    pub current_nurse: Option<NurseProfile>,

    // Input buffers for adding nurse
    pub input_buffer: String,
    pub input_email: String,
}

/// App display mode
#[derive(Debug, Clone, PartialEq)]
pub enum AppMode {
    Temperature,    // Main screen - temperature list
    NurseSelect,    // Nurse selection for login
    AddNurse,       // Adding new nurse (email input)
    AddNursePass,   // Adding new nurse (password input)
    Confirming,     // Confirmation dialog
    Submitting,     // Progress indicator
}

/// Saved nurse profile
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct NurseProfile {
    pub name: String,
    pub email: String,
    pub password: String,
}

/// EMR connection status
#[derive(Debug, Clone, PartialEq)]
pub enum EmrStatus {
    Disconnected,
    Connected,
    Error(String),
}

const CONFIG_FILE: &str = "nurse-tui.json";

impl App {
    pub fn new() -> Self {
        let nurses = Self::load_nurses();

        Self {
            mode: AppMode::Temperature,
            last_sync: None,
            emr_status: EmrStatus::Disconnected,
            emr_client: None,
            is_loading: false,
            loading_message: None,
            spinner_frame: 0,
            toast: None,
            temperature_data: None,
            temperature_selected: 0,
            submit_total: 0,
            submit_current: 0,
            nurses,
            selected_nurse: 0,
            current_nurse: None,
            input_buffer: String::new(),
            input_email: String::new(),
        }
    }

    /// Advance spinner frame (call on tick)
    pub fn tick(&mut self) {
        self.spinner_frame = (self.spinner_frame + 1) % SPINNER_FRAMES.len();

        // Clear expired toast
        if let Some(ref toast) = self.toast {
            if !toast.is_visible() {
                self.toast = None;
            }
        }
    }

    /// Get current spinner character
    pub fn spinner(&self) -> &'static str {
        SPINNER_FRAMES[self.spinner_frame]
    }

    /// Show success toast
    pub fn toast_success(&mut self, msg: impl Into<String>) {
        self.toast = Some(Toast::success(msg));
    }

    /// Show error toast
    pub fn toast_error(&mut self, msg: impl Into<String>) {
        self.toast = Some(Toast::error(msg));
    }

    /// Load nurses from config file
    fn load_nurses() -> Vec<NurseProfile> {
        let config_path = dirs::config_dir()
            .map(|p| p.join("nurse-tui").join(CONFIG_FILE))
            .unwrap_or_else(|| CONFIG_FILE.into());

        if let Ok(content) = std::fs::read_to_string(&config_path) {
            serde_json::from_str(&content).unwrap_or_default()
        } else {
            // Default nurses from env
            let mut nurses = Vec::new();
            if let (Ok(email), Ok(pass)) = (
                std::env::var("NURSE_EMR_EMAIL"),
                std::env::var("NURSE_EMR_PASSWORD"),
            ) {
                let name = email.split('@').next().unwrap_or("Nurse").to_string();
                nurses.push(NurseProfile { name, email, password: pass });
            }
            nurses
        }
    }

    /// Save nurses to config file
    pub fn save_nurses(&self) {
        let config_dir = dirs::config_dir()
            .map(|p| p.join("nurse-tui"))
            .unwrap_or_else(|| ".".into());

        let _ = std::fs::create_dir_all(&config_dir);
        let config_path = config_dir.join(CONFIG_FILE);

        if let Ok(json) = serde_json::to_string_pretty(&self.nurses) {
            let _ = std::fs::write(config_path, json);
        }
    }

    /// Add a new nurse (max 10)
    pub fn add_nurse(&mut self, name: String, email: String, password: String) -> bool {
        if self.nurses.len() >= 10 {
            return false;
        }
        self.nurses.push(NurseProfile { name, email, password });
        self.save_nurses();
        true
    }

    /// Remove nurse by index
    pub fn remove_nurse(&mut self, index: usize) -> bool {
        if index < self.nurses.len() {
            self.nurses.remove(index);
            self.save_nurses();
            true
        } else {
            false
        }
    }

    /// Get nurse for login by index
    pub fn get_nurse(&self, index: usize) -> Option<&NurseProfile> {
        self.nurses.get(index)
    }

    /// Enter nurse select mode
    pub fn enter_nurse_select(&mut self) {
        self.mode = AppMode::NurseSelect;
        self.selected_nurse = 0;
    }

    /// Start adding new nurse
    pub fn start_add_nurse(&mut self) {
        self.mode = AppMode::AddNurse;
        self.input_buffer.clear();
        self.input_email.clear();
    }

    /// Handle input for adding nurse
    pub fn handle_add_nurse_input(&mut self, c: char) {
        if self.input_buffer.len() < 50 {
            self.input_buffer.push(c);
        }
    }

    /// Backspace in input
    pub fn handle_add_nurse_backspace(&mut self) {
        self.input_buffer.pop();
    }

    /// Confirm email, move to password
    pub fn confirm_nurse_email(&mut self) {
        if !self.input_buffer.is_empty() {
            self.input_email = self.input_buffer.clone();
            self.input_buffer.clear();
            self.mode = AppMode::AddNursePass;
        }
    }

    /// Confirm password, add nurse
    pub fn confirm_nurse_password(&mut self) {
        if !self.input_buffer.is_empty() {
            let email = self.input_email.clone();
            let password = self.input_buffer.clone();
            let name = email.split('@').next().unwrap_or("Nurse").to_string();
            self.add_nurse(name, email, password);
            self.input_buffer.clear();
            self.input_email.clear();
            self.mode = AppMode::NurseSelect;
        }
    }

    /// Navigate to next patient
    pub fn next_patient(&mut self) {
        if let Some(ref data) = self.temperature_data {
            if !data.is_empty() {
                self.temperature_selected = (self.temperature_selected + 1) % data.len();
            }
        }
    }

    /// Navigate to previous patient
    pub fn previous_patient(&mut self) {
        if let Some(ref data) = self.temperature_data {
            if !data.is_empty() {
                self.temperature_selected = if self.temperature_selected == 0 {
                    data.len() - 1
                } else {
                    self.temperature_selected - 1
                };
            }
        }
    }

    /// Update last sync time
    pub fn refresh(&mut self) {
        self.last_sync = Some(Local::now().format("%H:%M").to_string());
    }

    /// Back action
    pub fn back(&mut self) {
        match self.mode {
            AppMode::Temperature => {}
            AppMode::NurseSelect => {
                self.mode = AppMode::Temperature;
            }
            AppMode::AddNurse | AppMode::AddNursePass => {
                self.input_buffer.clear();
                self.input_email.clear();
                self.mode = AppMode::NurseSelect;
            }
            AppMode::Confirming => {
                self.mode = AppMode::Temperature;
            }
            AppMode::Submitting => {
                // Can't go back while submitting
            }
        }
    }

    // Temperature methods

    /// Toggle selection of current temperature record
    pub fn toggle_temperature_selection(&mut self) {
        if let Some(ref mut data) = self.temperature_data {
            if let Some(record) = data.get_mut(self.temperature_selected) {
                // Don't allow selecting records that need manual review
                if !record.needs_manual_review {
                    record.selected = !record.selected;
                }
            }
        }
    }

    /// Select all temperature records (except those needing review)
    pub fn select_all_temperature(&mut self) {
        if let Some(ref mut data) = self.temperature_data {
            let all_selected = data.iter()
                .filter(|r| !r.needs_manual_review)
                .all(|r| r.selected);

            for record in data.iter_mut() {
                if !record.needs_manual_review {
                    record.selected = !all_selected;
                }
            }
        }
    }

    /// Start confirmation dialog
    pub fn start_confirm(&mut self) {
        let has_selected = self.temperature_data
            .as_ref()
            .map(|d| d.iter().any(|r| r.selected))
            .unwrap_or(false);

        if has_selected {
            self.mode = AppMode::Confirming;
        }
    }

    /// Confirm submission (Y pressed)
    pub fn confirm_submit(&mut self) {
        if self.mode == AppMode::Confirming {
            let count = self.temperature_data
                .as_ref()
                .map(|d| d.iter().filter(|r| r.selected).count())
                .unwrap_or(0);

            self.submit_total = count;
            self.submit_current = 0;
            self.mode = AppMode::Submitting;
        }
    }

    /// Cancel submission (N pressed)
    pub fn cancel_submit(&mut self) {
        if self.mode == AppMode::Confirming {
            self.mode = AppMode::Temperature;
        }
    }

    /// Update submit progress
    pub fn update_submit_progress(&mut self, current: usize) {
        self.submit_current = current;
    }

    /// Finish submission - remove submitted records
    pub fn finish_submit(&mut self) {
        if let Some(ref mut data) = self.temperature_data {
            data.retain(|r| !r.selected);
        }
        self.mode = AppMode::Temperature;
    }

    /// Get count of patients needing review (weird patients)
    pub fn weird_patient_count(&self) -> usize {
        self.temperature_data
            .as_ref()
            .map(|d| d.iter().filter(|r| r.needs_manual_review).count())
            .unwrap_or(0)
    }

    /// Get count of normal patients
    pub fn normal_patient_count(&self) -> usize {
        self.temperature_data
            .as_ref()
            .map(|d| d.iter().filter(|r| !r.needs_manual_review).count())
            .unwrap_or(0)
    }

    /// Get selected count
    pub fn selected_count(&self) -> usize {
        self.temperature_data
            .as_ref()
            .map(|d| d.iter().filter(|r| r.selected).count())
            .unwrap_or(0)
    }

    /// Get selected temperature records for submission
    pub fn get_selected_temperature_records(&self) -> Vec<(String, Vitals)> {
        self.temperature_data
            .as_ref()
            .map(|data| {
                data.iter()
                    .filter(|r| r.selected)
                    .map(|r| (r.patient.case_id.clone(), r.vitals.clone()))
                    .collect()
            })
            .unwrap_or_default()
    }

    /// Set temperature data from EMR
    pub fn set_temperature_data(&mut self, patients: Vec<Patient>, vitals_map: Vec<(String, Option<Vitals>)>) {
        let records: Vec<TemperatureRecord> = patients
            .into_iter()
            .zip(vitals_map.into_iter())
            .map(|(patient, (_case_id, yesterday_vitals))| {
                let (generated, needs_review, reason) = generate_vitals(yesterday_vitals.as_ref());

                TemperatureRecord {
                    patient,
                    vitals: generated,
                    yesterday_vitals,
                    needs_manual_review: needs_review,
                    review_reason: reason,
                    selected: false,
                }
            })
            .collect();

        self.temperature_data = Some(records);
        self.temperature_selected = 0;
    }
}
