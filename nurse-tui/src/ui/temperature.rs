//! Temperature sheet review screen
//!
//! Shows auto-generated vitals for nurse confirmation

use ratatui::{
    prelude::*,
    style::Modifier,
    widgets::{Block, Borders, BorderType, Cell, Paragraph, Row, Table, TableState},
};

use crate::app::App;

/// Render temperature review screen
pub fn render(frame: &mut Frame, app: &App) {
    let area = frame.area();

    // Layout: header, table, footer
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Length(3),  // Header
            Constraint::Min(10),    // Table
            Constraint::Length(3),  // Legend
            Constraint::Length(3),  // Footer
        ])
        .split(area);

    render_header(frame, chunks[0]);
    render_table(frame, chunks[1], app);
    render_legend(frame, chunks[2]);
    render_footer(frame, chunks[3], app);
}

fn render_header(frame: &mut Frame, area: Rect) {
    let header = Paragraph::new("  🌡️ TEMPERATURE SHEET │ Auto-generated from trends")
        .style(Style::default().fg(Color::Yellow).bold())
        .block(
            Block::default()
                .borders(Borders::ALL)
                .border_type(BorderType::Double)
                .style(Style::default().fg(Color::Yellow)),
        );

    frame.render_widget(header, area);
}

fn render_table(frame: &mut Frame, area: Rect, app: &App) {
    let records = match &app.temperature_data {
        Some(data) => data,
        None => {
            // Loading or no data
            let msg = if app.is_loading {
                "Loading patients from EMR..."
            } else {
                "No data. Press [L] to login and [R] to refresh."
            };
            let paragraph = Paragraph::new(format!("\n\n    {}", msg))
                .style(Style::default().fg(Color::DarkGray))
                .block(
                    Block::default()
                        .title(" Patients ")
                        .borders(Borders::ALL)
                        .border_type(BorderType::Rounded),
                );
            frame.render_widget(paragraph, area);
            return;
        }
    };

    // Table header - Boss TUI style with cyan bold
    let header_cells = [
        Cell::from("#").style(Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD)),
        Cell::from("Patient").style(Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD)),
        Cell::from("Ward").style(Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD)),
        Cell::from("Bed").style(Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD)),
        Cell::from("Days").style(Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD)),
        Cell::from("T°M").style(Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD)),
        Cell::from("T°E").style(Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD)),
        Cell::from("BP M").style(Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD)),
        Cell::from("BP E").style(Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD)),
        Cell::from("✓").style(Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD)),
    ];
    let header = Row::new(header_cells).height(1);

    // Table rows - Boss TUI style with alternating colors and indicators
    let rows: Vec<Row> = records
        .iter()
        .enumerate()
        .map(|(i, rec)| {
            let needs_review = rec.needs_manual_review;
            let is_long_stay = rec.patient.disease_day > 60;

            // Days style - color code like Boss TUI
            let days_style = match rec.patient.disease_day {
                d if d > 60 => Style::default().fg(Color::Red).add_modifier(Modifier::BOLD),
                d if d > 30 => Style::default().fg(Color::Yellow),
                _ => Style::default(),
            };

            // Row background style - Boss TUI pattern
            let row_style = if needs_review {
                // Needs review: red tint
                Style::default().bg(Color::Rgb(60, 20, 20))
            } else if is_long_stay {
                // Long stay: yellow tint
                Style::default().bg(Color::Rgb(60, 50, 20))
            } else if i % 2 == 1 {
                // Alternating row: subtle gray
                Style::default().bg(Color::Rgb(30, 30, 35))
            } else {
                Style::default()
            };

            // Row indicator (left border effect)
            let (row_indicator, indicator_style) = if needs_review {
                ("▌", Style::default().fg(Color::Red))
            } else if is_long_stay {
                ("▌", Style::default().fg(Color::Yellow))
            } else {
                (" ", Style::default().fg(Color::DarkGray))
            };

            // Checkbox
            let checkbox = if rec.selected { "☑" } else { "☐" };
            let checkbox_style = if rec.selected {
                Style::default().fg(Color::Green)
            } else {
                Style::default().fg(Color::DarkGray)
            };

            // Patient name with warning if needed
            let name = if needs_review {
                format!("⚠ {}", truncate(&rec.patient.name, 22))
            } else {
                truncate(&rec.patient.name, 24)
            };

            let cells = vec![
                Cell::from(format!("{}{}", row_indicator, i + 1)).style(indicator_style),
                Cell::from(name),
                Cell::from(rec.patient.ward.clone()),
                Cell::from(rec.patient.bed.clone()),
                Cell::from(format!("{}", rec.patient.disease_day)).style(days_style),
                Cell::from(format!("{:.1}", rec.vitals.temp_morning)),
                Cell::from(format!("{:.1}", rec.vitals.temp_evening)),
                Cell::from(format!("{}/{}", rec.vitals.bp_systolic_morning, rec.vitals.bp_diastolic_morning)),
                Cell::from(format!("{}/{}", rec.vitals.bp_systolic_evening, rec.vitals.bp_diastolic_evening)),
                Cell::from(checkbox).style(checkbox_style),
            ];

            Row::new(cells).height(1).style(row_style)
        })
        .collect();

    // Column widths - adjusted for new layout
    let widths = [
        Constraint::Length(4),   // # with indicator
        Constraint::Min(20),     // Patient
        Constraint::Length(6),   // Ward
        Constraint::Length(5),   // Bed
        Constraint::Length(5),   // Days
        Constraint::Length(5),   // T°M
        Constraint::Length(5),   // T°E
        Constraint::Length(8),   // BP M
        Constraint::Length(8),   // BP E
        Constraint::Length(3),   // ✓
    ];

    let table = Table::new(rows, widths)
        .header(header)
        .block(
            Block::default()
                .title(format!(
                    " 🌡️ Patients ({} selected / {} total) ",
                    records.iter().filter(|r| r.selected).count(),
                    records.len()
                ))
                .borders(Borders::ALL)
                .border_type(BorderType::Rounded)
                .border_style(Style::default().fg(Color::Blue)),
        )
        .row_highlight_style(Style::default().bg(Color::DarkGray).add_modifier(Modifier::BOLD))
        .highlight_symbol(">> ");

    // Render with state for highlighting
    let mut state = TableState::default();
    state.select(Some(app.temperature_selected));
    frame.render_stateful_widget(table, area, &mut state);
}

fn render_legend(frame: &mut Frame, area: Rect) {
    let legend = Paragraph::new(
        "  🔴 ⚠ Abnormal vitals  │  🟡 >60 days stay  │  ☑ Selected for submission"
    )
    .style(Style::default().fg(Color::DarkGray))
    .block(
        Block::default()
            .borders(Borders::LEFT | Borders::RIGHT)
            .style(Style::default().fg(Color::DarkGray)),
    );

    frame.render_widget(legend, area);
}

fn render_footer(frame: &mut Frame, area: Rect, app: &App) {
    let selected_count = app.temperature_data
        .as_ref()
        .map(|d| d.iter().filter(|r| r.selected).count())
        .unwrap_or(0);

    let footer_text = if selected_count > 0 {
        format!(
            "  [Space] Toggle  [A] Select All  [Enter] Submit {}  [Esc] Back",
            selected_count
        )
    } else {
        "  [Space] Toggle  [A] Select All  [Esc] Back".to_string()
    };

    let footer = Paragraph::new(footer_text)
        .style(Style::default().fg(Color::Cyan))
        .block(
            Block::default()
                .borders(Borders::ALL)
                .border_type(BorderType::Double)
                .style(Style::default().fg(Color::Cyan)),
        );

    frame.render_widget(footer, area);
}

/// Truncate string to max length
fn truncate(s: &str, max: usize) -> String {
    if s.chars().count() <= max {
        s.to_string()
    } else {
        format!("{}…", s.chars().take(max - 1).collect::<String>())
    }
}
