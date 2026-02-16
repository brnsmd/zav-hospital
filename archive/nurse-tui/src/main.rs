//! Nurse Station TUI - Temperature Sheet Only
//!
//! Simple workflow:
//! 1. Login (L) - select nurse
//! 2. Load patients (R) - fetch from EMR
//! 3. Select all (A) - auto-select normal patients
//! 4. Submit (Enter → Y) - BRRRRRT to EMR
//!
//! Weird patients (abnormal vitals) are flagged and skipped

mod app;
mod emr;
mod ui;

use std::io;
use anyhow::Result;
use crossterm::{
    event::{self, Event, KeyCode, KeyEventKind},
    execute,
    terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
};
use ratatui::prelude::*;
use tokio::sync::mpsc;

use app::{App, AppMode, EmrStatus, NurseProfile};
use emr::EmrClient;

/// Results from async tasks
enum TaskResult {
    LoginSuccess(EmrClient),
    LoginFailed(String),
    TemperatureLoaded(EmrClient, Vec<emr::Patient>, Vec<(String, Option<emr::Vitals>)>),
    TemperatureLoadFailed(EmrClient, String),
    SubmitProgress(usize),
    SubmitComplete(EmrClient),
    SubmitFailed(EmrClient, String),
}

#[tokio::main]
async fn main() -> Result<()> {
    // Load environment
    dotenvy::dotenv().ok();

    // Setup terminal
    enable_raw_mode()?;
    let mut stdout = io::stdout();
    execute!(stdout, EnterAlternateScreen)?;
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;

    // Create app
    let mut app = App::new();

    // Channel for async results
    let (result_tx, mut result_rx) = mpsc::channel::<TaskResult>(10);

    // Run main loop
    let result = run_app(&mut terminal, &mut app, result_tx, &mut result_rx).await;

    // Restore terminal
    disable_raw_mode()?;
    execute!(terminal.backend_mut(), LeaveAlternateScreen)?;
    terminal.show_cursor()?;

    result
}

async fn run_app<B: Backend>(
    terminal: &mut Terminal<B>,
    app: &mut App,
    result_tx: mpsc::Sender<TaskResult>,
    result_rx: &mut mpsc::Receiver<TaskResult>,
) -> Result<()> {
    let mut last_tick = std::time::Instant::now();
    let tick_rate = std::time::Duration::from_millis(100);

    loop {
        terminal.draw(|f| ui::render(f, app))?;

        // Tick for spinner animation
        if last_tick.elapsed() >= tick_rate {
            app.tick();
            last_tick = std::time::Instant::now();
        }

        // Check for async results (non-blocking)
        while let Ok(result) = result_rx.try_recv() {
            match result {
                TaskResult::LoginSuccess(client) => {
                    app.emr_client = Some(client);
                    app.emr_status = EmrStatus::Connected;
                    app.is_loading = false;
                    app.toast_success("Logged in to EMR");
                }
                TaskResult::LoginFailed(e) => {
                    app.emr_status = EmrStatus::Error(e.clone());
                    app.is_loading = false;
                    app.toast_error(format!("Login failed: {}", truncate(&e, 30)));
                }
                TaskResult::TemperatureLoaded(client, patients, vitals) => {
                    let count = patients.len();
                    app.emr_client = Some(client);
                    app.set_temperature_data(patients, vitals);
                    app.is_loading = false;
                    app.refresh();
                    app.toast_success(format!("Loaded {} patients", count));
                }
                TaskResult::TemperatureLoadFailed(client, e) => {
                    app.emr_client = Some(client);
                    app.emr_status = EmrStatus::Error(e.clone());
                    app.is_loading = false;
                    app.toast_error(format!("Load failed: {}", truncate(&e, 30)));
                }
                TaskResult::SubmitProgress(n) => {
                    app.update_submit_progress(n);
                }
                TaskResult::SubmitComplete(client) => {
                    let count = app.submit_total;
                    app.emr_client = Some(client);
                    app.finish_submit();
                    app.toast_success(format!("✓ Submitted {} records", count));
                }
                TaskResult::SubmitFailed(client, e) => {
                    app.emr_client = Some(client);
                    app.mode = AppMode::Temperature;
                    app.toast_error(format!("Submit failed: {}", truncate(&e, 30)));
                }
            }
        }

        if event::poll(std::time::Duration::from_millis(50))? {
            if let Event::Key(key) = event::read()? {
                if key.kind == KeyEventKind::Press {
                    match (&app.mode, key.code) {
                        // Quit (not in dialogs)
                        (AppMode::Temperature | AppMode::NurseSelect, KeyCode::Char('q') | KeyCode::Char('Q')) => {
                            return Ok(());
                        }

                        // Navigation
                        (AppMode::Temperature, KeyCode::Up | KeyCode::Char('k')) => {
                            app.previous_patient();
                        }
                        (AppMode::Temperature, KeyCode::Down | KeyCode::Char('j')) => {
                            app.next_patient();
                        }

                        // Refresh / Load data
                        (AppMode::Temperature, KeyCode::Char('r') | KeyCode::Char('R')) => {
                            if app.emr_status == EmrStatus::Connected && !app.is_loading {
                                if let Some(client) = app.emr_client.take() {
                                    app.is_loading = true;
                                    app.loading_message = Some("Loading patients...".to_string());
                                    let tx = result_tx.clone();
                                    tokio::spawn(async move {
                                        match do_load_temperature(client).await {
                                            Ok((client, patients, vitals)) => {
                                                let _ = tx.send(TaskResult::TemperatureLoaded(client, patients, vitals)).await;
                                            }
                                            Err((client, e)) => {
                                                let _ = tx.send(TaskResult::TemperatureLoadFailed(client, e.to_string())).await;
                                            }
                                        }
                                    });
                                }
                            }
                        }

                        // Login - open nurse selector
                        (AppMode::Temperature, KeyCode::Char('l') | KeyCode::Char('L')) => {
                            if app.emr_client.is_none() && !app.is_loading {
                                app.enter_nurse_select();
                            }
                        }

                        // Nurse Select: number keys 1-9, 0 for 10th
                        (AppMode::NurseSelect, KeyCode::Char(c @ '1'..='9')) => {
                            let idx = (c as usize) - ('1' as usize);
                            if let Some(nurse) = app.get_nurse(idx).cloned() {
                                start_login(app, nurse, result_tx.clone());
                            }
                        }
                        (AppMode::NurseSelect, KeyCode::Char('0')) => {
                            if let Some(nurse) = app.get_nurse(9).cloned() {
                                start_login(app, nurse, result_tx.clone());
                            }
                        }

                        // Nurse Select: + to add new nurse
                        (AppMode::NurseSelect, KeyCode::Char('+') | KeyCode::Char('=')) => {
                            if app.nurses.len() < 10 {
                                app.start_add_nurse();
                            }
                        }

                        // Nurse Select: - to remove selected nurse
                        (AppMode::NurseSelect, KeyCode::Char('-')) => {
                            if !app.nurses.is_empty() {
                                app.remove_nurse(app.selected_nurse);
                                if app.selected_nurse >= app.nurses.len() && app.selected_nurse > 0 {
                                    app.selected_nurse -= 1;
                                }
                            }
                        }

                        // Nurse Select: navigate
                        (AppMode::NurseSelect, KeyCode::Up | KeyCode::Char('k')) => {
                            if app.selected_nurse > 0 {
                                app.selected_nurse -= 1;
                            }
                        }
                        (AppMode::NurseSelect, KeyCode::Down | KeyCode::Char('j')) => {
                            if app.selected_nurse < app.nurses.len().saturating_sub(1) {
                                app.selected_nurse += 1;
                            }
                        }

                        // Nurse Select: Enter to login
                        (AppMode::NurseSelect, KeyCode::Enter) => {
                            if let Some(nurse) = app.get_nurse(app.selected_nurse).cloned() {
                                start_login(app, nurse, result_tx.clone());
                            }
                        }

                        // Add Nurse: type email
                        (AppMode::AddNurse, KeyCode::Char(c)) => {
                            app.handle_add_nurse_input(c);
                        }
                        (AppMode::AddNurse, KeyCode::Backspace) => {
                            app.handle_add_nurse_backspace();
                        }
                        (AppMode::AddNurse, KeyCode::Enter) => {
                            app.confirm_nurse_email();
                        }

                        // Add Nurse Password
                        (AppMode::AddNursePass, KeyCode::Char(c)) => {
                            app.handle_add_nurse_input(c);
                        }
                        (AppMode::AddNursePass, KeyCode::Backspace) => {
                            app.handle_add_nurse_backspace();
                        }
                        (AppMode::AddNursePass, KeyCode::Enter) => {
                            app.confirm_nurse_password();
                        }

                        // Temperature: Toggle selection
                        (AppMode::Temperature, KeyCode::Char(' ')) => {
                            app.toggle_temperature_selection();
                        }

                        // Temperature: Select all
                        (AppMode::Temperature, KeyCode::Char('a') | KeyCode::Char('A')) => {
                            app.select_all_temperature();
                        }

                        // Temperature: Submit (Enter)
                        (AppMode::Temperature, KeyCode::Enter) => {
                            app.start_confirm();
                        }

                        // Confirm dialog: Yes
                        (AppMode::Confirming, KeyCode::Char('y') | KeyCode::Char('Y')) => {
                            if let Some(client) = app.emr_client.take() {
                                let records = app.get_selected_temperature_records();
                                if !records.is_empty() {
                                    app.confirm_submit();
                                    let tx = result_tx.clone();
                                    tokio::spawn(async move {
                                        match do_submit_temperatures(client, records, tx.clone()).await {
                                            Ok(client) => {
                                                let _ = tx.send(TaskResult::SubmitComplete(client)).await;
                                            }
                                            Err((client, e)) => {
                                                let _ = tx.send(TaskResult::SubmitFailed(client, e.to_string())).await;
                                            }
                                        }
                                    });
                                } else {
                                    app.emr_client = Some(client);
                                }
                            }
                        }

                        // Confirm dialog: No
                        (AppMode::Confirming, KeyCode::Char('n') | KeyCode::Char('N') | KeyCode::Esc) => {
                            app.cancel_submit();
                        }

                        // Back (Esc)
                        (_, KeyCode::Esc) => {
                            app.back();
                        }

                        _ => {}
                    }
                }
            }
        }
    }
}

/// Start login process
fn start_login(app: &mut App, nurse: NurseProfile, tx: mpsc::Sender<TaskResult>) {
    app.is_loading = true;
    app.loading_message = Some(format!("Logging in as {}...", nurse.name));
    app.emr_status = EmrStatus::Disconnected;
    app.current_nurse = Some(nurse.clone());
    app.mode = AppMode::Temperature;

    tokio::spawn(async move {
        match do_login(nurse).await {
            Ok(client) => {
                let _ = tx.send(TaskResult::LoginSuccess(client)).await;
            }
            Err(e) => {
                let _ = tx.send(TaskResult::LoginFailed(e.to_string())).await;
            }
        }
    });
}

/// Perform login to EMR
async fn do_login(nurse: NurseProfile) -> Result<EmrClient> {
    let mut client = EmrClient::new().await?;
    client.login(&nurse.email, &nurse.password).await?;
    Ok(client)
}

/// Load temperature data
async fn do_load_temperature(
    client: EmrClient,
) -> Result<(EmrClient, Vec<emr::Patient>, Vec<(String, Option<emr::Vitals>)>), (EmrClient, anyhow::Error)> {
    let patients = match client.get_hospitalized_patients().await {
        Ok(p) => p,
        Err(e) => return Err((client, e)),
    };

    // Use default vitals (no history fetch for speed)
    let vitals_map: Vec<(String, Option<emr::Vitals>)> = patients
        .iter()
        .map(|p| (p.case_id.clone(), None))
        .collect();

    Ok((client, patients, vitals_map))
}

/// Submit temperature records one by one (BRRRRRT)
async fn do_submit_temperatures(
    client: EmrClient,
    records: Vec<(String, emr::Vitals)>,
    tx: mpsc::Sender<TaskResult>,
) -> Result<EmrClient, (EmrClient, anyhow::Error)> {
    for (i, (case_id, vitals)) in records.iter().enumerate() {
        let _ = tx.send(TaskResult::SubmitProgress(i)).await;

        if let Err(e) = client.submit_temperature(case_id, vitals).await {
            return Err((client, e));
        }

        tokio::time::sleep(tokio::time::Duration::from_millis(500)).await;
    }

    Ok(client)
}

/// Truncate string for toast display
fn truncate(s: &str, max: usize) -> String {
    if s.chars().count() > max {
        format!("{}...", s.chars().take(max - 3).collect::<String>())
    } else {
        s.to_string()
    }
}
