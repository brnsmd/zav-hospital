//! EMR browser client
//!
//! Headless Chrome automation for EMR access

use anyhow::{anyhow, Result};
use chromiumoxide::{Browser, BrowserConfig, Page};
use futures::StreamExt;
use std::sync::Arc;
use tokio::sync::Mutex;

const EMR_BASE_URL: &str = "https://doc.hospital.mia.software";

/// Find Chrome/Chromium executable
fn find_chrome() -> Option<String> {
    #[cfg(target_os = "windows")]
    let paths: Vec<std::path::PathBuf> = {
        let mut p = Vec::new();
        // Windows Chrome locations
        if let Ok(pf) = std::env::var("ProgramFiles") {
            p.push(std::path::PathBuf::from(&pf).join("Google/Chrome/Application/chrome.exe"));
        }
        if let Ok(pf86) = std::env::var("ProgramFiles(x86)") {
            p.push(std::path::PathBuf::from(&pf86).join("Google/Chrome/Application/chrome.exe"));
        }
        if let Ok(local) = std::env::var("LocalAppData") {
            p.push(std::path::PathBuf::from(&local).join("Google/Chrome/Application/chrome.exe"));
        }
        // Edge as fallback (Chromium-based)
        if let Ok(pf) = std::env::var("ProgramFiles") {
            p.push(std::path::PathBuf::from(&pf).join("Microsoft/Edge/Application/msedge.exe"));
        }
        if let Ok(pf86) = std::env::var("ProgramFiles(x86)") {
            p.push(std::path::PathBuf::from(&pf86).join("Microsoft/Edge/Application/msedge.exe"));
        }
        p
    };

    #[cfg(not(target_os = "windows"))]
    let paths: Vec<std::path::PathBuf> = vec![
        // Playwright-installed Chrome
        dirs::home_dir().map(|h| h.join(".local/share/playwright-browsers/chrome-linux/chrome")).unwrap_or_default(),
        // User local bin wrapper
        dirs::home_dir().map(|h| h.join(".local/bin/chrome")).unwrap_or_default(),
        // Flatpak Chrome
        "/var/lib/flatpak/exports/bin/com.google.Chrome".into(),
        // System Chrome/Chromium
        "/usr/bin/chromium".into(),
        "/usr/bin/chromium-browser".into(),
        "/usr/bin/google-chrome".into(),
        "/usr/bin/google-chrome-stable".into(),
        // Toolbox Chrome (via wrapper)
        "/opt/google/chrome/chrome".into(),
    ];

    for path in paths {
        if path.exists() {
            return Some(path.to_string_lossy().to_string());
        }
    }
    None
}

/// EMR client wrapping headless browser
pub struct EmrClient {
    #[allow(dead_code)]
    browser: Browser,
    page: Arc<Mutex<Page>>,
    logged_in: bool,
}

impl EmrClient {
    /// Create new EMR client with headless browser
    pub async fn new() -> Result<Self> {
        // Find Chrome executable
        let chrome_path = find_chrome()
            .ok_or_else(|| anyhow!("Chrome/Chromium not found. Install via: playwright install chromium"))?;

        let config = BrowserConfig::builder()
            .chrome_executable(chrome_path)
            // Add flags for better compatibility
            .arg("--no-sandbox")
            .arg("--disable-dev-shm-usage")
            .arg("--disable-gpu")
            .build()
            .map_err(|e| anyhow!("Browser config error: {}", e))?;

        let (browser, mut handler) = Browser::launch(config).await?;

        // Spawn browser event handler
        tokio::spawn(async move {
            while let Some(_) = handler.next().await {}
        });

        let page = browser.new_page("about:blank").await?;

        Ok(Self {
            browser,
            page: Arc::new(Mutex::new(page)),
            logged_in: false,
        })
    }

    /// Login to EMR
    pub async fn login(&mut self, email: &str, password: &str) -> Result<()> {
        let page = self.page.lock().await;

        // Navigate to login page
        let login_url = format!("{}/login/?next=/", EMR_BASE_URL);
        page.goto(&login_url).await?;

        // Wait for page to load
        tokio::time::sleep(tokio::time::Duration::from_secs(3)).await;

        // Check current URL - if redirected away from login, we're already authenticated
        let current_url = page.url().await?.unwrap_or_default();

        if !current_url.contains("/login") {
            // Already logged in from previous session cookies
            self.logged_in = true;
            return Ok(());
        }

        // Find and fill email/username field
        let username_field = page.find_element("#id_username").await?;
        username_field.click().await?;
        username_field.type_str(email).await?;

        // Find and fill password field
        page.find_element("#id_password")
            .await?
            .click()
            .await?
            .type_str(password)
            .await?;

        // Click sign in button
        page.find_element("button.btn-login-enter")
            .await?
            .click()
            .await?;

        // Wait for login to complete
        tokio::time::sleep(tokio::time::Duration::from_secs(5)).await;

        // Check if login succeeded
        let current_url = page.url().await?.unwrap_or_default();
        if current_url.contains("/login") {
            return Err(anyhow!("Login failed - still on login page. Check credentials."));
        }

        self.logged_in = true;
        Ok(())
    }

    /// Check if logged in
    pub fn is_logged_in(&self) -> bool {
        self.logged_in
    }

    /// Get the current page for direct manipulation
    pub fn page(&self) -> Arc<Mutex<Page>> {
        self.page.clone()
    }

    /// Navigate to a URL
    pub async fn goto(&self, url: &str) -> Result<()> {
        let page = self.page.lock().await;
        let full_url = if url.starts_with("http") {
            url.to_string()
        } else {
            format!("{}{}", EMR_BASE_URL, url)
        };
        page.goto(&full_url).await?;
        tokio::time::sleep(tokio::time::Duration::from_secs(2)).await;
        Ok(())
    }

    /// Get current page URL
    pub async fn current_url(&self) -> Result<String> {
        let page = self.page.lock().await;
        Ok(page.url().await?.unwrap_or_default())
    }
}
