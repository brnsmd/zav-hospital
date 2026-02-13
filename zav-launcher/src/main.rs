//! ZAV Hospital System Launcher
//!
//! Replaces START.bat with a proper Windows EXE.
//! Starts all services (n8n, ngrok, CyberIntern) then launches Boss TUI.
//! On exit, cleans up all child processes.

use std::env;
use std::fs;
use std::io::{self, Write, BufRead, BufReader};
use std::net::TcpStream;
use std::path::{Path, PathBuf};
use std::process::{Command, Child, Stdio};
use std::thread;
use std::time::{Duration, Instant};

/// ANSI color helpers for console output
const GREEN: &str = "\x1b[32m";
const YELLOW: &str = "\x1b[33m";
const RED: &str = "\x1b[31m";
const CYAN: &str = "\x1b[36m";
const BOLD: &str = "\x1b[1m";
const RESET: &str = "\x1b[0m";

fn main() {
    // Enable ANSI colors on Windows
    #[cfg(windows)]
    enable_ansi();

    // Set UTF-8 console codepage
    #[cfg(windows)]
    unsafe {
        extern "system" {
            fn SetConsoleOutputCP(codepage: u32) -> i32;
        }
        SetConsoleOutputCP(65001);
    }

    let launcher_dir = get_launcher_dir();
    println!();
    println!("  {BOLD}{CYAN}===================================={RESET}");
    println!("  {BOLD}{CYAN} ZAV BOSS HOSPITAL SERVER{RESET}");
    println!("  {BOLD}{CYAN}===================================={RESET}");
    println!();

    // Load secrets
    load_secrets(&launcher_dir);

    // Set standard config vars
    set_config_vars();

    // Track child processes for cleanup
    let mut children: Vec<(&str, Child)> = Vec::new();

    // [1/4] Start n8n
    print!("  {YELLOW}[1/4]{RESET} Starting n8n...");
    io::stdout().flush().ok();
    match start_n8n() {
        Some(child) => {
            children.push(("n8n", child));
            println!(" {GREEN}started{RESET}");
            // Wait for n8n to be ready
            print!("        Waiting for n8n health...");
            io::stdout().flush().ok();
            if wait_for_port("127.0.0.1", 5678, Duration::from_secs(20)) {
                println!(" {GREEN}OK{RESET}");
            } else {
                println!(" {YELLOW}still starting (continuing){RESET}");
            }
        }
        None => println!(" {RED}failed to start{RESET}"),
    }

    // [2/4] Start ngrok
    print!("  {YELLOW}[2/4]{RESET} Starting ngrok tunnel...");
    io::stdout().flush().ok();
    match start_ngrok() {
        Some(child) => {
            children.push(("ngrok", child));
            println!(" {GREEN}started{RESET}");
        }
        None => println!(" {YELLOW}skipped (ngrok not found or no auth token){RESET}"),
    }

    // [3/4] Start CyberIntern
    print!("  {YELLOW}[3/4]{RESET} Starting CyberIntern...");
    io::stdout().flush().ok();
    let cyberintern_dir = launcher_dir.parent()
        .map(|p| p.join("cyberintern"))
        .unwrap_or_else(|| PathBuf::from("..\\cyberintern"));
    match start_cyberintern(&cyberintern_dir) {
        Some(child) => {
            children.push(("cyberintern", child));
            println!(" {GREEN}started (port 8082){RESET}");
        }
        None => println!(" {YELLOW}skipped (cyberintern not found){RESET}"),
    }

    // Show config
    println!();
    println!("  {BOLD}Config:{RESET}");
    println!("    BOSS API:     {}", env::var("BOSS_API_URL").unwrap_or_default());
    println!("    N8N:          {}", env::var("N8N_URL").unwrap_or_default());
    println!("    CyberIntern:  {}", env::var("CYBERINTERN_API_URL").unwrap_or_default());
    println!("    Subnet:       {}", env::var("HOSPITAL_SUBNET").unwrap_or_default());
    println!();
    println!("  {BOLD}{CYAN}===================================={RESET}");
    println!("  {BOLD}  DO NOT CLOSE THIS WINDOW!{RESET}");
    println!("  {BOLD}{CYAN}===================================={RESET}");
    println!();

    // [4/4] Start Boss TUI (blocking - runs until user exits)
    println!("  {YELLOW}[4/4]{RESET} Launching Boss TUI...");
    println!();
    let boss_exe = launcher_dir.join("boss-tui.exe");
    if boss_exe.exists() {
        // Write a temp .bat that sets env vars then runs boss-tui.
        // This is needed because wt.exe spawns a new process tree that
        // doesn't inherit our env::set_var() values.
        let env_bat = launcher_dir.join("_env_launch.bat");
        {
            let env_vars = [
                "BOSS_API_URL", "N8N_URL", "CYBERINTERN_API_URL",
                "ZAV_DATABASE_PATH", "HOSPITAL_SUBNET", "HOSPITAL_GATEWAY",
                "BOSS_HEADLESS", "RUST_LOG",
                "AIRTABLE_TOKEN", "AIRTABLE_BASE", "N8N_API_KEY",
                "NGROK_AUTHTOKEN", "SLACK_BOT_TOKEN",
                "EMR_URL", "EMR_EMAIL", "EMR_PASSWORD", "EMR_ROLE_ID",
            ];
            let mut bat = String::from("@echo off\r\n");
            for key in &env_vars {
                if let Ok(val) = env::var(key) {
                    bat.push_str(&format!("set {}={}\r\n", key, val));
                }
            }
            bat.push_str(&format!("cd /d \"{}\"\r\n", launcher_dir.display()));
            bat.push_str("boss-tui.exe\r\n");
            let _ = fs::write(&env_bat, &bat);
        }

        // Try launching in Windows Terminal with custom theme
        let status = Command::new("wt.exe")
            .args(["new-tab", "--title", "ZAV Boss", "cmd.exe", "/c", &env_bat.to_string_lossy()])
            .status();

        match status {
            Ok(s) if s.success() => {
                // Windows Terminal launched — wait for boss-tui to exit
                // WT returns immediately, so we wait for boss-tui process
                println!("  {GREEN}Boss TUI launched in Windows Terminal{RESET}");
                println!("  Waiting for Boss TUI to exit...");
                println!("  (Close the Boss TUI window when done)");
                // Poll until boss-tui.exe is no longer running
                loop {
                    thread::sleep(Duration::from_secs(2));
                    let check = Command::new("tasklist")
                        .args(["/FI", "IMAGENAME eq boss-tui.exe", "/NH"])
                        .stdout(Stdio::piped())
                        .output();
                    match check {
                        Ok(output) => {
                            let out = String::from_utf8_lossy(&output.stdout);
                            if !out.contains("boss-tui.exe") {
                                break;
                            }
                        }
                        Err(_) => break,
                    }
                }
            }
            _ => {
                // Fallback: run directly in this console (env vars inherited automatically)
                println!("  {YELLOW}Windows Terminal not available, running here{RESET}");
                let status = Command::new(&boss_exe)
                    .current_dir(&launcher_dir)
                    .stdin(Stdio::inherit())
                    .stdout(Stdio::inherit())
                    .stderr(Stdio::inherit())
                    .status();
                match status {
                    Ok(s) => {
                        if !s.success() {
                            eprintln!("  {RED}Boss TUI exited with: {}{RESET}", s);
                        }
                    }
                    Err(e) => eprintln!("  {RED}Failed to start Boss TUI: {}{RESET}", e),
                }
            }
        }

        // Cleanup temp bat
        let _ = fs::remove_file(&env_bat);
    } else {
        eprintln!("  {RED}boss-tui.exe not found at: {}{RESET}", boss_exe.display());
        eprintln!("  Press Enter to exit...");
        let _ = io::stdin().read_line(&mut String::new());
    }

    // Cleanup: kill all child processes
    println!();
    println!("  Stopping services...");
    for (name, mut child) in children {
        match child.kill() {
            Ok(_) => println!("    {GREEN}Stopped {}{RESET}", name),
            Err(_) => {
                // Process may have already exited, try taskkill as fallback
                let exe_name = match name {
                    "n8n" => "node.exe",
                    "ngrok" => "ngrok.exe",
                    "cyberintern" => "python.exe",
                    _ => continue,
                };
                let _ = Command::new("taskkill")
                    .args(["/F", "/IM", exe_name])
                    .stdout(Stdio::null())
                    .stderr(Stdio::null())
                    .status();
                println!("    {YELLOW}Force-stopped {}{RESET}", name);
            }
        }
    }
    println!("  {GREEN}All services stopped.{RESET}");
    println!();
    println!("  Press Enter to close...");
    let _ = io::stdin().read_line(&mut String::new());
}

/// Get the directory where the launcher EXE is located
fn get_launcher_dir() -> PathBuf {
    env::current_exe()
        .ok()
        .and_then(|p| p.parent().map(|p| p.to_path_buf()))
        .unwrap_or_else(|| env::current_dir().unwrap_or_else(|_| PathBuf::from(".")))
}

/// Load secrets from secrets.bat by parsing SET commands
fn load_secrets(launcher_dir: &Path) {
    let secrets_path = launcher_dir.join("secrets.bat");
    if !secrets_path.exists() {
        println!("  {RED}[!] WARNING: secrets.bat not found!{RESET}");
        println!("      Create it with AIRTABLE_TOKEN, AIRTABLE_BASE, N8N_API_KEY");
        return;
    }

    if let Ok(file) = fs::File::open(&secrets_path) {
        let reader = BufReader::new(file);
        for line in reader.lines().flatten() {
            let trimmed = line.trim();
            // Parse "set KEY=VALUE" or "SET KEY=VALUE"
            if let Some(rest) = trimmed.strip_prefix("set ").or_else(|| trimmed.strip_prefix("SET ")) {
                if let Some((key, value)) = rest.split_once('=') {
                    let key = key.trim();
                    let value = value.trim();
                    if !key.is_empty() && !key.starts_with("REM") {
                        env::set_var(key, value);
                    }
                }
            }
        }
        println!("  {GREEN}[OK]{RESET} Secrets loaded from secrets.bat");
    }
}

/// Set standard configuration environment variables
fn set_config_vars() {
    env::set_var("BOSS_API_URL", "http://127.0.0.1:8084");
    env::set_var("N8N_URL", "http://127.0.0.1:5678");
    env::set_var("CYBERINTERN_API_URL", "http://127.0.0.1:8082");
    env::set_var("ZAV_DATABASE_PATH", r"C:\ZavBoss\data\zav.db");
    env::set_var("HOSPITAL_SUBNET", "192.168.4.");
    env::set_var("HOSPITAL_GATEWAY", "192.168.4.1");
    env::set_var("BOSS_HEADLESS", "true");

    // Only set RUST_LOG if not already set
    if env::var("RUST_LOG").is_err() {
        env::set_var("RUST_LOG", "boss_tui=debug,chromiumoxide=info");
    }
}

/// Start n8n as a background process
fn start_n8n() -> Option<Child> {
    Command::new("cmd")
        .args(["/C", "n8n", "start"])
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn()
        .ok()
}

/// Start ngrok tunnel as a background process
fn start_ngrok() -> Option<Child> {
    // Check if ngrok auth token is set
    if env::var("NGROK_AUTHTOKEN").unwrap_or_default().is_empty() {
        return None;
    }

    Command::new("ngrok")
        .args([
            "http", "5678",
            "--domain=kristeen-rootlike-unflirtatiously.ngrok-free.dev",
        ])
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn()
        .ok()
}

/// Start CyberIntern Python backend
fn start_cyberintern(cyberintern_dir: &Path) -> Option<Child> {
    if !cyberintern_dir.exists() {
        return None;
    }

    // Check if the API module exists (src/api/main.py)
    let api_main = cyberintern_dir.join("src").join("api").join("main.py");
    if !api_main.exists() {
        // Fallback: check legacy main.py
        if !cyberintern_dir.join("main.py").exists() {
            return None;
        }
    }

    // Set JWT secret so the server doesn't crash on startup
    let mut cmd = Command::new("python");
    cmd.args(["-m", "uvicorn", "src.api.main:app", "--host", "127.0.0.1", "--port", "8082"])
        .current_dir(cyberintern_dir)
        .env("JWT_SECRET_KEY", "zav-hospital-dev-key")
        .stdout(Stdio::null())
        .stderr(Stdio::null());

    cmd.spawn().ok()
}

/// Wait for a TCP port to become available
fn wait_for_port(host: &str, port: u16, timeout: Duration) -> bool {
    let start = Instant::now();
    while start.elapsed() < timeout {
        if TcpStream::connect(format!("{}:{}", host, port)).is_ok() {
            return true;
        }
        thread::sleep(Duration::from_millis(500));
    }
    false
}

/// Enable ANSI escape codes on Windows 10+
#[cfg(windows)]
fn enable_ansi() {
    unsafe {
        extern "system" {
            fn SetConsoleMode(handle: *mut std::ffi::c_void, mode: u32) -> i32;
            fn GetConsoleMode(handle: *mut std::ffi::c_void, mode: *mut u32) -> i32;
            fn GetStdHandle(std_handle: u32) -> *mut std::ffi::c_void;
        }
        let handle = GetStdHandle(0xFFFF_FFF5); // STD_OUTPUT_HANDLE
        let mut mode: u32 = 0;
        GetConsoleMode(handle, &mut mode);
        // ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
        SetConsoleMode(handle, mode | 0x0004);
    }
}
