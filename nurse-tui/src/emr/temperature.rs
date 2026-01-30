//! Temperature sheet automation
//!
//! Fetches patients and vitals from EMR, generates today's values

use anyhow::{anyhow, Result};
use chrono::{Local, NaiveDate};
use serde::{Deserialize, Serialize};
use std::io::Write;

use super::EmrClient;

/// Log to file (visible even in TUI mode)
fn log(msg: &str) {
    if let Ok(mut f) = std::fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open("/tmp/nurse-tui-submit.log")
    {
        let _ = writeln!(f, "[{}] {}", chrono::Local::now().format("%H:%M:%S"), msg);
    }
}

/// Patient from hospitalized list
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Patient {
    pub case_id: String,
    pub card_number: String,
    pub name: String,
    pub ward: String,
    pub bed: String,
    pub diagnosis: String,
    pub disease_day: i32,
}

/// Vital signs record
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Vitals {
    #[serde(skip)]
    pub date: Option<NaiveDate>,
    pub temp_morning: f32,
    pub temp_evening: f32,
    pub bp_systolic_morning: i32,
    pub bp_diastolic_morning: i32,
    pub bp_systolic_evening: i32,
    pub bp_diastolic_evening: i32,
    pub pulse_morning: i32,
    pub pulse_evening: i32,
}

impl Vitals {
    pub fn new_for_today() -> Self {
        Self {
            date: Some(Local::now().date_naive()),
            temp_morning: 36.6,
            temp_evening: 36.6,
            bp_systolic_morning: 120,
            bp_diastolic_morning: 80,
            bp_systolic_evening: 120,
            bp_diastolic_evening: 80,
            pulse_morning: 72,
            pulse_evening: 72,
        }
    }
}

/// Temperature record for submission
#[derive(Debug, Clone)]
pub struct TemperatureRecord {
    pub patient: Patient,
    pub vitals: Vitals,
    pub yesterday_vitals: Option<Vitals>,
    pub needs_manual_review: bool,
    pub review_reason: Option<String>,
    pub selected: bool,
}

impl EmrClient {
    /// Fetch list of hospitalized patients (all pages)
    pub async fn get_hospitalized_patients(&self) -> Result<Vec<Patient>> {
        let page_arc = self.page();
        let page = page_arc.lock().await;

        // Navigate to hospitalized patients list
        page.goto("https://doc.hospital.mia.software/case/hospitalized/hospitalized/")
            .await?;
        tokio::time::sleep(tokio::time::Duration::from_secs(3)).await;

        let mut all_patients: Vec<Patient> = Vec::new();
        let mut page_num = 1;

        loop {

            // Extract patient data from table using JavaScript
            // Column indices (from debug_emr):
            // [0] Number, [1] Card, [2] Name, [3] Case date, [4] Placement date,
            // [5] Type, [6] Age, [7] Sex, [8] Admission Dx, [9] Clinical Dx,
            // [10] Reanimation, [11] Doctor, [12] Ward, [13] Bed, [14] Disease day, [15] Actions
            let patients_js = r#"
                (() => {
                    const rows = document.querySelectorAll('table tbody tr');
                    const patients = [];
                    rows.forEach(row => {
                        const cells = row.querySelectorAll('td');
                        if (cells.length >= 14) {
                            // Extract case_id from link - find link with numeric case ID
                            const links = row.querySelectorAll('a');
                            let caseId = '';
                            for (const link of links) {
                                const match = link.href.match(/\/case\/(\d+)\/?/);
                                if (match) {
                                    caseId = match[1];
                                    break;
                                }
                            }

                            if (caseId) {  // Only add if we found a valid case ID
                                patients.push({
                                    case_id: caseId,
                                    card_number: cells[1]?.textContent?.trim() || '',
                                    name: cells[2]?.textContent?.trim() || '',
                                    ward: cells[12]?.textContent?.trim() || '',
                                    bed: cells[13]?.textContent?.trim() || '-',
                                    diagnosis: cells[9]?.textContent?.trim() || cells[8]?.textContent?.trim() || '',
                                    disease_day: parseInt(cells[14]?.textContent?.trim()) || 0,
                                });
                            }
                        }
                    });
                    return JSON.stringify(patients);
                })()
            "#;

            let result = page.evaluate(patients_js).await?;
            let json_str = result.into_value::<String>()?;
            let patients: Vec<Patient> = serde_json::from_str(&json_str)?;

            if patients.is_empty() {
                break;
            }

            all_patients.extend(patients);

            // Try to click "Next" page in pagination
            // EMR uses Bootstrap pagination: <ul class="pagination"><li><a>1</a></li><li><a>2</a></li></ul>
            let has_next_js = format!(r#"
                (() => {{
                    // Find pagination and click next page number
                    const pagination = document.querySelector('ul.pagination');
                    if (!pagination) return false;

                    const links = pagination.querySelectorAll('li a');
                    const currentPage = {};

                    // Find link for next page
                    for (const link of links) {{
                        const pageNum = parseInt(link.textContent.trim());
                        if (pageNum === currentPage + 1) {{
                            link.click();
                            return true;
                        }}
                    }}
                    return false;
                }})()
            "#, page_num);

            let has_next = page.evaluate(has_next_js).await?;
            let clicked = has_next.into_value::<bool>().unwrap_or(false);

            if !clicked {
                break;
            }

            // Wait for next page to load
            tokio::time::sleep(tokio::time::Duration::from_secs(2)).await;
            page_num += 1;

            // Safety limit
            if page_num > 10 {
                break;
            }
        }

        Ok(all_patients)
    }

    /// Fetch vitals history for a patient (last N days)
    pub async fn get_patient_vitals(&self, case_id: &str, days: i32) -> Result<Vec<Vitals>> {
        let page_arc = self.page();
        let page = page_arc.lock().await;

        // Navigate to patient's temperature sheet
        let url = format!(
            "https://doc.hospital.mia.software/case/{}/#/temperature-sheet",
            case_id
        );
        page.goto(&url).await?;
        tokio::time::sleep(tokio::time::Duration::from_secs(2)).await;

        // Extract vitals from temperature sheet table
        let vitals_js = format!(
            r#"
            (() => {{
                const rows = document.querySelectorAll('table tbody tr');
                const vitals = [];
                const limit = {};
                let count = 0;

                rows.forEach(row => {{
                    if (count >= limit) return;
                    const cells = row.querySelectorAll('td');
                    if (cells.length >= 10) {{
                        vitals.push({{
                            temp_morning: parseFloat(cells[7]?.textContent) || 36.6,
                            temp_evening: parseFloat(cells[8]?.textContent) || 36.6,
                            bp_systolic_morning: parseInt(cells[1]?.textContent) || 120,
                            bp_diastolic_morning: parseInt(cells[2]?.textContent) || 80,
                            bp_systolic_evening: parseInt(cells[3]?.textContent) || 120,
                            bp_diastolic_evening: parseInt(cells[4]?.textContent) || 80,
                            pulse_morning: parseInt(cells[5]?.textContent) || 72,
                            pulse_evening: parseInt(cells[6]?.textContent) || 72,
                        }});
                        count++;
                    }}
                }});
                return JSON.stringify(vitals);
            }})()
        "#,
            days
        );

        let result = page.evaluate(vitals_js.as_str()).await?;
        let json_str = result.into_value::<String>()?;

        // Parse vitals (date is optional/not included in JS extraction)
        let raw_vitals: Vec<serde_json::Value> = serde_json::from_str(&json_str)?;
        let vitals: Vec<Vitals> = raw_vitals
            .into_iter()
            .map(|v| Vitals {
                date: None,
                temp_morning: v["temp_morning"].as_f64().unwrap_or(36.6) as f32,
                temp_evening: v["temp_evening"].as_f64().unwrap_or(36.6) as f32,
                bp_systolic_morning: v["bp_systolic_morning"].as_i64().unwrap_or(120) as i32,
                bp_diastolic_morning: v["bp_diastolic_morning"].as_i64().unwrap_or(80) as i32,
                bp_systolic_evening: v["bp_systolic_evening"].as_i64().unwrap_or(120) as i32,
                bp_diastolic_evening: v["bp_diastolic_evening"].as_i64().unwrap_or(80) as i32,
                pulse_morning: v["pulse_morning"].as_i64().unwrap_or(72) as i32,
                pulse_evening: v["pulse_evening"].as_i64().unwrap_or(72) as i32,
            })
            .collect();

        Ok(vitals)
    }

    /// Submit temperature record for a patient
    /// EMR temperature sheet has form already visible - just fill and save
    pub async fn submit_temperature(&self, case_id: &str, vitals: &Vitals) -> Result<()> {
        log(&format!("Starting submit for case_id={}", case_id));
        let page_arc = self.page();
        let page = page_arc.lock().await;

        // Navigate to patient's temperature sheet
        let url = format!(
            "https://doc.hospital.mia.software/case/{}/#/temperature-sheet",
            case_id
        );
        log(&format!("Navigating to {}", url));
        page.goto(&url).await?;
        tokio::time::sleep(tokio::time::Duration::from_secs(3)).await;

        // Check actual URL
        let actual_url = page.url().await?.unwrap_or_default();
        log(&format!("Actual URL: {}", actual_url));

        // Check if date picker exists
        let has_picker = page.evaluate(r#"!!document.querySelector('.date-picker .ant-picker')"#).await?;
        let has_picker_val = has_picker.into_value::<bool>().unwrap_or(false);
        log(&format!("Has date picker: {}", has_picker_val));

        if !has_picker_val {
            return Err(anyhow!("Date picker not found on page - wrong page?"));
        }

        // Step 1: Click the ant-picker with native chromiumoxide click
        log("Finding and clicking date picker...");
        match page.find_element(".date-picker .ant-picker").await {
            Ok(picker_el) => {
                picker_el.click().await?;
                log("Clicked date picker");
            }
            Err(e) => {
                log(&format!("Picker not found: {:?}, trying input...", e));
                // Fallback: try the input directly
                match page.find_element(".date-picker .ant-picker input").await {
                    Ok(input_el) => {
                        input_el.click().await?;
                        log("Clicked date picker input");
                    }
                    Err(e2) => {
                        return Err(anyhow!("Could not find date picker: {:?}", e2));
                    }
                }
            }
        }

        // Wait for dropdown to appear
        tokio::time::sleep(tokio::time::Duration::from_secs(2)).await;

        // Step 2: Click today cell in the dropdown (JS click works here)
        let select_today_js = r#"
            (() => {
                // Find visible dropdown (not hidden)
                const dropdown = document.querySelector('.ant-picker-dropdown:not(.ant-picker-dropdown-hidden)');
                if (!dropdown) {
                    return 'no-visible-dropdown';
                }

                // Try clicking the cell marked as today
                const todayCell = dropdown.querySelector('.ant-picker-cell-today .ant-picker-cell-inner');
                if (todayCell) {
                    todayCell.click();
                    return 'today-cell-clicked';
                }

                // Fallback: Try "Today" button at bottom
                const todayBtn = dropdown.querySelector('.ant-picker-today-btn');
                if (todayBtn) {
                    todayBtn.click();
                    return 'today-btn-clicked';
                }

                return 'dropdown-found-no-today';
            })()
        "#;

        let today_result = page.evaluate(select_today_js).await?;
        let today_str = today_result.into_value::<String>().unwrap_or_default();
        log(&format!("Today click result: {}", today_str));

        if today_str == "no-visible-dropdown" {
            return Err(anyhow!("Date picker dropdown did not open"));
        }

        tokio::time::sleep(tokio::time::Duration::from_millis(500)).await;

        // Verify date was set
        let date_check = page.evaluate(r#"
            (() => {
                const input = document.querySelector('.date-picker .ant-picker input');
                return input?.value || '';
            })()
        "#).await?;
        let date_val = date_check.into_value::<String>().unwrap_or_default();
        log(&format!("Date value after selection: '{}'", date_val));

        if date_val.is_empty() {
            return Err(anyhow!("Date was not set - required field"));
        }

        // Fill form using NATIVE keyboard typing (not JS events)
        // This is the only way to reliably trigger React/Ant Design state updates
        let values = [
            format!("{}", vitals.bp_systolic_morning),
            format!("{}", vitals.bp_systolic_evening),
            format!("{}", vitals.bp_diastolic_morning),
            format!("{}", vitals.bp_diastolic_evening),
            format!("{}", vitals.pulse_morning),
            format!("{}", vitals.pulse_evening),
            format!("{:.1}", vitals.temp_morning),   // 1 decimal for temperature
            format!("{:.1}", vitals.temp_evening),
        ];

        log(&format!("Filling {} values: {:?}", values.len(), values));

        // Get all input elements using CSS selector
        let input_selector = "input.ant-input-number-input";

        for (i, val) in values.iter().enumerate() {
            // Find the i-th input using nth-of-type or by index
            let nth_selector = format!(
                r#"document.querySelectorAll('{}')[{}]"#,
                input_selector, i
            );

            // Click to focus (using JS to get element, then triple-click to select all)
            let focus_js = format!(
                r#"
                (() => {{
                    const inp = {};
                    if (!inp) return 'not-found';
                    inp.focus();
                    inp.select();
                    return 'focused';
                }})()
                "#,
                nth_selector
            );

            let focus_result = page.evaluate(focus_js).await?;
            let focus_str = focus_result.into_value::<String>().unwrap_or_default();
            if focus_str == "not-found" {
                log(&format!("Input {} not found!", i));
                continue;
            }

            // Small delay for focus
            tokio::time::sleep(tokio::time::Duration::from_millis(50)).await;

            // Type the value using native keyboard input
            // First clear with backspace/delete
            page.find_element(input_selector)
                .await
                .ok(); // Ignore if not found, we already focused via JS

            // Use keyboard to type - this triggers real browser events
            use chromiumoxide::cdp::browser_protocol::input::{DispatchKeyEventParams, DispatchKeyEventType};

            // Clear existing content with Ctrl+A then type new value
            // For now, just type the value (the select() should have selected existing text)
            for c in val.chars() {
                let key_params = DispatchKeyEventParams::builder()
                    .r#type(DispatchKeyEventType::Char)
                    .text(c.to_string())
                    .build()
                    .unwrap();
                let _ = page.execute(key_params).await;
                tokio::time::sleep(tokio::time::Duration::from_millis(10)).await;
            }

            // Tab to next field (commits the value)
            let tab_params = DispatchKeyEventParams::builder()
                .r#type(DispatchKeyEventType::KeyDown)
                .key("Tab".to_string())
                .code("Tab".to_string())
                .build()
                .unwrap();
            let _ = page.execute(tab_params).await;

            let tab_up = DispatchKeyEventParams::builder()
                .r#type(DispatchKeyEventType::KeyUp)
                .key("Tab".to_string())
                .code("Tab".to_string())
                .build()
                .unwrap();
            let _ = page.execute(tab_up).await;

            tokio::time::sleep(tokio::time::Duration::from_millis(50)).await;
        }

        log("All values typed");

        // Verify values are actually set before saving
        let verify_js = r#"
            (() => {
                const inputs = document.querySelectorAll('input.ant-input-number-input');
                const vals = [...inputs].slice(0, 8).map(i => i.value);
                return JSON.stringify({ values: vals });
            })()
        "#;
        let verify_result = page.evaluate(verify_js).await?;
        let verify_str = verify_result.into_value::<String>().unwrap_or_default();
        log(&format!("Verify before save: {}", verify_str));

        // Click Save button with NATIVE click (JS click doesn't work for Ant Design)
        log("Looking for save button...");
        let save_selectors = [
            "button.his-btn-primary",
            "button.ant-btn-primary",
            "button[type='submit']",
        ];

        let mut clicked = false;
        for selector in save_selectors {
            if let Ok(btn) = page.find_element(selector).await {
                log(&format!("Found save button: {}", selector));
                btn.click().await?;
                clicked = true;
                break;
            }
        }

        if !clicked {
            log("ERROR: Save button not found!");
            return Err(anyhow!("Save button not found"));
        }

        log("Save clicked, waiting for response...");
        tokio::time::sleep(tokio::time::Duration::from_secs(2)).await;

        // Check for any error messages after save
        let after_save = page.evaluate(r#"
            JSON.stringify({
                url: window.location.href,
                error: document.querySelector('.ant-message-error, .ant-notification-error, .ant-form-item-explain-error')?.textContent || '',
                success: document.querySelector('.ant-message-success, .ant-notification-success')?.textContent || '',
                formStillVisible: !!document.querySelector('.ant-form')
            })
        "#).await?;
        let save_state = after_save.into_value::<String>().unwrap_or_default();
        log(&format!("After save state: {}", save_state));

        // Parse and check for errors
        if let Ok(state) = serde_json::from_str::<serde_json::Value>(&save_state) {
            let error = state["error"].as_str().unwrap_or("");
            if !error.is_empty() {
                log(&format!("ERROR from EMR: {}", error));
                return Err(anyhow!("EMR error: {}", error));
            }
        }

        log(&format!("Done for case_id={}", case_id));
        Ok(())
    }
}

/// Generate today's vitals based on yesterday's values
pub fn generate_vitals(yesterday: Option<&Vitals>) -> (Vitals, bool, Option<String>) {
    use rand::Rng;
    let mut rng = rand::thread_rng();

    // Default normal values
    let default = Vitals::new_for_today();
    let base = yesterday.unwrap_or(&default);

    // Check if yesterday's values are abnormal (needs manual review)
    let mut needs_review = false;
    let mut review_reason = None;

    if base.temp_morning > 38.0 || base.temp_evening > 38.0 {
        needs_review = true;
        review_reason = Some("Fever > 38°C".to_string());
    } else if base.bp_systolic_morning > 160 || base.bp_systolic_evening > 160 {
        needs_review = true;
        review_reason = Some("High BP > 160".to_string());
    } else if base.bp_systolic_morning < 90 || base.bp_systolic_evening < 90 {
        needs_review = true;
        review_reason = Some("Low BP < 90".to_string());
    } else if base.pulse_morning > 100 || base.pulse_evening > 100 {
        needs_review = true;
        review_reason = Some("Tachycardia > 100".to_string());
    } else if base.pulse_morning < 50 || base.pulse_evening < 50 {
        needs_review = true;
        review_reason = Some("Bradycardia < 50".to_string());
    }

    // Generate helper functions (inline to avoid closure borrow issues)
    fn gen_temp(rng: &mut impl Rng, prev: f32) -> f32 {
        let variance: f32 = rng.gen_range(-0.1..0.1);
        if prev > 37.0 {
            // Fever: trend down
            (prev - 0.2 + variance).max(36.4)
        } else if prev < 36.4 {
            // Low: trend up
            (prev + 0.1 + variance).min(36.8)
        } else {
            // Normal range: slight variance
            (prev + variance).clamp(36.4, 36.8)
        }
    }

    fn gen_bp_sys(rng: &mut impl Rng, prev: i32) -> i32 {
        let variance: i32 = rng.gen_range(-5..5);
        if prev > 140 {
            (prev - 5 + variance).clamp(110, 140)
        } else if prev < 100 {
            (prev + 5 + variance).clamp(100, 130)
        } else {
            (prev + variance).clamp(100, 140)
        }
    }

    fn gen_bp_dia(rng: &mut impl Rng, prev: i32) -> i32 {
        let variance: i32 = rng.gen_range(-3..3);
        if prev > 90 {
            (prev - 3 + variance).clamp(60, 90)
        } else if prev < 60 {
            (prev + 3 + variance).clamp(60, 85)
        } else {
            (prev + variance).clamp(60, 90)
        }
    }

    fn gen_pulse(rng: &mut impl Rng, prev: i32) -> i32 {
        let variance: i32 = rng.gen_range(-3..3);
        if prev > 85 {
            (prev - 3 + variance).clamp(60, 90)
        } else if prev < 65 {
            (prev + 3 + variance).clamp(65, 80)
        } else {
            (prev + variance).clamp(60, 90)
        }
    }

    let vitals = Vitals {
        date: Some(Local::now().date_naive()),
        temp_morning: gen_temp(&mut rng, base.temp_morning),
        temp_evening: gen_temp(&mut rng, base.temp_evening),
        bp_systolic_morning: gen_bp_sys(&mut rng, base.bp_systolic_morning),
        bp_diastolic_morning: gen_bp_dia(&mut rng, base.bp_diastolic_morning),
        bp_systolic_evening: gen_bp_sys(&mut rng, base.bp_systolic_evening),
        bp_diastolic_evening: gen_bp_dia(&mut rng, base.bp_diastolic_evening),
        pulse_morning: gen_pulse(&mut rng, base.pulse_morning),
        pulse_evening: gen_pulse(&mut rng, base.pulse_evening),
    };

    (vitals, needs_review, review_reason)
}
