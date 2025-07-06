# Version 2.0
# - Added persistent memory for task visibility and completion states via JSON file.
# - On start, loads saved states if present, else defaults.
# - On changes or exit, saves current states to JSON for next session.

import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta, timezone
import json
import os

STATE_FILE = "tasktracker_state.json"

WEEKLY_TASKS = {
    "Vendors": [
        "Iron Wake",
        "Teshin",
        "Maroo",
        "Nora",
        "Bird 3",
        "Acrithis - Riven/Forma/Adapter",
        "Archimedean Yonta - Kuva"
    ],
    "Quests": [
        "Archon Hunt",
        "Deep Archimedea",
        "Temporal Archimedea",
        "Netracell",
        "Circuit",
        "SP Circuit",
        "Hex Calendar",
        "Kahl",
        "Helminth Invigoration"
    ]
}

DAILY_TASKS = {
    "Quests": [
        "Tribute",
        "Sortie",
        "KIM",
        "Syndicate Missions",
        "Steel Path Incursions"
    ],
    "Reputation": [
        "Ostron",
        "Quills",
        "---",
        "Solaris",
        "Ventkids",
        "Solaris Vox",
        "---",
        "Entrati",
        "Necraloid",
        "Cavia",
        "---",
        "Holdfasts",
        "---",
        "Hex",
        "---",
        "Cephalon Simaris",
        "Conclave"  # Changed from Teshin to Conclave in 1.03
    ],
    "Vendor": [
        "Acrithis - Arcanes"
    ]
}

EXTRA_TIMERS = ["Tenet Weapon Reset", "Coda Weapon Reset", "Baro Ki'Teer"]

class TaskTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Warframe Task Tracker")
        self.root.geometry("700x700")

        # Fonts with increased sizes
        self.font_main_header = ("Segoe UI", 14, "bold")
        self.font_col_header = ("Segoe UI", 12, "bold")
        self.font_sub_header = ("Segoe UI", 11, "bold")
        self.font_task = ("Segoe UI", 11)
        self.font_button = ("Segoe UI", 12)
        self.font_gear_button = ("Segoe UI", 14)

        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True)

        # Visibility settings in gear submenu: controls what is opt-in to show
        self.visibility_settings = {}
        # Completion status of tasks
        self.checked_tasks = {}

        # Initialize all tasks in both dicts
        for task_group in [DAILY_TASKS, WEEKLY_TASKS]:
            for section in task_group:
                for task in task_group[section]:
                    if task != "---":
                        self.visibility_settings[task] = tk.BooleanVar(value=True)  # default opt-in visible
                        self.checked_tasks[task] = tk.BooleanVar(value=False)  # not completed

        for task in EXTRA_TIMERS:
            self.visibility_settings[task] = tk.BooleanVar(value=True)
            self.checked_tasks[task] = tk.BooleanVar(value=False)

        self.timer_labels = {task: tk.StringVar() for task in EXTRA_TIMERS}

        self.settings_window = None

        self.load_state()

        self.create_header()
        self.create_scrollable_area()
        self.create_task_frames()
        self.populate_task_columns()
        self.populate_timer_rows()
        self.create_bottom_ribbon()
        self.update_timer_labels()

        # Save on exit
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def load_state(self):
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r") as f:
                    data = json.load(f)
                # Load visibility
                vis = data.get("visibility_settings", {})
                for task, val in vis.items():
                    if task in self.visibility_settings:
                        self.visibility_settings[task].set(val)
                # Load checked tasks
                checked = data.get("checked_tasks", {})
                for task, val in checked.items():
                    if task in self.checked_tasks:
                        self.checked_tasks[task].set(val)
            except Exception as e:
                print(f"Failed to load state: {e}")

    def save_state(self):
        data = {
            "visibility_settings": {task: var.get() for task, var in self.visibility_settings.items()},
            "checked_tasks": {task: var.get() for task, var in self.checked_tasks.items()}
        }
        try:
            with open(STATE_FILE, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Failed to save state: {e}")

    def on_close(self):
        self.save_state()
        self.root.destroy()

    def create_header(self):
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill="x", pady=5)

        date_label = ttk.Label(header_frame, text=self.get_date_string(), font=self.font_main_header)
        date_label.pack(side="left", padx=10)

        self.gear_btn = ttk.Button(header_frame, text="⚙", command=self.open_settings, style="Gear.TButton")
        self.gear_btn.pack(side="right", padx=10)

        self.header_label = date_label
        self.root.after(60000, self.update_time)

        # Style for gear button large font
        style = ttk.Style()
        style.configure("Gear.TButton", font=self.font_gear_button)

    def get_date_string(self):
        now = datetime.now()
        utc_now = datetime.now(timezone.utc)
        next_reset = (utc_now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        hours_to_reset = (next_reset - utc_now).total_seconds() / 3600
        return f"{now.strftime('%a %m/%d/%y')} (Reset in {hours_to_reset:.2f} Hrs)"

    def update_time(self):
        self.header_label.config(text=self.get_date_string())
        self.update_timer_labels()
        self.root.after(60000, self.update_time)

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
        for widget in self.daily_col.winfo_children():
            widget.destroy()
        for widget in self.weekly_col.winfo_children():
            widget.destroy()

        def add_tasks_with_separators(parent, tasks_list):
            last_was_separator = False
            for task in tasks_list:
                if task == "---":
                    if not last_was_separator:
                        sep = ttk.Separator(parent, orient='horizontal')
                        sep.pack(fill='x', padx=20, pady=4)
                        last_was_separator = True
                    continue
                else:
                    if self.visibility_settings.get(task, tk.BooleanVar(value=False)).get() and not self.checked_tasks.get(task, tk.BooleanVar(value=True)).get():
                        cb = ttk.Checkbutton(parent, text=task, variable=self.checked_tasks[task], style="Task.TCheckbutton")
                        cb.pack(anchor="w", padx=20)
                        last_was_separator = False

        # Daily Tasks: with subheaders bigger font
        for section in DAILY_TASKS:
            label = ttk.Label(self.daily_col, text=section, font=self.font_sub_header)
            label.pack(anchor="w", padx=10, pady=(5, 0))
            add_tasks_with_separators(self.daily_col, DAILY_TASKS[section])

        # Weekly Tasks:
        # Rebuild weekly quests with separators after specific tasks
        for widget in self.weekly_col.winfo_children():
            widget.destroy()

        label = ttk.Label(self.weekly_col, text="Vendors", font=self.font_sub_header)
        label.pack(anchor="w", padx=10, pady=(5, 0))
        add_tasks_with_separators(self.weekly_col, WEEKLY_TASKS["Vendors"])

        label = ttk.Label(self.weekly_col, text="Quests", font=self.font_sub_header)
        label.pack(anchor="w", padx=10, pady=(5, 0))

        last_was_separator = False
        for task in WEEKLY_TASKS["Quests"]:
            if task in ["Archon Hunt", "Netracell", "SP Circuit"]:
                if not last_was_separator:
                    sep = ttk.Separator(self.weekly_col, orient='horizontal')
                    sep.pack(fill='x', padx=20, pady=4)
                    last_was_separator = True

            if self.visibility_settings.get(task, tk.BooleanVar(value=False)).get() and not self.checked_tasks.get(task, tk.BooleanVar(value=True)).get():
                cb = ttk.Checkbutton(self.weekly_col, text=task, variable=self.checked_tasks[task], style="Task.TCheckbutton")
                cb.pack(anchor="w", padx=20)
                last_was_separator = False

    def populate_timer_rows(self):
        if hasattr(self, "timer_frame"):
            self.timer_frame.destroy()
        self.timer_frame = ttk.LabelFrame(self.scroll_frame, text="Timers")
        self.timer_frame.pack(fill="x", padx=10, pady=5)

        for task in EXTRA_TIMERS:
            if self.visibility_settings[task].get() and not self.checked_tasks[task].get():
                cb = ttk.Checkbutton(self.timer_frame, textvariable=self.timer_labels[task], variable=self.checked_tasks[task], style="Task.TCheckbutton")
                cb.pack(anchor="w", padx=20)

        style = ttk.Style()
        style.configure("Timer.TLabel", font=self.font_task)
        style.configure("Task.TCheckbutton", font=self.font_task)

    def update_timer_labels(self):
        utc_now = datetime.utcnow().replace(tzinfo=timezone.utc)
        epoch = datetime(2020, 1, 1, tzinfo=timezone.utc)
        days_since_epoch = (utc_now - epoch).days

        coda_days_to_reset = 4 - (days_since_epoch % 4)
        tenet_days_to_reset = (4 - ((days_since_epoch + 2) % 4))

        coda_next_reset = (utc_now + timedelta(days=coda_days_to_reset)).replace(hour=0, minute=0)
        tenet_next_reset = (utc_now + timedelta(days=tenet_days_to_reset)).replace(hour=0, minute=0)

        delta_coda = coda_next_reset - utc_now
        delta_tenet = tenet_next_reset - utc_now

        self.timer_labels["Coda Weapon Reset"].set(f"Coda Weapon Reset (Next Reset in {delta_coda.days} Days, {delta_coda.seconds // 3600} Hours)")
        self.timer_labels["Tenet Weapon Reset"].set(f"Tenet Weapon Reset (Next Reset in {delta_tenet.days} Days, {delta_tenet.seconds // 3600} Hours)")

        baro_next_arrival = datetime(2025, 6, 27, 14, 0, tzinfo=timezone.utc)
        while baro_next_arrival < utc_now:
            baro_next_arrival += timedelta(weeks=2)
        baro_leave = baro_next_arrival + timedelta(days=2)

        if utc_now < baro_next_arrival:
            delta_baro = baro_next_arrival - utc_now
            self.timer_labels["Baro Ki'Teer"].set(f"Baro Ki'Teer (Arrives in {delta_baro.days} Days, {delta_baro.seconds // 3600} Hours)")
        elif utc_now < baro_leave:
            delta_baro = baro_leave - utc_now
            self.timer_labels["Baro Ki'Teer"].set(f"Baro Ki'Teer (Leaves in {delta_baro.days} Days, {delta_baro.seconds // 3600} Hours)")

        self.root.after(60000, self.update_timer_labels)

    def create_bottom_ribbon(self):
        self.bottom_ribbon = ttk.Frame(self.root)
        self.bottom_ribbon.pack(fill="x", side="bottom", pady=5)

        self.complete_btn = ttk.Button(self.bottom_ribbon, text="Complete Checked", command=self.complete_tasks, style="Complete.TButton")
        self.complete_btn.pack(padx=10, pady=5, fill="x")

        style = ttk.Style()
        style.configure("Complete.TButton", font=self.font_button)

    def complete_tasks(self):
        for task in list(self.checked_tasks.keys()):
            if self.visibility_settings.get(task, tk.BooleanVar(value=False)).get() and self.checked_tasks.get(task, tk.BooleanVar(value=False)).get():
                self.checked_tasks[task].set(True)
        self.refresh_task_lists()
        self.save_state()

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

        # Add titles with larger font manually for clarity
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
                cb = ttk.Checkbutton(weekly_col, text=task, variable=self.visibility_settings[task], command=self.on_setting_change, style="Task.TCheckbutton")
                cb.pack(anchor="w", padx=20)
                if section == "Quests":
                    if task == "Archon Hunt":
                        ttk.Separator(weekly_col, orient='horizontal').pack(fill='x', padx=20, pady=4)
                    elif task == "Netracell":
                        ttk.Separator(weekly_col, orient='horizontal').pack(fill='x', padx=20, pady=4)
                    elif task == "SP Circuit":
                        ttk.Separator(weekly_col, orient='horizontal').pack(fill='x', padx=20, pady=4)

        style = ttk.Style()
        style.configure("Task.TCheckbutton", font=self.font_task)

    def on_setting_change(self):
        self.refresh_task_lists()
        self.save_state()

    def close_settings(self):
        if self.settings_window:
            self.settings_window.destroy()
            self.settings_window = None
        self.gear_btn.config(state="normal")

    def refresh_task_lists(self):
        self.populate_task_columns()
        self.populate_timer_rows()


if __name__ == '__main__':
    root = tk.Tk()
    app = TaskTrackerApp(root)
    root.mainloop()
