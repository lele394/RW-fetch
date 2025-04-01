// src/config.rs
use colored::*;
use lazy_static::lazy_static;
use std::collections::HashMap;
use sysinfo::System; // Keep System needed for function signature type

// --- Paths ---
pub const CACHE_FILE_NAME: &str = "cache.json";

// --- Concurrency ---
pub const MAX_FETCH_THREADS: usize = 12; // Max threads for fetching sysinfo/shell commands

// --- System Info Display Formatting ---
const LABEL_COLOR: Color = Color::Blue;
const VALUE_COLOR: Color = Color::BrightWhite;
const ERROR_COLOR: Color = Color::Red;
const SEPARATOR_COLOR: Color = Color::Blue; // Color for separators like "---" or "Hardware"

pub const SYS_INFO_KV_SEPARATOR: &str = ":";
pub const RESET_COLOR_STR: &str = "\x1b[0m";
pub const SYS_INFO_SEPARATOR_CHAR: char = '-';

// --- Image/Info Layout ---
pub const IMAGE_INFO_SEPARATOR: &str = "  │  ";

// --- Fallback Shell Commands ---
lazy_static! {
    pub static ref FALLBACK_COMMANDS: HashMap<&'static str, &'static str> = {
        let mut m = HashMap::new();
        // Copy commands directly from Python config. Use raw strings r#""# for multiline.
        m.insert("Packages", r#"
            pkgs=''; updated=0
            append_pkg() { local name="$1"; local count="$2"; [ "$count" -gt 0 ] && pkgs="${pkgs}${pkgs:+, }$name ($count)"; updated=1; }
            if command -v dpkg-query >/dev/null; then append_pkg "apt" "$(dpkg-query -W -f='${Status}\n' 2>/dev/null | grep -c '^install ok installed')";
            elif command -v rpm >/dev/null; then append_pkg "rpm" "$(rpm -qa --nosignature --nodigest 2>/dev/null | wc -l)"; fi
            if command -v snap >/dev/null; then count=$(snap list 2>/dev/null | wc -l); [ "$count" -gt 1 ] && count=$((count-1)) || count=0; if [ "$count" -gt 0 ] || snap list >/dev/null 2>&1; then append_pkg "snap" "$count"; fi; fi
            if command -v flatpak >/dev/null; then count=$(flatpak list --app --columns=application 2>/dev/null | wc -l); [ "$count" -gt 1 ] && count=$((count-1)) || count=0; if [ "$count" -gt 0 ] || flatpak list >/dev/null 2>&1; then append_pkg "flatpak" "$count"; fi; fi
            [ "$updated" -eq 0 ] && pkgs="N/A" # Show N/A if no managers found/counted
            printf '%s' "$pkgs"
        "#);
        m.insert("Resolution", r#"
            res=""
            if command -v xrandr >/dev/null; then res=$(xrandr --current 2>/dev/null | awk '/\*/ {print $1; exit}');
            elif command -v swaymsg >/dev/null; then res=$(swaymsg -t get_outputs | jq -r '.[] | select(.active) | .current_mode | "\(.width)x\(.height)"' 2>/dev/null | paste -sd ',' -);
            elif [ "$(uname -s)" = "Darwin" ]; then res=$(system_profiler SPDisplaysDataType 2>/dev/null | awk '/Resolution:/ {print $2 "x" $4; exit}'); fi
            printf "%s" "${res:-N/A}"
        "#);
        m.insert("WM", r#"
            wm=""
            if [ -n "$XDG_CURRENT_DESKTOP" ]; then wm="$XDG_CURRENT_DESKTOP";
            elif [ -n "$DESKTOP_SESSION" ]; then wm="$DESKTOP_SESSION";
            elif command -v wmctrl >/dev/null; then wm=$(wmctrl -m 2>/dev/null | awk '/Name:/ {print $2}'); fi
            # Add more pgrep checks if desired, but keep it concise for fallback
            printf "%s" "${wm:-N/A}"
        "#);
        m.insert("Theme", r#"
            theme=""
            append_theme() { local val="$1"; local name="$2"; [ -n "$val" ] && theme="${theme}${theme:+, }$name: $val"; }
            if command -v gsettings >/dev/null; then append_theme "$(gsettings get org.gnome.desktop.interface gtk-theme 2>/dev/null | tr -d "'")" "GTK"; fi
            if command -v kreadconfig5 >/dev/null; then append_theme "$(kreadconfig5 --group LookAndFeel --key name 2>/dev/null)" "Plasma"; fi
            printf "%s" "${theme:-N/A}"
        "#);
        m.insert("Icons", r#"
            icons=""
            if command -v gsettings >/dev/null; then icons=$(gsettings get org.gnome.desktop.interface icon-theme 2>/dev/null | tr -d "'"); fi
            if [ -z "$icons" ] && command -v kreadconfig5 >/dev/null; then icons=$(kreadconfig5 --group Icons --key Theme 2>/dev/null); fi
            printf "%s" "${icons:-N/A}"
        "#);
        m.insert("Terminal Font", r#"
            font="N/A" # Default to N/A
            if command -v gsettings >/dev/null; then
                 profile_id=$(gsettings get org.gnome.Terminal.ProfilesList default 2>/dev/null | tr -d "'")
                 if [ -n "$profile_id" ]; then
                      profile_path="/org/gnome/terminal/legacy/profiles:/:$profile_id/"
                      use_sys=$(gsettings get org.gnome.Terminal.Legacy.Profile:"$profile_path" use-system-font 2>/dev/null)
                      if [ "$use_sys" = "true" ]; then
                           font=$(gsettings get org.gnome.desktop.interface monospace-font-name 2>/dev/null | tr -d "'")" (Sys)"
                      else
                           font=$(gsettings get org.gnome.Terminal.Legacy.Profile:"$profile_path" font 2>/dev/null | tr -d "'")
                      fi
                 fi
            fi
            printf "%s" "$font"
         "#);
         m.insert("GPU", r#"
            gpu="N/A"
            if command -v lspci > /dev/null; then
                 gpu=$(lspci 2>/dev/null | grep -E 'VGA|3D|Display' | head -n1 | cut -d':' -f3- | sed 's/^[ \t]*//; s/ (rev ..)$//')
            elif [ "$(uname -s)" = "Darwin" ]; then
                 gpu=$(system_profiler SPDisplaysDataType 2>/dev/null | awk -F': ' '/Chipset Model:/ {print $2; exit}')
            fi
            printf "%s" "${gpu:-N/A}"
         "#);
        m
    };
}

// --- Helper Functions for Formatting ---
// Helper to apply label color and boldness
pub fn format_label(label: &str) -> String {
    format!("{}{}{}", label.color(LABEL_COLOR).bold(), RESET_COLOR_STR, SYS_INFO_KV_SEPARATOR)
}

// Helper to apply value color
pub fn format_value(value: &str) -> String {
    format!(" {}", value.color(VALUE_COLOR))
}

// Helper for error values (can be used by fetch_shell_command)
pub fn format_error(value: &str) -> String {
    format!(" {}", value.color(ERROR_COLOR))
}

// Helper for separator lines
pub fn format_separator(text: &str, width: usize) -> String {
    if text.is_empty() {
        // Default separator: line of dashes
        format!("{}", SYS_INFO_SEPARATOR_CHAR.to_string().repeat(width).color(SEPARATOR_COLOR))
    } else {
        // Custom text separator (e.g., "Hardware") - centered
        let text_len = text.chars().count();
        let padding = width.saturating_sub(text_len) / 2;
        format!("{}{}{}", " ".repeat(padding), text.color(SEPARATOR_COLOR).bold(), " ".repeat(padding))
    }
}


// --- Define Fetcher Types and SysInfoItem structure ---
pub enum FetcherType {
    SysinfoFn(fn(&System) -> String), // Function using sysinfo
    ShellCommand(&'static str),     // Key into FALLBACK_COMMANDS map
    Separator(&'static str),        // Text for separator (empty for default line)
    // ColorPalette could be special cased or use SysinfoFn with a dummy function
}

pub struct SysInfoItem {
   pub label: &'static str, // Label to display (or header text for Separator)
   pub fetcher_type: FetcherType,
}


// --- Define the order and fetchers ---
// Now using the new structure and including all desired fields
pub const SYSTEM_INFO_ORDER: &[SysInfoItem] = &[
    SysInfoItem { label: "User@Host", fetcher_type: FetcherType::SysinfoFn(crate::sysinfo_fetchers::get_user_host) },
    SysInfoItem { label: "", fetcher_type: FetcherType::Separator("") }, // Default separator
    SysInfoItem { label: "OS", fetcher_type: FetcherType::SysinfoFn(crate::sysinfo_fetchers::get_os) },
    SysInfoItem { label: "Kernel", fetcher_type: FetcherType::SysinfoFn(crate::sysinfo_fetchers::get_kernel) },
    SysInfoItem { label: "Uptime", fetcher_type: FetcherType::SysinfoFn(crate::sysinfo_fetchers::get_uptime) },
    // SysInfoItem { label: "Packages", fetcher_type: FetcherType::ShellCommand("Packages") }, // Uncomment if desired
    SysInfoItem { label: "Shell", fetcher_type: FetcherType::SysinfoFn(crate::sysinfo_fetchers::get_shell) },
    SysInfoItem { label: "Resolution", fetcher_type: FetcherType::ShellCommand("Resolution") },
    SysInfoItem { label: "WM", fetcher_type: FetcherType::ShellCommand("WM") },
    SysInfoItem { label: "Theme", fetcher_type: FetcherType::ShellCommand("Theme") },
    SysInfoItem { label: "Icons", fetcher_type: FetcherType::ShellCommand("Icons") },
    SysInfoItem { label: "Terminal", fetcher_type: FetcherType::SysinfoFn(crate::sysinfo_fetchers::get_terminal) },
    SysInfoItem { label: "Terminal Font", fetcher_type: FetcherType::ShellCommand("Terminal Font") },
    SysInfoItem { label: "", fetcher_type: FetcherType::Separator("") }, // Default separator
    SysInfoItem { label: "Hardware", fetcher_type: FetcherType::Separator("Hardware") }, // Named separator
    SysInfoItem { label: "CPU", fetcher_type: FetcherType::SysinfoFn(crate::sysinfo_fetchers::get_cpu) },
    SysInfoItem { label: "GPU", fetcher_type: FetcherType::ShellCommand("GPU") },
    SysInfoItem { label: "Memory", fetcher_type: FetcherType::SysinfoFn(crate::sysinfo_fetchers::get_memory) },
    SysInfoItem { label: "", fetcher_type: FetcherType::Separator("") }, // Default separator
    SysInfoItem { label: "Color Palette", fetcher_type: FetcherType::SysinfoFn(crate::sysinfo_fetchers::get_color_palette) },
];