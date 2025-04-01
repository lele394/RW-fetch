// src/sysinfo_fetchers.rs
use crate::config;
use sysinfo::System;
use users::{get_current_uid, get_user_by_uid};
use std::process::Command; // Needed for shell commands
use std::time::Duration; // Optional: for command timeout

// --- Helper Functions (format_bytes, format_duration_secs) ---
// (Keep these helpers as they were)
fn format_bytes(bytes: u64) -> String {
    const KIB: u64 = 1024;
    const MIB: u64 = KIB * 1024;
    const GIB: u64 = MIB * 1024;

    if bytes >= GIB {
        format!("{:.1} GiB", bytes as f64 / GIB as f64)
    } else if bytes >= MIB {
        format!("{:.1} MiB", bytes as f64 / MIB as f64)
    } else if bytes >= KIB {
        format!("{:.1} KiB", bytes as f64 / KIB as f64)
    } else {
        format!("{} B", bytes)
    }
}

fn format_duration_secs(total_seconds: u64) -> String {
    if total_seconds == 0 {
        return "Just booted".to_string();
    }
    // ... (rest of format_duration_secs remains the same) ...
     let days = total_seconds / (24 * 3600);
    let remaining_seconds = total_seconds % (24 * 3600);
    let hours = remaining_seconds / 3600;
    let remaining_seconds = remaining_seconds % 3600;
    let minutes = remaining_seconds / 60;

    let mut parts = Vec::new();
    if days > 0 {
        parts.push(format!("{} {}", days, if days == 1 { "day" } else { "days" }));
    }
    if hours > 0 {
        parts.push(format!("{} {}", hours, if hours == 1 { "hour" } else { "hours" }));
    }
    if minutes > 0 {
        parts.push(format!("{} {}", minutes, if minutes == 1 { "minute" } else { "minutes" }));
    }

    if parts.is_empty() {
        format!("{} seconds", total_seconds % 60)
    } else {
        parts.join(", ")
    }
}


// --- Helper Function to Execute Shell Commands ---
pub fn fetch_shell_command(command_key: &str) -> String {
    match config::FALLBACK_COMMANDS.get(command_key) {
        Some(command_str) => {
            // Use sh -c to execute the command string properly
            let output_result = Command::new("sh")
                                     .arg("-c")
                                     .arg(command_str)
                                     // Optional: Add a timeout (requires more complex handling, e.g., external crate like wait-timeout or async)
                                     // .timeout(Duration::from_secs(5)) // Example, needs crate
                                     .output(); // Executes and waits

            match output_result {
                Ok(output) => {
                    if output.status.success() {
                        let stdout = String::from_utf8_lossy(&output.stdout).trim().to_string();
                        if stdout.is_empty() {
                            config::format_value("N/A") // Treat empty output as N/A
                        } else {
                            config::format_value(&stdout) // Format successful output
                        }
                    } else {
                        // Command failed, include stderr if available
                        let stderr = String::from_utf8_lossy(&output.stderr);
                        let err_msg = if !stderr.is_empty() {
                             format!("Cmd Err: {}", stderr.trim())
                        } else {
                             format!("Exit {}", output.status.code().map_or_else(|| "?".to_string(), |c| c.to_string()))
                        };
                        config::format_error(&err_msg.chars().take(50).collect::<String>()) // Limit error length
                    }
                }
                Err(e) => {
                    // Failed to even run the command (e.g., 'sh' not found)
                    config::format_error(&format!("Exec Err: {}", e.kind()))
                }
            }
        }
        None => {
            config::format_error(&format!("No cmd for {}", command_key))
        }
    }
}


// --- Fetcher Functions ---
// (Sysinfo-based functions remain mostly the same, ensure they use _s where appropriate)

pub fn get_user_host(_s: &System) -> String {
    let user_name = get_user_by_uid(get_current_uid())
        .map(|u| u.name().to_string_lossy().into_owned())
        .unwrap_or_else(|| "N/A".to_string());
    let host_name = System::host_name().unwrap_or_else(|| "N/A".to_string());
    config::format_value(&format!("{}@{}", user_name, host_name))
}

pub fn get_os(_s: &System) -> String {
    let name = System::name().unwrap_or_else(|| "OS".to_string());
    let version = System::os_version().unwrap_or_default();
    let os_string = if !version.is_empty() {
        format!("{} {}", name, version)
    } else { name };
    config::format_value(&os_string.trim())
}

pub fn get_kernel(_s: &System) -> String {
    config::format_value(&System::kernel_version().unwrap_or_else(|| "N/A".to_string()))
}

pub fn get_uptime(_s: &System) -> String {
    config::format_value(&format_duration_secs(System::uptime()))
}

pub fn get_shell(_s: &System) -> String {
    match std::env::var("SHELL") {
        Ok(shell_path) => {
            let shell_name = std::path::Path::new(&shell_path)
                .file_name()
                .map(|name| name.to_string_lossy().into_owned())
                .unwrap_or(shell_path);
            config::format_value(&shell_name)
        }
        Err(_) => config::format_error("N/A"),
    }
}

pub fn get_terminal(_s: &System) -> String {
    let term_program = std::env::var("TERM_PROGRAM").ok();
    let term = std::env::var("TERM").ok();
    let display_term = match (term_program, term) {
        (Some(prog), _) if !prog.is_empty() => prog.replace(".app", ""),
        (_, Some(t)) if !t.is_empty() => t,
        _ => "N/A".to_string(),
    };
    config::format_value(&display_term)
}

pub fn get_cpu(s: &System) -> String {
    if let Some(cpu) = s.cpus().first() {
        let brand = cpu.brand().trim();
        let freq_mhz = cpu.frequency();
        let core_count = s.cpus().len();
        let mut parts = vec![brand.to_string()];
        if core_count > 0 { parts.push(format!("({} Cores)", core_count)); }
        if freq_mhz > 0 { parts.push(format!("@ {}MHz", freq_mhz)); }
        config::format_value(&parts.into_iter().filter(|p| !p.is_empty()).collect::<Vec<_>>().join(" "))
    } else { config::format_error("N/A") }
}

pub fn get_memory(s: &System) -> String {
    let total = s.total_memory();
    let used = s.used_memory();
    if total > 0 {
        let percent = (used as f64 / total as f64) * 100.0;
        let mem_string = format!("{} / {} ({:.0}%)", format_bytes(used), format_bytes(total), percent);
        config::format_value(&mem_string)
    } else { config::format_error("N/A") }
}

pub fn get_color_palette(_s: &System) -> String {
    let line1: String = (0..8).map(|i| format!("\x1b[4{}m  ", i)).collect();
    let line2: String = (0..8).map(|i| format!("\x1b[10{}m  ", i)).collect();
    // Return value formatted - will be split in main loop
    format!(" {}\x1b[0m\n {}\x1b[0m", line1, line2)
}

// NOTE: No explicit functions needed here for Resolution, WM, Theme etc.
// The main loop will call fetch_shell_command directly based on FetcherType::ShellCommand(key)