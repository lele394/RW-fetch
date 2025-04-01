# config.py
import os

# --- Script Paths ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_RSC_DIR = os.path.join(SCRIPT_DIR, "rsc")
DEFAULT_CACHE_FILE = os.path.join(SCRIPT_DIR, "cache.json")

# --- Image Categorization Thresholds ---
SMALL_THRESHOLD = 20
MEDIUM_THRESHOLD = 40
LARGE_THRESHOLD = 60

# --- System Information Display Order & Content ---
# Defines the structure of the system info panel.
# Labels here correspond to function names (e.g., "OS" -> get_os())
# or keys in FALLBACK_COMMANDS for items still using shell.
SYSTEM_INFO_ORDER = [
    {"label": "User@Host"},
    {"separator": True},
    {"label": "OS"},
    {"label": "Kernel"},
    {"label": "Uptime"},
    # {"label": "Packages"},        # Uses shell command, tends to timeout
    {"label": "Shell"},
    {"label": "Resolution"},      # Still uses shell command
    {"label": "WM"},              # Still uses shell command
    {"label": "Theme"},           # Still uses shell command
    {"label": "Icons"},           # Still uses shell command
    {"label": "Terminal"},
    {"label": "Terminal Font"},   # Still uses shell command (very unreliable)
    {"separator": True},
    {"separator": "Hardware"},
    {"label": "CPU"},
    {"label": "GPU"},             # Still uses shell command
    {"label": "Memory"},
    {"separator": True},
    {"label": "Color Palette"}
]

# --- Fallback Shell Commands ---
# For information difficult to get reliably via pure Python APIs.
# The main script will use subprocess for these keys if Python methods fail or aren't implemented.
FALLBACK_COMMANDS = {
    "Packages": r"""
        pkgs=''; updated=0
        append_pkg() { local name="$1"; local count="$2"; [ "$count" -gt 0 ] && pkgs="${pkgs}${pkgs:+, }$name ($count)"; updated=1; }
        if command -v dpkg-query >/dev/null; then append_pkg "apt" "$(dpkg-query -W -f='${Status}\n' 2>/dev/null | grep -c '^install ok installed')";
        elif command -v rpm >/dev/null; then append_pkg "rpm" "$(rpm -qa --nosignature --nodigest 2>/dev/null | wc -l)"; fi
        if command -v snap >/dev/null; then count=$(snap list 2>/dev/null | wc -l); [ "$count" -gt 1 ] && count=$((count-1)) || count=0; if [ "$count" -gt 0 ] || snap list >/dev/null 2>&1; then append_pkg "snap" "$count"; fi; fi
        if command -v flatpak >/dev/null; then count=$(flatpak list --app --columns=application 2>/dev/null | wc -l); [ "$count" -gt 1 ] && count=$((count-1)) || count=0; if [ "$count" -gt 0 ] || flatpak list >/dev/null 2>&1; then append_pkg "flatpak" "$count"; fi; fi
        [ "$updated" -eq 0 ] && pkgs="N/A" # Show N/A if no managers found/counted
        printf '%s' "$pkgs"
    """,
    "Resolution": r"""
        res=""
        if command -v xrandr >/dev/null; then res=$(xrandr --current 2>/dev/null | awk '/\*/ {print $1; exit}');
        elif command -v swaymsg >/dev/null; then res=$(swaymsg -t get_outputs | jq -r '.[] | select(.active) | .current_mode | "\(.width)x\(.height)"' 2>/dev/null | paste -sd ',' -);
        elif [ "$(uname -s)" = "Darwin" ]; then res=$(system_profiler SPDisplaysDataType 2>/dev/null | awk '/Resolution:/ {print $2 "x" $4; exit}'); fi
        printf "%s" "${res:-N/A}"
    """,
     "WM": r"""
        wm=""
        if [ -n "$XDG_CURRENT_DESKTOP" ]; then wm="$XDG_CURRENT_DESKTOP";
        elif [ -n "$DESKTOP_SESSION" ]; then wm="$DESKTOP_SESSION";
        elif command -v wmctrl >/dev/null; then wm=$(wmctrl -m 2>/dev/null | awk '/Name:/ {print $2}'); fi
        # Add more pgrep checks if desired, but keep it concise for fallback
        printf "%s" "${wm:-N/A}"
    """,
    "Theme": r"""
        theme=""
        append_theme() { local val="$1"; local name="$2"; [ -n "$val" ] && theme="${theme}${theme:+, }$name: $val"; }
        if command -v gsettings >/dev/null; then append_theme "$(gsettings get org.gnome.desktop.interface gtk-theme 2>/dev/null | tr -d "'")" "GTK"; fi
        if command -v kreadconfig5 >/dev/null; then append_theme "$(kreadconfig5 --group LookAndFeel --key name 2>/dev/null)" "Plasma"; fi
        printf "%s" "${theme:-N/A}"
    """,
    "Icons": r"""
        icons=""
        if command -v gsettings >/dev/null; then icons=$(gsettings get org.gnome.desktop.interface icon-theme 2>/dev/null | tr -d "'"); fi
        if [ -z "$icons" ] && command -v kreadconfig5 >/dev/null; then icons=$(kreadconfig5 --group Icons --key Theme 2>/dev/null); fi
        printf "%s" "${icons:-N/A}"
    """,
     "Terminal Font": r"""
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
     """,
     "GPU": r"""
        gpu="N/A"
        if command -v lspci > /dev/null; then
             gpu=$(lspci 2>/dev/null | grep -E 'VGA|3D|Display' | head -n1 | cut -d':' -f3- | sed 's/^[ \t]*//; s/ (rev ..)$//')
        elif [ "$(uname -s)" = "Darwin" ]; then
             gpu=$(system_profiler SPDisplaysDataType 2>/dev/null | awk -F': ' '/Chipset Model:/ {print $2; exit}')
        fi
        printf "%s" "${gpu:-N/A}"
     """,
}


# --- System Info Display Formatting ---
SYS_INFO_LABEL_COLOR = "\033[1;34m"
SYS_INFO_VALUE_COLOR = "\033[0;37m"
SYS_INFO_SEPARATOR_CHAR = "-"
SYS_INFO_KV_SEPARATOR = " >"
SYS_INFO_ERROR_COLOR = "\033[0;31m"
SYS_INFO_WARN_COLOR = "\033[0;33m" # Yellow for warnings like missing psutil
RESET_COLOR = "\033[0m"

# --- Image/Info Layout ---
IMAGE_INFO_SEPARATOR = "  │  "