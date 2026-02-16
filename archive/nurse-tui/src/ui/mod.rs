//! UI rendering - Temperature only

mod temperature;

use ratatui::prelude::*;
use ratatui::widgets::{Block, Borders, Clear, Gauge, Paragraph};

use crate::app::{App, AppMode, ToastType};

pub fn render(frame: &mut Frame, app: &App) {
    match app.mode {
        AppMode::Temperature => temperature::render(frame, app),
        AppMode::NurseSelect => render_nurse_select(frame, app),
        AppMode::AddNurse => render_add_nurse(frame, app, false),
        AppMode::AddNursePass => render_add_nurse(frame, app, true),
        AppMode::Confirming => render_confirmation(frame, app),
        AppMode::Submitting => render_submitting(frame, app),
    }

    // Render loading overlay if loading
    if app.is_loading {
        render_loading_overlay(frame, app);
    }

    // Render toast notification on top
    if let Some(ref toast) = app.toast {
        if toast.is_visible() {
            render_toast(frame, toast);
        }
    }
}

fn render_loading_overlay(frame: &mut Frame, app: &App) {
    let area = frame.area();
    let overlay_area = centered_rect(50, 5, area);
    frame.render_widget(Clear, overlay_area);

    let msg = app.loading_message.as_deref().unwrap_or("Loading...");
    let spinner = app.spinner();
    let text = format!("  {} {}", spinner, msg);

    let block = Block::default()
        .borders(Borders::ALL)
        .border_type(ratatui::widgets::BorderType::Rounded)
        .style(Style::default().fg(Color::Cyan).bg(Color::Black));

    let loading = Paragraph::new(format!("\n{}", text))
        .block(block)
        .style(Style::default().fg(Color::Cyan))
        .alignment(Alignment::Left);

    frame.render_widget(loading, overlay_area);
}

fn render_toast(frame: &mut Frame, toast: &crate::app::Toast) {
    let area = frame.area();

    let toast_width = (toast.message.chars().count() + 6).min(60) as u16;
    let toast_height = 3;
    let x = area.x + (area.width.saturating_sub(toast_width)) / 2;
    let y = area.y + area.height.saturating_sub(toast_height + 1);
    let toast_area = Rect::new(x, y, toast_width, toast_height);

    frame.render_widget(Clear, toast_area);

    let (icon, color, border_color) = match toast.toast_type {
        ToastType::Success => ("✓", Color::Green, Color::Green),
        ToastType::Error => ("✗", Color::Red, Color::Red),
    };

    let text = format!(" {} {} ", icon, toast.message);

    let block = Block::default()
        .borders(Borders::ALL)
        .border_type(ratatui::widgets::BorderType::Rounded)
        .style(Style::default().fg(border_color).bg(Color::Black));

    let paragraph = Paragraph::new(text)
        .block(block)
        .style(Style::default().fg(color))
        .alignment(Alignment::Center);

    frame.render_widget(paragraph, toast_area);
}

fn render_nurse_select(frame: &mut Frame, app: &App) {
    use ratatui::widgets::{List, ListItem};

    let area = frame.area();

    let bg = Block::default().style(Style::default().bg(Color::Black));
    frame.render_widget(bg, area);

    let dialog_width = 50;
    let dialog_height = (app.nurses.len() as u16 + 8).min(20);
    let dialog_area = centered_rect(dialog_width, dialog_height, area);

    frame.render_widget(Clear, dialog_area);

    let block = Block::default()
        .title(" 👩‍⚕️ SELECT NURSE ")
        .borders(Borders::ALL)
        .border_type(ratatui::widgets::BorderType::Double)
        .style(Style::default().fg(Color::Cyan));

    let items: Vec<ListItem> = app.nurses
        .iter()
        .enumerate()
        .map(|(i, nurse)| {
            let key = if i == 9 { "0".to_string() } else { (i + 1).to_string() };
            let prefix = if i == app.selected_nurse { "▶ " } else { "  " };
            let style = if i == app.selected_nurse {
                Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD)
            } else {
                Style::default().fg(Color::White)
            };
            ListItem::new(format!("{}[{}] {} ({})", prefix, key, nurse.name, nurse.email))
                .style(style)
        })
        .collect();

    let inner = Layout::default()
        .direction(Direction::Vertical)
        .margin(1)
        .constraints([
            Constraint::Min(1),
            Constraint::Length(3),
        ])
        .split(dialog_area);

    frame.render_widget(block, dialog_area);

    if items.is_empty() {
        let empty = Paragraph::new("  No nurses saved. Press [+] to add.")
            .style(Style::default().fg(Color::DarkGray));
        frame.render_widget(empty, inner[0]);
    } else {
        let list = List::new(items);
        frame.render_widget(list, inner[0]);
    }

    let help = if app.nurses.len() < 10 {
        "[1-0] Login  [+] Add  [-] Remove  [Esc] Back"
    } else {
        "[1-0] Login  [-] Remove  [Esc] Back (max 10)"
    };
    let help_text = Paragraph::new(help)
        .style(Style::default().fg(Color::DarkGray))
        .alignment(Alignment::Center);
    frame.render_widget(help_text, inner[1]);
}

fn render_add_nurse(frame: &mut Frame, app: &App, is_password: bool) {
    let area = frame.area();

    let bg = Block::default().style(Style::default().bg(Color::Black));
    frame.render_widget(bg, area);

    let dialog_width = 50;
    let dialog_height = 8;
    let dialog_area = centered_rect(dialog_width, dialog_height, area);

    frame.render_widget(Clear, dialog_area);

    let title = if is_password { " 🔑 ENTER PASSWORD " } else { " 📧 ENTER EMAIL " };
    let block = Block::default()
        .title(title)
        .borders(Borders::ALL)
        .border_type(ratatui::widgets::BorderType::Double)
        .style(Style::default().fg(Color::Magenta));

    let inner = Layout::default()
        .direction(Direction::Vertical)
        .margin(1)
        .constraints([
            Constraint::Length(1),
            Constraint::Length(2),
            Constraint::Length(1),
        ])
        .split(dialog_area);

    frame.render_widget(block, dialog_area);

    let label = if is_password { "Password:" } else { "Email:" };
    let label_text = Paragraph::new(format!("  {}", label))
        .style(Style::default().fg(Color::White));
    frame.render_widget(label_text, inner[0]);

    let display = if is_password {
        "*".repeat(app.input_buffer.len())
    } else {
        app.input_buffer.clone()
    };
    let input_text = Paragraph::new(format!("  {}_", display))
        .style(Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD));
    frame.render_widget(input_text, inner[1]);

    let help = Paragraph::new("  [Enter] Confirm  [Esc] Cancel")
        .style(Style::default().fg(Color::DarkGray));
    frame.render_widget(help, inner[2]);
}

fn render_confirmation(frame: &mut Frame, app: &App) {
    let area = frame.area();

    let bg = Block::default().style(Style::default().bg(Color::Black));
    frame.render_widget(bg, area);

    let dialog_width = 44;
    let dialog_height = 7;
    let dialog_area = centered_rect(dialog_width, dialog_height, area);

    frame.render_widget(Clear, dialog_area);

    let count = app.selected_count();
    let text = format!(
        "\n  Submit {} temperature records?\n\n  [Y] Yes, submit    [N] Cancel",
        count
    );

    let dialog = Paragraph::new(text)
        .style(Style::default().fg(Color::White))
        .block(
            Block::default()
                .title(" ⚠️  CONFIRM SUBMISSION ")
                .borders(Borders::ALL)
                .border_type(ratatui::widgets::BorderType::Double)
                .style(Style::default().fg(Color::Yellow)),
        );

    frame.render_widget(dialog, dialog_area);
}

fn render_submitting(frame: &mut Frame, app: &App) {
    let area = frame.area();

    let bg = Block::default().style(Style::default().bg(Color::Black));
    frame.render_widget(bg, area);

    let dialog_width = 50;
    let dialog_height = 8;
    let dialog_area = centered_rect(dialog_width, dialog_height, area);

    frame.render_widget(Clear, dialog_area);

    let total = app.submit_total;
    let current = app.submit_current;
    let percent = if total > 0 {
        (current as f64 / total as f64 * 100.0) as u16
    } else {
        0
    };

    let inner = Layout::default()
        .direction(Direction::Vertical)
        .margin(1)
        .constraints([
            Constraint::Length(2),
            Constraint::Length(3),
        ])
        .split(dialog_area);

    let block = Block::default()
        .title(" 🚀 SUBMITTING ")
        .borders(Borders::ALL)
        .border_type(ratatui::widgets::BorderType::Double)
        .style(Style::default().fg(Color::Green));

    frame.render_widget(block, dialog_area);

    let status = Paragraph::new(format!("  Submitting {} / {} ...", current + 1, total))
        .style(Style::default().fg(Color::White));
    frame.render_widget(status, inner[0]);

    let gauge = Gauge::default()
        .gauge_style(Style::default().fg(Color::Green))
        .percent(percent)
        .label(format!("{}%", percent));
    frame.render_widget(gauge, inner[1]);
}

fn centered_rect(width: u16, height: u16, area: Rect) -> Rect {
    let x = area.x + (area.width.saturating_sub(width)) / 2;
    let y = area.y + (area.height.saturating_sub(height)) / 2;
    Rect::new(x, y, width.min(area.width), height.min(area.height))
}
