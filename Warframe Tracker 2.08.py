# Version 2.08
# - Baro Ki'Teer timer updated for 2-week reset cycle from July 11, 2025, 13:00 UTC
# - Shows "Present" for 48 hours after reset time, then switches text accordingly

import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta, timezone
import json
import os

STATE_FILE = "tasktracker_state.json"
WINDOW_POS_FILE = "window_position.json"

WEEKLY_TASKS = {
    "Vendors": [
        "Iron Wake", "Teshin", "Maroo", "Nora", "Bird 3",
        "Acrithis - Riven/Forma/Adapter", "Archimedean Yonta - Kuva"
    ],
    "Quests": [
        "Archon Hunt", "Deep Archimedea", "Temporal Archimedea", "Netracell",
        "Circuit", "SP Circuit", "Hex Calendar", "Kahl", "Helminth Invigoration"
    ]
}

DAILY_TASKS = {
    "Quests": [
        "Tribute", "Sortie", "KIM", "Syndicate Missions", "Steel Path Incursions"
    ],
    "Reputation": [
        "Ostron", "Quills", "---", "Solaris", "Ventkids", "Solaris Vox", "---",
        "Entrati", "Necraloid", "Cavia", "---", "Holdfasts", "---", "Hex", "---",
        "Cephalon Simaris", "Conclave"
    ],
    "Vendor": ["Acrithis - Arcanes"]
}

EXTRA_TIMERS = ["Tenet Weapon Reset", "Coda Weapon Reset", "Baro Ki'Teer"]

class TaskTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Warframe Task Tracker")
        self.root.geometry("700x700")
        self.load_window_position_and_size()

        self.font_main_header = ("Segoe UI", 14, "bold")
        self.font_col_header = ("Segoe UI", 12, "bold")
        self.font_sub_header = ("Segoe UI", 11, "bold")
        self.font_task = ("Segoe UI", 11)
        self.font_button = ("Segoe UI", 12)
        self.font_gear_button = ("Segoe UI", 14)

        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True)

        self.visibility_settings = {}
        self.checked_tasks = {}

        for task_group in [DAILY_TASKS, WEEKLY_TASKS]:
            for section in task_group:
                for task in task_group[section]:
                    if task != "---":
                        self.visibility_settings[task] = tk.BooleanVar(value=True)
                        self.checked_tasks[task] = tk.BooleanVar(value=False)

        for task in EXTRA_TIMERS:
            self.visibility_settings[task] = tk.BooleanVar(value=True)
            self.checked_tasks[task] = tk.BooleanVar(value=False)

        self.timer_labels = {task: tk.StringVar() for task in EXTRA_TIMERS}
        self.settings_window = None
        self.last_reset_check = None
        self.load_state()

        self.create_header()
        self.create_scrollable_area()
        self.create_task_frames()
        self.populate_task_columns()
        self.populate_timer_rows()
        self.create_bottom_ribbon()
        self.update_timer_labels()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.check_for_reset()
        self.root.after(60000, self.check_for_reset)

    def create_header(self):
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill="x", pady=5)

        date_label = ttk.Label(header_frame, text=self.get_date_string(), font=self.font_main_header)
        date_label.pack(side="left", padx=10)

        self.gear_btn = ttk.Button(header_frame, text="⚙", command=self.open_settings, style="Gear.TButton")
        self.gear_btn.pack(side="right", padx=10)

        self.header_label = date_label
        self.root.after(60000, self.update_time)

        style = ttk.Style()
        style.configure("Gear.TButton", font=self.font_gear_button)

    def open_settings(self):
        if self.settings_window is not None and tk.Toplevel.winfo_exists(self.settings_window):
            return
        self.gear_btn.config(state="disabled")

        self.settings_window = tk.Toplevel(self.root)
        self.settings_window.title("Settings")
        self.settings_window.geometry("750x600")
        self.settings_window.protocol("WM_DELETE_WINDOW", self.close_settings)

        ttk.Label(self.settings_window, text="Show/Hide Tasks (Opt-In Filter)", font=self.font_main_header).pack(pady=5)

        canvas = tk.Canvas(self.settings_window)
        scrollable = ttk.Frame(canvas)
        scroll_y = ttk.Scrollbar(self.settings_window, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scroll_y.set)

        scroll_y.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas.create_window((0, 0), window=scrollable, anchor='nw')
        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind_all("<MouseWheel>", lambda event: canvas.yview_scroll(int(-1 * (event.delta / 120)), "units"))

        content = ttk.Frame(scrollable)
        content.pack(fill="both", expand=True, padx=10, pady=5)

        daily_col = ttk.LabelFrame(content, text="Daily Tasks")
        daily_col.grid(row=0, column=0, padx=10, sticky="nw")
        weekly_col = ttk.LabelFrame(content, text="Weekly Tasks")
        weekly_col.grid(row=0, column=1, padx=10, sticky="nw")

        ttk.Label(daily_col, text="Daily Tasks", font=self.font_col_header).pack(anchor="w", padx=5, pady=5)
        ttk.Label(weekly_col, text="Weekly Tasks", font=self.font_col_header).pack(anchor="w", padx=5, pady=5)

        for section in DAILY_TASKS:
            ttk.Label(daily_col, text=section, font=self.font_sub_header).pack(anchor="w", padx=10, pady=(5, 0))
            for task in DAILY_TASKS[section]:
                if task == "---":
                    ttk.Separator(daily_col, orient='horizontal').pack(fill='x', padx=20, pady=4)
                    continue
                cb = ttk.Checkbutton(daily_col, text=task, variable=self.visibility_settings[task], command=self.on_setting_change, style="Task.TCheckbutton")
                cb.pack(anchor="w", padx=20)

        for section in WEEKLY_TASKS:
            ttk.Label(weekly_col, text=section, font=self.font_sub_header).pack(anchor="w", padx=10, pady=(5, 0))
            for task in WEEKLY_TASKS[section]:
                if task == "---":
                    ttk.Separator(weekly_col, orient='horizontal').pack(fill='x', padx=20, pady=4)
                    continue
                cb = ttk.Checkbutton(weekly_col, text=task, variable=self.visibility_settings[task], command=self.on_setting_change, style="Task.TCheckbutton")
                cb.pack(anchor="w", padx=20)

        style = ttk.Style()
        style.configure("Task.TCheckbutton", font=self.font_task)

    def close_settings(self):
        if self.settings_window:
            self.settings_window.destroy()
            self.settings_window = None
        self.gear_btn.config(state="normal")

    def get_date_string(self):
        now = datetime.now()
        utc_now = datetime.now(timezone.utc)
        next_reset = (utc_now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        hours_to_reset = (next_reset - utc_now).total_seconds() / 3600
        return f"{now.strftime('%a %m/%d/%y')} (Reset in {hours_to_reset:.2f} Hrs)"

    def update_time(self):
        self.header_label.config(text=self.get_date_string())
        self.root.after(60000, self.update_time)

    def load_window_position_and_size(self):
        if os.path.exists(WINDOW_POS_FILE):
            try:
                with open(WINDOW_POS_FILE, "r") as f:
                    pos = json.load(f)
                width = pos.get("width")
                height = pos.get("height")
                x = pos.get("x")
                y = pos.get("y")
                geometry_string = ""
                if width is not None and height is not None:
                    geometry_string += f"{width}x{height}"
                if x is not None and y is not None:
                    geometry_string += f"+{x}+{y}"
                if geometry_string:
                    self.root.geometry(geometry_string)
            except Exception as e:
                print(f"Failed to load window position and size: {e}")

    def save_window_position_and_size(self):
        try:
            self.root.update_idletasks()
            geom = self.root.geometry()
            size_part, _, pos_part = geom.partition('+')
            width, height = size_part.split('x')
            pos_split = pos_part.split('+')
            x = int(pos_split[0]) if len(pos_split) > 0 else 0
            y = int(pos_split[1]) if len(pos_split) > 1 else 0
            with open(WINDOW_POS_FILE, "w") as f:
                json.dump({"width": int(width), "height": int(height), "x": x, "y": y}, f)
        except Exception as e:
            print(f"Failed to save window position and size: {e}")

    def check_for_reset(self):
        now_utc = datetime.now(timezone.utc)
        last_check_str = self.state_data.get("last_reset_check") if hasattr(self, "state_data") else None
        if last_check_str:
            try:
                last_check = datetime.fromisoformat(last_check_str)
            except Exception:
                last_check = None
        else:
            last_check = None

        today = now_utc.date()
        is_sunday = now_utc.weekday() == 6
        should_reset = (not last_check) or (last_check.date() < today)

        if should_reset:
            for task in [t for s in DAILY_TASKS.values() for t in s if t != "---"]:
                if task in self.checked_tasks:
                    self.checked_tasks[task].set(False)
            if is_sunday:
                for task in [t for s in WEEKLY_TASKS.values() for t in s]:
                    if task in self.checked_tasks:
                        self.checked_tasks[task].set(False)

            if not hasattr(self, "state_data"):
                self.state_data = {}
            self.state_data["last_reset_check"] = now_utc.isoformat()
            self.refresh_task_lists()
            self.save_state()

        self.root.after(60000, self.check_for_reset)

    def load_state(self):
        self.state_data = {}
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r") as f:
                    self.state_data = json.load(f)
                vis = self.state_data.get("visibility_settings", {})
                for task, val in vis.items():
                    if task in self.visibility_settings:
                        self.visibility_settings[task].set(val)
                checked = self.state_data.get("checked_tasks", {})
                for task, val in checked.items():
                    if task in self.checked_tasks:
                        self.checked_tasks[task].set(val)
            except Exception as e:
                print(f"Failed to load state: {e}")

    def save_state(self):
        if not hasattr(self, "state_data"):
            self.state_data = {}
        self.state_data["visibility_settings"] = {task: var.get() for task, var in self.visibility_settings.items()}
        self.state_data["checked_tasks"] = {task: var.get() for task, var in self.checked_tasks.items()}
        try:
            with open(STATE_FILE, "w") as f:
                json.dump(self.state_data, f, indent=4)
        except Exception as e:
            print(f"Failed to save state: {e}")

    def refresh_task_lists(self):
        self.populate_task_columns()
        self.populate_timer_rows()

    def create_scrollable_area(self):
        self.canvas = tk.Canvas(self.main_frame)
        self.scroll_frame = ttk.Frame(self.canvas)
        scrollbar = ttk.Scrollbar(self.main_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor='nw')
        self.scroll_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind_all("<MouseWheel>", lambda event: self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units"))

    def create_task_frames(self):
        content_frame = ttk.Frame(self.scroll_frame)
        content_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.daily_col_label = ttk.Label(content_frame, text="Daily Tasks", font=self.font_col_header)
        self.daily_col_label.grid(row=0, column=0, sticky="w", padx=10)
        self.daily_col = ttk.Frame(content_frame)
        self.daily_col.grid(row=1, column=0, padx=10, sticky="nw")

        self.weekly_col_label = ttk.Label(content_frame, text="Weekly Tasks", font=self.font_col_header)
        self.weekly_col_label.grid(row=0, column=1, sticky="w", padx=10)
        self.weekly_col = ttk.Frame(content_frame)
        self.weekly_col.grid(row=1, column=1, padx=10, sticky="nw")

    def populate_task_columns(self):
        for widget in self.daily_col.winfo_children(): widget.destroy()
        for widget in self.weekly_col.winfo_children(): widget.destroy()

        def add_tasks(parent, task_list):
            last_was_sep = False
            for task in task_list:
                if task == "---":
                    if not last_was_sep:
                        ttk.Separator(parent, orient='horizontal').pack(fill='x', padx=20, pady=4)
                        last_was_sep = True
                    continue
                if self.visibility_settings[task].get() and not self.checked_tasks[task].get():
                    cb = ttk.Checkbutton(parent, text=task, variable=self.checked_tasks[task], style="Task.TCheckbutton")
                    cb.pack(anchor="w", padx=20)
                    last_was_sep = False

        for section in DAILY_TASKS:
            ttk.Label(self.daily_col, text=section, font=self.font_sub_header).pack(anchor="w", padx=10, pady=(5, 0))
            add_tasks(self.daily_col, DAILY_TASKS[section])

        for category in ["Vendors", "Quests"]:
            ttk.Label(self.weekly_col, text=category, font=self.font_sub_header).pack(anchor="w", padx=10, pady=(5, 0))
            add_tasks(self.weekly_col, WEEKLY_TASKS[category])

    def populate_timer_rows(self):
        if hasattr(self, "timer_frame"):
            self.timer_frame.destroy()
        self.timer_frame = ttk.LabelFrame(self.scroll_frame, text="Custom Timers")
        self.timer_frame.pack(fill="x", padx=10, pady=5)

        # Apply font matching other headers to LabelFrame text
        self.timer_frame.configure(labelanchor="nw")
        style = ttk.Style()
        style.configure("CustomTimer.TLabelframe.Label", font=self.font_col_header)
        self.timer_frame.configure(style="CustomTimer.TLabelframe")

        for task in EXTRA_TIMERS:
            if self.visibility_settings[task].get():
                label = self.timer_labels[task].get()
                if self.checked_tasks[task].get():
                    label += " ✔"
                cb = ttk.Checkbutton(self.timer_frame, text=label, variable=self.checked_tasks[task], style="Task.TCheckbutton")
                cb.pack(anchor="w", padx=20)

        style.configure("Task.TCheckbutton", font=self.font_task)

    def update_timer_labels(self):
        utc_now = datetime.now(timezone.utc)

        tenet_base = datetime(2025, 7, 3, tzinfo=timezone.utc)
        coda_base = datetime(2025, 7, 5, tzinfo=timezone.utc)
        baro_base = datetime(2025, 7, 11, 13, 0, tzinfo=timezone.utc)  # July 11, 2025 13:00 UTC

        def next_reset(base, interval_days):
            while base <= utc_now:
                base += timedelta(days=interval_days)
            return base

        tenet_next = next_reset(tenet_base, 4)
        coda_next = next_reset(coda_base, 4)
        baro_next = next_reset(baro_base, 14)

        def format_td(td):
            days = td.days
            hours = td.seconds // 3600
            minutes = (td.seconds % 3600) // 60
            return days, hours, minutes

        tdelta_tenet = tenet_next - utc_now
        tdelta_coda = coda_next - utc_now
        tdelta_baro = baro_next - utc_now

        # Baro presence window: from baro_next - 14 days + 14 days reset, so we find the last reset in past and check if within 48 hrs
        # Actually better: Find last reset by subtracting intervals until <= utc_now
        baro_last = baro_next - timedelta(days=14)
        presence_end = baro_last + timedelta(hours=48)

        days_baro, hours_baro, minutes_baro = format_td(tdelta_baro)

        if baro_last <= utc_now < presence_end:
            # Baro is present
            # Show how long until he returns (next reset)
            self.timer_labels["Baro Ki'Teer"].set(f"Baro Ki'Teer - Present (Returns in {days_baro}d {hours_baro}h)")
        else:
            # Baro not present
            self.timer_labels["Baro Ki'Teer"].set(f"Baro Ki'Teer (Returns in {days_baro}d {hours_baro}h)")

        self.timer_labels["Tenet Weapon Reset"].set(f"Tenet Weapon Reset (Next in {tdelta_tenet.days}d {tdelta_tenet.seconds//3600}h)")
        self.timer_labels["Coda Weapon Reset"].set(f"Coda Weapon Reset (Next in {tdelta_coda.days}d {tdelta_coda.seconds//3600}h)")

        self.refresh_task_lists()
        self.root.after(60000, self.update_timer_labels)

    def create_bottom_ribbon(self):
        frame = ttk.Frame(self.root)
        frame.pack(side="bottom", fill="x", pady=5)

        ttk.Button(frame, text="Simulate Week", command=self.simulate_week_reset, style="Task.TButton").pack(side="right", padx=5)
        ttk.Button(frame, text="Simulate Day", command=self.simulate_day_reset, style="Task.TButton").pack(side="right", padx=5)
        ttk.Button(frame, text="Complete Checked", command=self.complete_tasks, style="Task.TButton").pack(side="right", padx=5)
        ttk.Button(frame, text="Reset", command=self.reset_tasks, style="Task.TButton").pack(side="right", padx=5)

        style = ttk.Style()
        style.configure("Task.TButton", font=self.font_button)

    def reset_tasks(self):
        for task in self.checked_tasks:
            if self.visibility_settings[task].get():
                self.checked_tasks[task].set(False)
        self.refresh_task_lists()
        self.save_state()

    def complete_tasks(self):
        for task in self.checked_tasks:
            if self.visibility_settings[task].get():
                self.checked_tasks[task].set(True)
        self.refresh_task_lists()
        self.save_state()

    def simulate_day_reset(self):
        for task in [t for s in DAILY_TASKS.values() for t in s if t != "---"]:
            self.checked_tasks[task].set(False)
        self.refresh_task_lists()
        self.save_state()

    def simulate_week_reset(self):
        for task in [t for s in WEEKLY_TASKS.values() for t in s]:
            self.checked_tasks[task].set(False)
        self.refresh_task_lists()
        self.save_state()

    def on_setting_change(self):
        self.refresh_task_lists()
        self.save_state()

    def on_close(self):
        self.save_state()
        self.save_window_position_and_size()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = TaskTrackerApp(root)
    root.mainloop()