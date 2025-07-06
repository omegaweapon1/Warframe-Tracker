# Warframe Task Tracker v1.05a
# 1.0 - Starting point. GUI layout, daily/weekly columns, timers, bottom ribbon
# 1.01 - Gear menu acts as opt-in filter; completed tasks hidden until reset
# 1.02 - Enlarged and bolded main column headers
# 1.03 - Renamed Reputation "Teshin" to "Conclave" to avoid conflict with Vendor "Teshin"
# 1.04 - Attempted duplicate line break fix on collapse (did not work)
# 1.05 - Fixed separator rendering logic: now removes redundant separators properly
# 1.05a - Fixed crash by removing invalid font= from ttk.LabelFrame

import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta, timezone

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
        "Conclave"
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

        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True)

        self.visibility_settings = {}
        self.checked_tasks = {}
        self.timer_labels = {}

        for task_group in [DAILY_TASKS, WEEKLY_TASKS]:
            for section in task_group:
                for task in task_group[section]:
                    if task != "---":
                        self.visibility_settings[task] = tk.BooleanVar(value=True)
                        self.checked_tasks[task] = tk.BooleanVar(value=False)

        for task in EXTRA_TIMERS:
            self.visibility_settings[task] = tk.BooleanVar(value=True)
            self.checked_tasks[task] = tk.BooleanVar(value=False)
            self.timer_labels[task] = tk.StringVar()

        self.settings_window = None

        self.create_header()
        self.create_scrollable_area()
        self.create_task_frames()
        self.populate_task_columns()
        self.populate_timer_rows()
        self.create_bottom_ribbon()
        self.update_timer_labels()

    def create_header(self):
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill="x", pady=5)

        date_label = ttk.Label(header_frame, text=self.get_date_string(), font=("Segoe UI", 10, "bold"))
        date_label.pack(side="left", padx=10)

        self.gear_btn = ttk.Button(header_frame, text="⚙", command=self.open_settings)
        self.gear_btn.pack(side="right", padx=10)

        self.header_label = date_label
        self.root.after(60000, self.update_time)

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

        self.daily_col = ttk.Frame(content_frame)
        self.weekly_col = ttk.Frame(content_frame)

        self.daily_col.grid(row=0, column=0, padx=10, sticky="nw")
        self.weekly_col.grid(row=0, column=1, padx=10, sticky="nw")

        ttk.Label(self.daily_col, text="Daily Tasks", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))
        ttk.Label(self.weekly_col, text="Weekly Tasks", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))

    def add_tasks_with_separators(self, parent, task_list, section=None):
        last_was_separator = True
        for task in task_list:
            if task == "---":
                if not last_was_separator:
                    ttk.Separator(parent, orient="horizontal").pack(fill="x", padx=20, pady=4)
                    last_was_separator = True
                continue
            if self.visibility_settings[task].get() and not self.checked_tasks[task].get():
                cb = ttk.Checkbutton(parent, text=task, variable=self.checked_tasks[task])
                cb.pack(anchor="w", padx=20)
                last_was_separator = False

    def populate_task_columns(self):
        for widget in self.daily_col.winfo_children():
            if isinstance(widget, ttk.Checkbutton) or isinstance(widget, ttk.Separator) or isinstance(widget, ttk.Label):
                widget.destroy()

        for widget in self.weekly_col.winfo_children():
            if isinstance(widget, ttk.Checkbutton) or isinstance(widget, ttk.Separator) or isinstance(widget, ttk.Label):
                widget.destroy()

        ttk.Label(self.daily_col, text="Daily Tasks", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))
        for section in DAILY_TASKS:
            ttk.Label(self.daily_col, text=section, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=10, pady=(5, 0))
            self.add_tasks_with_separators(self.daily_col, DAILY_TASKS[section])

        ttk.Label(self.weekly_col, text="Weekly Tasks", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))
        for section in WEEKLY_TASKS:
            ttk.Label(self.weekly_col, text=section, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=10, pady=(5, 0))
            self.add_tasks_with_separators(self.weekly_col, WEEKLY_TASKS[section])

    def populate_timer_rows(self):
        if hasattr(self, "timer_frame"):
            self.timer_frame.destroy()
        self.timer_frame = ttk.LabelFrame(self.scroll_frame, text="Timers")
        self.timer_frame.pack(fill="x", padx=10, pady=5)

        for task in EXTRA_TIMERS:
            if self.visibility_settings[task].get() and not self.checked_tasks[task].get():
                cb = ttk.Checkbutton(self.timer_frame, textvariable=self.timer_labels[task], variable=self.checked_tasks[task])
                cb.pack(anchor="w", padx=20)

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

        self.complete_btn = ttk.Button(self.bottom_ribbon, text="Complete Checked", command=self.complete_tasks)
        self.complete_btn.pack(padx=10, pady=5, fill="x")

    def complete_tasks(self):
        for task in self.checked_tasks:
            if self.visibility_settings[task].get() and self.checked_tasks[task].get():
                self.checked_tasks[task].set(True)
        self.refresh_task_lists()

    def open_settings(self):
        if self.settings_window is not None and tk.Toplevel.winfo_exists(self.settings_window):
            return
        self.gear_btn.config(state="disabled")

        self.settings_window = tk.Toplevel(self.root)
        self.settings_window.title("Settings")
        self.settings_window.geometry("750x600")

        self.settings_window.protocol("WM_DELETE_WINDOW", self.close_settings)

        ttk.Label(self.settings_window, text="Show/Hide Tasks (Opt-In Filter)", font=("Segoe UI", 10, "bold")).pack(pady=5)

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
        weekly_col = ttk.LabelFrame(content, text="Weekly Tasks")
        daily_col.grid(row=0, column=0, padx=10, sticky="nw")
        weekly_col.grid(row=0, column=1, padx=10, sticky="nw")

        for section in DAILY_TASKS:
            ttk.Label(daily_col, text=section, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=10, pady=(5, 0))
            for task in DAILY_TASKS[section]:
                if task == "---":
                    ttk.Separator(daily_col, orient='horizontal').pack(fill='x', padx=20, pady=4)
                    continue
                cb = ttk.Checkbutton(daily_col, text=task, variable=self.visibility_settings[task], command=self.refresh_task_lists)
                cb.pack(anchor="w", padx=20)

        for section in WEEKLY_TASKS:
            ttk.Label(weekly_col, text=section, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=10, pady=(5, 0))
            for task in WEEKLY_TASKS[section]:
                cb = ttk.Checkbutton(weekly_col, text=task, variable=self.visibility_settings[task], command=self.refresh_task_lists)
                cb.pack(anchor="w", padx=20)

        timer_frame = ttk.LabelFrame(content, text="Timers")
        timer_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=10)

        for task in EXTRA_TIMERS:
            cb = ttk.Checkbutton(timer_frame, text=task, variable=self.visibility_settings[task], command=self.refresh_task_lists)
            cb.pack(anchor="w", padx=20)

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
