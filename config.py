# config.py
import os
import sys

# --- Script Paths ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_RSC_DIR = os.path.join(SCRIPT_DIR, "rsc")
DEFAULT_CACHE_FILE = os.path.join(SCRIPT_DIR, "cache.json")

# --- Image Categorization Thresholds ---
SMALL_THRESHOLD = 20
MEDIUM_THRESHOLD = 40
LARGE_THRESHOLD = 60

# --- System Information Fetching ---

# This list defines the ORDER and CONTENT of the system info display.
# Each item is a dictionary:
# - {"label": "LabelName"} : Displays the info item with this label. The command
#                             is looked up in SYSTEM_INFO_COMMANDS below.
# - {"separator": "Optional Text"} : Displays a separator. If "Optional Text" is
#                                     provided, it's printed. Otherwise, a line
#                                     using SYS_INFO_SEPARATOR_CHAR is printed.
# - {"separator": True} : Displays a default separator line.
SYSTEM_INFO_ORDER = [
    {"label": "User@Host"},
    {"separator": True}, # Default line separator
    {"label": "OS"},
    {"label": "Kernel"},
    {"label": "Uptime"},
    # {"label": "Packages"}, # tends to error out
    {"label": "Shell"},
    {"label": "Resolution"},
    {"label": "WM"},
    {"label": "Theme"}, # WM Theme / GTK Theme
    {"label": "Icons"},
    {"label": "Terminal"},
    {"label": "Terminal Font"},
    {"separator": True}, # Separator with text
    {"label": "CPU"},
    {"label": "GPU"},
    {"label": "Memory"},
    {"separator": True},
    {"label": "Color Palette"}
]

# Dictionary mapping info labels (used in SYSTEM_INFO_ORDER) to shell commands.
SYSTEM_INFO_COMMANDS = {
    "User@Host": r"printf '%s@%s' \"$(whoami)\" \"$(hostname)\"",
    "OS": r"""
        if command -v lsb_release > /dev/null; then
            lsb_release -ds | sed 's/"//g'
        elif [ -f /etc/os-release ]; then
            awk -F= '/^PRETTY_NAME=/ {print $2}' /etc/os-release | sed 's/"//g'
        elif [ "$(uname -s)" = "Darwin" ]; then
             printf '%s %s' "$(sw_vers -productName)" "$(sw_vers -productVersion)"
        else
            uname -o 2>/dev/null || uname -s
        fi
    """,
    "Kernel": "uname -r",
    "Uptime": "uptime -p | sed 's/^up //'",
    "Packages": r"""
        pkgs=''
        # APT (Debian/Ubuntu)
        if command -v dpkg >/dev/null; then
            count=$(dpkg -l | grep -c '^ii')
            pkgs="${pkgs}apt ($count), "
        # RPM (Fedora/CentOS/etc.)
        elif command -v rpm >/dev/null; then
            count=$(rpm -qa | wc -l)
            pkgs="${pkgs}rpm ($count), "
        fi
        # Snap
        if command -v snap >/dev/null; then
             # Subtract header line
            count=$(snap list 2>/dev/null | tail -n +2 | wc -l)
             # Check if snapd might be installed but no snaps are
             if [ "$count" -gt 0 ] || snap list >/dev/null 2>&1; then
                 pkgs="${pkgs}snap ($count), "
             fi
        fi
        # Flatpak
        if command -v flatpak >/dev/null; then
             # Subtract header line
            count=$(flatpak list 2>/dev/null | tail -n +2 | wc -l)
             # Check if flatpak might be installed but no apps are
             if [ "$count" -gt 0 ] || flatpak list >/dev/null 2>&1; then
                 pkgs="${pkgs}flatpak ($count), "
             fi
        fi
        # Remove trailing comma and space
        pkgs=$(echo "$pkgs" | sed 's/, $//')
        echo "$pkgs"
    """,
    "Shell": "basename \"$SHELL\"",
    "Resolution": r"""
        if command -v xdpyinfo >/dev/null; then
            xdpyinfo | awk '/dimensions:/ {print $2}'
        elif command -v swaymsg >/dev/null; then
             swaymsg -t get_outputs | jq -r '.[] | select(.active) | .current_mode | "\(.width)x\(.height)"' | paste -sd ',' -
        elif command -v wlr-randr >/dev/null; then
             # Might need parsing, output varies
             wlr-randr --json | jq -r '.[] | select(.active) | .modes[0] | "\(.width)x\(.height)"' | paste -sd ',' -
        elif [ "$(uname -s)" = "Darwin" ]; then
             system_profiler SPDisplaysDataType | awk '/Resolution:/ {print $2 "x" $4}' | head -n1
        else
            echo "N/A"
        fi
    """,
    "WM": r"""
        if [ -n "$XDG_CURRENT_DESKTOP" ]; then
             echo "$XDG_CURRENT_DESKTOP"
        elif [ "$DESKTOP_SESSION" = "ubuntu" ]; then
             echo "Gnome" # Special case for Ubuntu
        elif [ -n "$DESKTOP_SESSION" ]; then
             echo "$DESKTOP_SESSION" | awk '{print toupper(substr($0,1,1))substr($0,2)}' # Capitalize first letter
        elif command -v wmctrl >/dev/null; then
             wmctrl -m | awk '/Name:/ {print $2}'
        elif pgrep -x -U "$USER" Mutter > /dev/null; then echo "Mutter (Gnome)";
        elif pgrep -x -U "$USER" KWin > /dev/null; then echo "KWin (KDE)";
        elif pgrep -x -U "$USER" Xfwm4 > /dev/null; then echo "Xfwm4 (Xfce)";
        elif pgrep -x -U "$USER" Awesome > /dev/null; then echo "Awesome";
        elif pgrep -x -U "$USER" i3 > /dev/null; then echo "i3";
        elif pgrep -x -U "$USER" sway > /dev/null; then echo "Sway";
        else echo "N/A"; fi
    """,
    "Theme": r"""
        theme=""
        # Try gsettings (Gnome, Mate, Cinnamon, etc.)
        if command -v gsettings >/dev/null; then
            gtk_theme=$(gsettings get org.gnome.desktop.interface gtk-theme 2>/dev/null | tr -d "'")
            [ -n "$gtk_theme" ] && theme="GTK: $gtk_theme"
        fi
        # Try kreadconfig5 (KDE Plasma 5+)
        if command -v kreadconfig5 >/dev/null; then
            plasma_theme=$(kreadconfig5 --group LookAndFeel --key name 2>/dev/null)
             [ -n "$plasma_theme" ] && theme="$theme${theme:+, }Plasma: $plasma_theme"
        fi
        # Try Xfce settings
        if command -v xfconf-query >/dev/null; then
             xfce_theme=$(xfconf-query -c xsettings -p /Net/ThemeName 2>/dev/null)
             [ -n "$xfce_theme" ] && theme="$theme${theme:+, }Xfce: $xfce_theme"
        fi
        # Fallback or if empty
        [ -z "$theme" ] && theme="N/A"
        echo "$theme"
    """,
    "Icons": r"""
        icons=""
        # Try gsettings (Gnome, Mate, Cinnamon, etc.)
        if command -v gsettings >/dev/null; then
            icons=$(gsettings get org.gnome.desktop.interface icon-theme 2>/dev/null | tr -d "'")
        fi
         # Try kreadconfig5 (KDE Plasma 5+) - Icons often part of global theme or plasma theme
        if command -v kreadconfig5 >/dev/null && [ -z "$icons" ]; then
             icons=$(kreadconfig5 --group Icons --key Theme 2>/dev/null)
        fi
        # Try Xfce settings
        if command -v xfconf-query >/dev/null && [ -z "$icons" ]; then
             icons=$(xfconf-query -c xsettings -p /Net/IconThemeName 2>/dev/null)
        fi
         # Fallback or if empty
        [ -z "$icons" ] && icons="N/A"
        echo "$icons"
    """,
    "Terminal": r"echo \"$TERM_PROGRAM\" | sed 's/.app$//' || echo \"$TERM\"",
    "Terminal Font": r"""
        # Very difficult to get reliably. This tries Gnome Terminal's profile.
        if command -v gsettings >/dev/null; then
            profile_path="/org/gnome/terminal/legacy/profiles:/:$(gsettings get org.gnome.Terminal.ProfilesList default | tr -d "'")/"
            font=$(gsettings get org.gnome.Terminal.Legacy.Profile:"$profile_path" font 2>/dev/null | tr -d "'")
            use_sys_font=$(gsettings get org.gnome.Terminal.Legacy.Profile:"$profile_path" use-system-font 2>/dev/null)
            if [ "$use_sys_font" = "true" ]; then
                sys_font=$(gsettings get org.gnome.desktop.interface monospace-font-name 2>/dev/null | tr -d "'")
                echo "$sys_font (System Mono)"
            elif [ -n "$font" ]; then
                echo "$font"
            else
                echo "N/A (Gnome method failed)"
            fi
        else
            echo "N/A (gsettings not found)"
        fi
    """,
    "CPU": r"""
        if command -v lscpu > /dev/null; then
            lscpu | awk -F: '/^Model name/ {gsub(/^[ \t]+|[ \t]+$/, "", $2); print $2; exit}'
        elif [ "$(uname -s)" = "Darwin" ]; then
            sysctl -n machdep.cpu.brand_string
        else
            awk -F: '/^model name/ {gsub(/^[ \t]+|[ \t]+$/, "", $2); print $2; exit}' /proc/cpuinfo 2>/dev/null || echo "N/A"
        fi
    """,
    "GPU": r"""
        if command -v lspci > /dev/null; then
            lspci 2>/dev/null | awk -F: '/VGA|3D|Display/ {gsub(/^[ \t]+|[ \t]+$/, "", $3); print $3; exit}'
        elif [ "$(uname -s)" = "Darwin" ]; then
            system_profiler SPDisplaysDataType 2>/dev/null | awk -F: '/Chipset Model:/ {gsub(/^[ \t]+|[ \t]+$/, "", $2); print $2; exit}'
        else
            echo 'N/A (lspci not found)'
        fi
    """,
    "Memory": r"""
        if command -v free > /dev/null; then
            free -h | awk '/^Mem:/ {printf "%s / %s", $3, $2}'
        elif [ "$(uname -s)" = "Darwin" ]; then
            total_bytes=$(sysctl -n hw.memsize)
            # Use vm_stat for used memory approximation
            pagesize=$(pagesize)
            vm_stat_out=$(vm_stat)
            wired=$(echo "$vm_stat_out" | awk '/Pages wired down:/ {print $4}' | tr -d '.')
            active=$(echo "$vm_stat_out" | awk '/Pages active:/ {print $3}' | tr -d '.')
            # inactive=$(echo "$vm_stat_out" | awk '/Pages inactive:/ {print $3}' | tr -d '.') # Often counts towards cache
            compressed=$(echo "$vm_stat_out" | awk '/Pages stored in compressor:/ {print $5}' | tr -d '.')
            # Used = Wired + Active + Compressed (approximation)
            used_bytes=$(( ($wired + $active + $compressed) * $pagesize ))
            printf "%.2f GiB / %.2f GiB\n" $(echo "$used_bytes / (1024^3)" | bc -l) $(echo "$total_bytes / (1024^3)" | bc -l)

        elif [ -f /proc/meminfo ]; then
             awk '/MemTotal|MemAvailable/ {gsub(/ kB/, ""); val[$1] = $2} END {if (val["MemTotal"] > 0) printf "%.1f GiB / %.1f GiB", (val["MemTotal"] - val["MemAvailable"]) / 1024^2, val["MemTotal"] / 1024^2; else print "N/A"}' /proc/meminfo
        else
             echo "N/A"
        fi
    """,
    "Color Palette": r"""
        printf " "; for i in $(seq 0 7); do printf "\033[4%sm  " "$i"; done; printf "\033[0m\n"
        printf " "; for i in $(seq 0 7); do printf "\033[10%sm  " "$i"; done; printf "\033[0m"
    """
}

# --- System Info Display Formatting ---
SYS_INFO_LABEL_COLOR = "\033[1;34m"  # Bold Blue (or choose another)
SYS_INFO_VALUE_COLOR = "\033[0;37m"  # White
SYS_INFO_SEPARATOR_CHAR = "-"        # Character used for default separator lines
SYS_INFO_KV_SEPARATOR = ":"          # Separator between Label and Value (e.g., OS: Linux)
SYS_INFO_ERROR_COLOR = "\033[0;31m" # Red for errors
RESET_COLOR = "\033[0m"

# --- Image/Info Layout ---
IMAGE_INFO_SEPARATOR = "  │  " # Separator between image and sysinfo column