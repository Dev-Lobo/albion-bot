"""Albion Gatherer — customtkinter GUI front end."""
import customtkinter as ctk

import config as C
from engine import BotEngine
from recorder import Recorder

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

ACCENT = "#3fae5a"
MUTED = "#8a8f98"


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.cfg = C.load()
        self.engine = BotEngine(self.cfg, self.log, self.set_status)
        self.recorder = Recorder(self.cfg, self.log)

        self.title("Albion Gatherer")
        self.geometry("900x640")
        self.minsize(860, 600)

        self._res_vars = {}
        self._build_header()
        self._build_tabs()
        self._build_log()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # -- layout ---------------------------------------------------------------
    def _build_header(self):
        bar = ctk.CTkFrame(self, corner_radius=0, height=66, fg_color="#1b1d22")
        bar.pack(fill="x")
        ctk.CTkLabel(bar, text="Albion Gatherer",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(side="left", padx=22, pady=16)
        self.status_lbl = ctk.CTkLabel(bar, text="Idle", text_color=ACCENT,
                                       font=ctk.CTkFont(size=15, weight="bold"))
        self.status_lbl.pack(side="right", padx=22)

    def _build_tabs(self):
        self.tabs = ctk.CTkTabview(self, corner_radius=12)
        self.tabs.pack(fill="both", expand=True, padx=16, pady=(14, 8))
        self._tab_setup(self.tabs.add("Setup"))
        self._tab_routes(self.tabs.add("Routes"))
        self._tab_control(self.tabs.add("Control"))

    def _slider(self, parent, label, key, lo, hi, steps, fmt="{:.2f}"):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=6)
        ctk.CTkLabel(row, text=label, width=170, anchor="w").pack(side="left")
        val = ctk.CTkLabel(row, text=fmt.format(self.cfg[key]), width=60, text_color=MUTED)
        val.pack(side="right")

        def on_change(v, k=key, lbl=val, f=fmt):
            self.cfg[k] = round(float(v), 3)
            lbl.configure(text=f.format(self.cfg[k]))
        s = ctk.CTkSlider(row, from_=lo, to=hi, number_of_steps=steps, command=on_change)
        s.set(self.cfg[key])
        s.pack(side="left", fill="x", expand=True, padx=12)

    def _tab_setup(self, tab):
        ctk.CTkLabel(tab, text="Home city (where the bot returns when tools break)",
                     anchor="w").pack(fill="x", padx=14, pady=(14, 2))
        self.city_entry = ctk.CTkEntry(tab, placeholder_text="Martlock")
        self.city_entry.insert(0, self.cfg["home_city"])
        self.city_entry.pack(fill="x", padx=14, pady=(0, 12))

        ctk.CTkLabel(tab, text="Resources to gather", anchor="w").pack(fill="x", padx=14)
        grid = ctk.CTkFrame(tab, fg_color="transparent")
        grid.pack(fill="x", padx=8, pady=4)
        for i, res in enumerate(self.cfg["resources_all"]):
            var = ctk.BooleanVar(value=res in self.cfg["resources_selected"])
            self._res_vars[res] = var
            ctk.CTkCheckBox(grid, text=res, variable=var).grid(
                row=i // 3, column=i % 3, sticky="w", padx=14, pady=6)

        self._slider(tab, "Match confidence", "threshold", 0.5, 0.95, 45)
        self._slider(tab, "Travel delay (s)", "travel_delay", 0.4, 5.0, 46)
        self._slider(tab, "Gather delay (s)", "gather_delay", 0.5, 6.0, 55)
        self._slider(tab, "Cursor move time (s)", "move_time", 0.05, 1.0, 19)
        self._slider(tab, "Return home after N gathers", "max_gathers", 0, 120, 120, fmt="{:.0f}")

        self.resume_sw = ctk.CTkSwitch(tab, text="Auto-resume loop after returning home")
        if self.cfg["auto_resume"]:
            self.resume_sw.select()
        self.resume_sw.pack(anchor="w", padx=14, pady=(10, 6))

        ctk.CTkButton(tab, text="Save settings", command=self.save_settings,
                      fg_color=ACCENT).pack(anchor="e", padx=14, pady=8)

    def _tab_routes(self, tab):
        ctk.CTkLabel(tab, text="Record movement by pointing your mouse in-game and "
                              "pressing hotkeys.\nF7 = add current cursor as a waypoint    "
                              "F8 = capture a node/tool image under the cursor",
                     justify="left", text_color=MUTED).pack(fill="x", padx=14, pady=(12, 8))

        self.target_seg = ctk.CTkSegmentedButton(
            tab, values=["gather_route", "town_route", "repair_route"],
            command=self.recorder.set_target)
        self.target_seg.set("gather_route")
        self.target_seg.pack(fill="x", padx=14, pady=6)

        self.type_seg = ctk.CTkSegmentedButton(
            tab, values=["minimap", "screen"], command=self.recorder.set_type)
        self.type_seg.set("minimap")
        self.type_seg.pack(fill="x", padx=14, pady=6)

        row = ctk.CTkFrame(tab, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=6)
        ctk.CTkLabel(row, text="Template name", width=120, anchor="w").pack(side="left")
        self.tpl_entry = ctk.CTkEntry(row, placeholder_text="ore / broken / ...")
        self.tpl_entry.insert(0, "ore")
        self.tpl_entry.pack(side="left", fill="x", expand=True, padx=8)
        self.tpl_entry.bind("<KeyRelease>",
                            lambda e: self.recorder.set_tpl_name(self.tpl_entry.get()))

        self.arm_btn = ctk.CTkButton(tab, text="Arm recorder (F7 / F8)",
                                     command=self.toggle_recorder, fg_color=ACCENT)
        self.arm_btn.pack(fill="x", padx=14, pady=(8, 4))

        self.counts_lbl = ctk.CTkLabel(tab, text="", text_color=MUTED, justify="left")
        self.counts_lbl.pack(fill="x", padx=14, pady=4)
        self._refresh_counts()

        clr = ctk.CTkFrame(tab, fg_color="transparent")
        clr.pack(fill="x", padx=14, pady=6)
        for name in ("gather_route", "town_route", "repair_route"):
            ctk.CTkButton(clr, text=f"Clear {name.split('_')[0]}", width=120,
                          fg_color="#5a2c2c",
                          command=lambda n=name: self.clear_route(n)).pack(side="left", padx=4)

    def _tab_control(self, tab):
        self.start_btn = ctk.CTkButton(tab, text="START", height=64,
                                       font=ctk.CTkFont(size=20, weight="bold"),
                                       fg_color=ACCENT, command=self.toggle_bot)
        self.start_btn.pack(fill="x", padx=40, pady=(30, 10))
        ctk.CTkLabel(tab, text="Move the game to your PRIMARY monitor. Keep the camera "
                              "steady while farming. Panic-stop: press START again.",
                     text_color=MUTED, wraplength=560, justify="center").pack(padx=20, pady=8)

    def _build_log(self):
        wrap = ctk.CTkFrame(self, corner_radius=12)
        wrap.pack(fill="both", expand=False, padx=16, pady=(0, 14))
        ctk.CTkLabel(wrap, text="Log", anchor="w").pack(fill="x", padx=12, pady=(8, 0))
        self.log_box = ctk.CTkTextbox(wrap, height=150, wrap="word")
        self.log_box.pack(fill="both", expand=True, padx=12, pady=10)
        self.log_box.configure(state="disabled")

    # -- actions --------------------------------------------------------------
    def save_settings(self):
        self.cfg["home_city"] = self.city_entry.get().strip() or "Martlock"
        self.cfg["resources_selected"] = [r for r, v in self._res_vars.items() if v.get()]
        self.cfg["auto_resume"] = bool(self.resume_sw.get())
        self.cfg["max_gathers"] = int(self.cfg["max_gathers"])
        C.save(self.cfg)
        self.log("settings saved.")

    def toggle_recorder(self):
        if self.recorder.armed():
            self.recorder.stop()
            self.arm_btn.configure(text="Arm recorder (F7 / F8)", fg_color=ACCENT)
        else:
            self.recorder.set_tpl_name(self.tpl_entry.get())
            self.recorder.start()
            self.arm_btn.configure(text="Recorder ARMED — click to disarm", fg_color="#a06a1f")
        self._refresh_counts()

    def clear_route(self, name):
        self.cfg[name] = []
        C.save(self.cfg)
        self.log(f"cleared {name}")
        self._refresh_counts()

    def _refresh_counts(self):
        self.counts_lbl.configure(
            text=(f"gather: {len(self.cfg['gather_route'])} wp   "
                  f"town: {len(self.cfg['town_route'])} wp   "
                  f"repair: {len(self.cfg['repair_route'])} wp"))
        self.after(1200, self._refresh_counts)

    def toggle_bot(self):
        if self.engine.running():
            self.engine.stop()
            self.start_btn.configure(text="START", fg_color=ACCENT)
        else:
            self.save_settings()
            self.engine.start()
            self.start_btn.configure(text="STOP", fg_color="#b23b3b")

    # -- callbacks from engine/recorder --------------------------------------
    def log(self, msg):
        def _append():
            self.log_box.configure(state="normal")
            self.log_box.insert("end", msg + "\n")
            self.log_box.see("end")
            self.log_box.configure(state="disabled")
        self.after(0, _append)

    def set_status(self, text):
        self.after(0, lambda: self.status_lbl.configure(text=text))
        if text == "Idle":
            self.after(0, lambda: self.start_btn.configure(text="START", fg_color=ACCENT))

    def _on_close(self):
        self.engine.stop()
        self.recorder.stop()
        self.destroy()


if __name__ == "__main__":
    App().mainloop()
