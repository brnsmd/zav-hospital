# RUST SCRAPER MIGRATION - THE FINAL HUNT 🪓

**Created:** 2026-01-27
**Status:** PLANNED
**Tribe:** Grug (User) + Clug (Claude)

---

## OVERVIEW

Replace the Python Playwright scraper with a pure Rust implementation using `chromiumoxide`.
This will make Boss-TUI a TRUE all-in-one binary (minus Chrome itself).

---

## CURRENT STATE (Python)

**File:** `cyberintern-boss/src/scraper.py` (845 lines)

### What It Does:
1. **Login to EMR** - Form submission with username/password
2. **Navigate to patient list** - `/case/hospitalized/hospitalized/`
3. **Extract data from tables** - JavaScript execution in browser
4. **Handle pagination** - Detect "next page" links
5. **Fetch patient details** - Navigate to `/case/{id}/#/`
6. **Extract from detail page** - Wait for JS rendering, click tabs
7. **Extract diagnosis** - Click "Діагноз" tab, parse content

### Why It Needs Browser:
- EMR uses JavaScript rendering (line 399: "WAIT FOR KEY ELEMENTS TO RENDER")
- Login with cookies/sessions
- Tabs are JavaScript-driven (can't just request HTML)
- Dynamic content loading

---

## RUST SOLUTION

### Library: `chromiumoxide`
- Pure Rust Chrome DevTools Protocol client
- Same capabilities as Playwright
- Async/await with tokio
- No Python, no Node.js

### Cargo.toml Addition:
```toml
[dependencies]
chromiumoxide = "0.7"
```

---

## IMPLEMENTATION PLAN

### Phase 1: Core Scraper Module (src/scraper/mod.rs)

```rust
pub mod browser;
pub mod login;
pub mod patients;
pub mod enrichment;

use anyhow::Result;
use chromiumoxide::Browser;

pub struct EMRScraper {
    browser: Browser,
    authenticated: bool,
}

impl EMRScraper {
    pub async fn new(headless: bool) -> Result<Self>;
    pub async fn login(&mut self, email: &str, password: &str, role_id: &str) -> Result<()>;
    pub async fn fetch_all_hospitalized(&self, max_pages: u32) -> Result<Vec<Patient>>;
    pub async fn fetch_patient_details(&self, case_id: &str) -> Result<PatientDetails>;
    pub async fn enrich_patients_batch(&self, patients: &mut [Patient], max: u32) -> Result<EnrichmentResult>;
    pub async fn close(self) -> Result<()>;
}
```

### Phase 2: Browser Management (src/scraper/browser.rs)

```rust
use chromiumoxide::{Browser, BrowserConfig};

pub async fn launch_browser(headless: bool) -> Result<Browser> {
    let config = BrowserConfig::builder()
        .with_head() // or headless
        .build()?;

    let (browser, mut handler) = Browser::launch(config).await?;

    // Spawn handler in background
    tokio::spawn(async move {
        while let Some(h) = handler.next().await {
            if h.is_err() { break; }
        }
    });

    Ok(browser)
}
```

### Phase 3: Login Flow (src/scraper/login.rs)

```rust
pub async fn login(page: &Page, email: &str, password: &str, role_id: &str) -> Result<()> {
    // Navigate to login
    page.goto("https://doc.hospital.mia.software/login/").await?;
    page.wait_for_navigation().await?;

    // Fill form
    page.find_element("input[name='username']").await?.type_str(email).await?;
    page.find_element("input[name='password']").await?.type_str(password).await?;
    page.find_element("button[type='submit']").await?.click().await?;

    // Wait for redirect
    page.wait_for_navigation().await?;

    // Select role
    page.goto(&format!("https://doc.hospital.mia.software/role-choose/{role_id}/?next=")).await?;
    page.wait_for_navigation().await?;

    Ok(())
}
```

### Phase 4: Patient List Extraction (src/scraper/patients.rs)

```rust
pub async fn extract_patients_from_page(page: &Page) -> Result<Vec<Patient>> {
    // Wait for table
    page.wait_for_selector("table").await?;

    // Execute JavaScript to extract data
    let result: Vec<Patient> = page.evaluate(r#"
        () => {
            const patients = [];
            const rows = document.querySelectorAll('table tbody tr');
            // ... same JS as Python
            return patients;
        }
    "#).await?;

    Ok(result)
}

pub async fn has_next_page(page: &Page) -> Result<bool> {
    let result: bool = page.evaluate(r#"
        () => {
            // ... same JS as Python
        }
    "#).await?;

    Ok(result)
}
```

### Phase 5: Detail Page Extraction (src/scraper/enrichment.rs)

```rust
pub async fn fetch_patient_details(page: &Page, case_id: &str) -> Result<PatientDetails> {
    // Navigate to detail page
    page.goto(&format!("https://doc.hospital.mia.software/case/{case_id}/#/")).await?;

    // Wait for JS to render
    page.wait_for_selector(".color-label").await?;
    tokio::time::sleep(Duration::from_secs(3)).await;

    // Extract fields
    let data: PatientDetails = page.evaluate(r#"
        () => {
            // ... same field extraction JS as Python
        }
    "#).await?;

    Ok(data)
}

pub async fn fetch_diagnosis_from_tab(page: &Page, case_id: &str) -> Result<String> {
    // Navigate
    page.goto(&format!("https://doc.hospital.mia.software/case/{case_id}/#/")).await?;

    // Click Diagnosis tab
    page.evaluate(r#"
        () => {
            const tabs = document.querySelectorAll('[role="tab"]');
            for (const tab of tabs) {
                if (tab.textContent.includes('Діагноз')) {
                    tab.click();
                    return true;
                }
            }
            return false;
        }
    "#).await?;

    // Wait for content
    tokio::time::sleep(Duration::from_secs(2)).await;

    // Extract diagnosis
    let diagnosis: String = page.evaluate(r#"
        () => {
            // ... same extraction JS as Python
        }
    "#).await?;

    Ok(diagnosis)
}
```

---

## INTEGRATION WITH BOSS-TUI

### Update routes.rs sync endpoints:

```rust
// POST /sync
async fn start_sync(state: ...) {
    // Instead of calling Python subprocess:
    let mut scraper = EMRScraper::new(headless).await?;
    scraper.login(&email, &password, &role_id).await?;
    let patients = scraper.fetch_all_hospitalized(50).await?;

    // Save to database
    state.db.upsert_patients_batch(&patients)?;

    scraper.close().await?;
}
```

---

## BENEFITS

| Before (Python) | After (Rust) |
|-----------------|--------------|
| 2 processes (Rust TUI + Python scraper) | 1 process |
| ~50MB (Python + Playwright) | ~8MB (Rust binary) |
| Subprocess communication | Direct function calls |
| Python dependency | Pure Rust |
| pip install playwright | cargo build |

---

## MIGRATION STEPS

1. **Add chromiumoxide to Cargo.toml**
2. **Create src/scraper/ module structure**
3. **Implement browser launch** (Phase 2)
4. **Implement login flow** (Phase 3)
5. **Implement patient list extraction** (Phase 4)
6. **Implement detail page extraction** (Phase 5)
7. **Update routes.rs to use Rust scraper**
8. **Remove Python subprocess calls**
9. **Test with real EMR**
10. **Delete cyberintern-boss Python code** (optional, keep as backup)

---

## NOTES

- Chrome/Chromium still required on system
- JavaScript extraction code can be copied from Python (same logic)
- EMR credentials still from environment variables
- Same rate limiting (1s between patient details)

---

## PARALLEL RUST MIGRATION

**Note from Grug:** Another Claude is currently migrating CyberIntern (the 027/о enrichment API) to Rust as well. Coordinate to avoid conflicts.

---

## READY FOR NEXT HUNT! 🪓
