import os

LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "brain", "logs"))
os.makedirs(LOG_DIR, exist_ok=True)
TRACE_FILE = os.path.join(LOG_DIR, "trace.log")

# ANSI Text Colors
COLORS = {
    "RESET": "\033[0m",
    "GREEN": "\033[92m",
    "BLUE": "\033[94m",
    "CYAN": "\033[96m",
    "MAGENTA": "\033[95m",
    "YELLOW": "\033[93m",
    "RED": "\033[91m",
    "GRAY": "\033[90m",
}


def clear_trace_log():
    with open(TRACE_FILE, "w", encoding="utf-8") as f:
        f.write("=== THE KID TRACE LOG ===\n")


def trace_log(module: str, message: str, color: str = "GRAY", show_in_console: bool = True):
    """
    Prints a colored trace to the terminal and appends cleanly to the trace.log file
    so the user can tail it in a separate terminal.
    """
    color_code = COLORS.get(color.upper(), COLORS["RESET"])
    formatted_console = f"{color_code}[TRACE: {module}]{COLORS['RESET']} {message}"
    formatted_file = f"[TRACE: {module}] {message}\n"

    # Print to console if user wants it, or we could only print major things.
    # Currently, we'll print it out to keep behavior consistent, just colored.
    if show_in_console:
        print(formatted_console)

    # Append to file for separate terminal viewing
    with open(TRACE_FILE, "a", encoding="utf-8") as f:
        f.write(formatted_file)


def error_log(message: str):
    formatted_console = f"{COLORS['RED']}[ERROR]{COLORS['RESET']} {message}"
    formatted_file = f"[ERROR] {message}\n"
    print(formatted_console)
    with open(TRACE_FILE, "a", encoding="utf-8") as f:
        f.write(formatted_file)
