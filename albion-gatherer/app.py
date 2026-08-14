"""Albion Gatherer — interfaz gráfica hecha con customtkinter."""
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
        self.geometry("900x680")
        self.minsize(860, 640)

        self._res_vars = {}
        self._smart_switches = {}
        self._build_header()
        self._build_tabs()
        self._build_log()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # -- disposición ----------------------------------------------------------
    def _build_header(self):
        bar = ctk.CTkFrame(self, corner_radius=0, height=66, fg_color="#1b1d22")
        bar.pack(fill="x")
        ctk.CTkLabel(bar, text="Albion Gatherer",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(side="left", padx=22, pady=16)
        self.status_lbl = ctk.CTkLabel(bar, text=C.STATUS_IDLE, text_color=ACCENT,
                                       font=ctk.CTkFont(size=15, weight="bold"))
        self.status_lbl.pack(side="right", padx=22)

    def _build_tabs(self):
        self.tabs = ctk.CTkTabview(self, corner_radius=12)
        self.tabs.pack(fill="both", expand=True, padx=16, pady=(14, 8))
        self._tab_setup(self.tabs.add("Ajustes"))
        self._tab_routes(self.tabs.add("Rutas"))
        self._tab_control(self.tabs.add("Control"))

    def _slider(self, parent, label, key, lo, hi, steps, fmt="{:.2f}"):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=6)
        ctk.CTkLabel(row, text=label, width=210, anchor="w").pack(side="left")
        val = ctk.CTkLabel(row, text=fmt.format(self.cfg[key]), width=60, text_color=MUTED)
        val.pack(side="right")

        def on_change(v, k=key, lbl=val, f=fmt):
            self.cfg[k] = round(float(v), 3)
            lbl.configure(text=f.format(self.cfg[k]))
        s = ctk.CTkSlider(row, from_=lo, to=hi, number_of_steps=steps, command=on_change)
        s.set(self.cfg[key])
        s.pack(side="left", fill="x", expand=True, padx=12)

    def _smart_switch(self, parent, label, key):
        sw = ctk.CTkSwitch(parent, text=label)
        if self.cfg.get(key, True):
            sw.select()
        sw.pack(anchor="w", padx=14, pady=4)
        self._smart_switches[key] = sw

    def _tab_setup(self, tab):
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        ctk.CTkLabel(scroll, text="Ciudad de origen (adonde vuelve el bot cuando se rompen las herramientas)",
                     anchor="w").pack(fill="x", padx=14, pady=(14, 2))
        self.city_entry = ctk.CTkEntry(scroll, placeholder_text="Martlock")
        self.city_entry.insert(0, self.cfg["home_city"])
        self.city_entry.pack(fill="x", padx=14, pady=(0, 12))

        ctk.CTkLabel(scroll, text="Recursos a recolectar", anchor="w").pack(fill="x", padx=14)
        grid = ctk.CTkFrame(scroll, fg_color="transparent")
        grid.pack(fill="x", padx=8, pady=4)
        for i, res in enumerate(self.cfg["resources_all"]):
            var = ctk.BooleanVar(value=res in self.cfg["resources_selected"])
            self._res_vars[res] = var
            ctk.CTkCheckBox(grid, text=res, variable=var).grid(
                row=i // 3, column=i % 3, sticky="w", padx=14, pady=6)

        ctk.CTkLabel(scroll, text="Inteligencia", anchor="w",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(fill="x", padx=14, pady=(14, 2))
        self._smart_switch(scroll, "Escaneo inteligente (ve y farmea todos los nodos visibles)", "smart_scan")
        self._smart_switch(scroll, "Recolección adaptativa (detecta cuándo el nodo se agota)", "adaptive_gather")
        self._smart_switch(scroll, "Confianza adaptativa (se autocalibra según aciertos)", "adaptive_threshold")
        self._smart_switch(scroll, "Humanizar (ruido en tiempos + descansos tipo humano)", "humanize")

        self._slider(scroll, "Confianza de coincidencia", "threshold", 0.5, 0.95, 45)
        self._slider(scroll, "Retardo de viaje (s)", "travel_delay", 0.4, 5.0, 46)
        self._slider(scroll, "Techo de recolección (s)", "gather_delay", 0.5, 6.0, 55)
        self._slider(scroll, "Tiempo de movimiento del cursor (s)", "move_time", 0.05, 1.0, 19)
        self._slider(scroll, "Nodos por parada (máx)", "max_scan_nodes", 1, 8, 7, fmt="{:.0f}")
        self._slider(scroll, "Volver a casa tras N recolecciones", "max_gathers", 0, 120, 120, fmt="{:.0f}")
        self._slider(scroll, "Descanso cada (mín) recolecciones", "break_every_min", 5, 80, 75, fmt="{:.0f}")
        self._slider(scroll, "Descanso cada (máx) recolecciones", "break_every_max", 10, 120, 110, fmt="{:.0f}")

        self.resume_sw = ctk.CTkSwitch(scroll, text="Reanudar el bucle automáticamente al volver a casa")
        if self.cfg["auto_resume"]:
            self.resume_sw.select()
        self.resume_sw.pack(anchor="w", padx=14, pady=(10, 6))

        ctk.CTkButton(scroll, text="Guardar ajustes", command=self.save_settings,
                      fg_color=ACCENT).pack(anchor="e", padx=14, pady=8)

    def _tab_routes(self, tab):
        ctk.CTkLabel(tab, text="Graba el movimiento apuntando con el ratón dentro del juego y "
                              "pulsando atajos.\nF7 = añadir el cursor actual como punto    "
                              "F8 = capturar una imagen de nodo/herramienta bajo el cursor",
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
        ctk.CTkLabel(row, text="Nombre de plantilla", width=140, anchor="w").pack(side="left")
        self.tpl_entry = ctk.CTkEntry(row, placeholder_text="mineral / broken / ...")
        self.tpl_entry.insert(0, "mineral")
        self.tpl_entry.pack(side="left", fill="x", expand=True, padx=8)
        self.tpl_entry.bind("<KeyRelease>",
                            lambda e: self.recorder.set_tpl_name(self.tpl_entry.get()))

        self.arm_btn = ctk.CTkButton(tab, text="Armar grabador (F7 / F8)",
                                     command=self.toggle_recorder, fg_color=ACCENT)
        self.arm_btn.pack(fill="x", padx=14, pady=(8, 4))

        self.counts_lbl = ctk.CTkLabel(tab, text="", text_color=MUTED, justify="left")
        self.counts_lbl.pack(fill="x", padx=14, pady=4)
        self._refresh_counts()

        clr = ctk.CTkFrame(tab, fg_color="transparent")
        clr.pack(fill="x", padx=14, pady=6)
        labels = {"gather_route": "recolección", "town_route": "ciudad", "repair_route": "reparación"}
        for name in ("gather_route", "town_route", "repair_route"):
            ctk.CTkButton(clr, text=f"Borrar {labels[name]}", width=130,
                          fg_color="#5a2c2c",
                          command=lambda n=name: self.clear_route(n)).pack(side="left", padx=4)

    def _tab_control(self, tab):
        self.start_btn = ctk.CTkButton(tab, text="INICIAR", height=64,
                                       font=ctk.CTkFont(size=20, weight="bold"),
                                       fg_color=ACCENT, command=self.toggle_bot)
        self.start_btn.pack(fill="x", padx=40, pady=(30, 10))
        ctk.CTkLabel(tab, text="Pon el juego en tu monitor PRINCIPAL. Mantén la cámara "
                              "quieta mientras farmeas. Parada de emergencia: pulsa INICIAR otra vez.",
                     text_color=MUTED, wraplength=560, justify="center").pack(padx=20, pady=8)

    def _build_log(self):
        wrap = ctk.CTkFrame(self, corner_radius=12)
        wrap.pack(fill="both", expand=False, padx=16, pady=(0, 14))
        ctk.CTkLabel(wrap, text="Registro", anchor="w").pack(fill="x", padx=12, pady=(8, 0))
        self.log_box = ctk.CTkTextbox(wrap, height=150, wrap="word")
        self.log_box.pack(fill="both", expand=True, padx=12, pady=10)
        self.log_box.configure(state="disabled")

    # -- acciones -------------------------------------------------------------
    def save_settings(self):
        self.cfg["home_city"] = self.city_entry.get().strip() or "Martlock"
        self.cfg["resources_selected"] = [r for r, v in self._res_vars.items() if v.get()]
        self.cfg["auto_resume"] = bool(self.resume_sw.get())
        self.cfg["max_gathers"] = int(self.cfg["max_gathers"])
        self.cfg["max_scan_nodes"] = int(self.cfg["max_scan_nodes"])
        self.cfg["break_every_min"] = int(self.cfg["break_every_min"])
        self.cfg["break_every_max"] = max(int(self.cfg["break_every_min"]),
                                          int(self.cfg["break_every_max"]))
        for key, sw in self._smart_switches.items():
            self.cfg[key] = bool(sw.get())
        C.save(self.cfg)
        self.log("ajustes guardados.")

    def toggle_recorder(self):
        if self.recorder.armed():
            self.recorder.stop()
            self.arm_btn.configure(text="Armar grabador (F7 / F8)", fg_color=ACCENT)
        else:
            self.recorder.set_tpl_name(self.tpl_entry.get())
            self.recorder.start()
            self.arm_btn.configure(text="Grabador ARMADO — pulsa para desarmar", fg_color="#a06a1f")
        self._refresh_counts()

    def clear_route(self, name):
        self.cfg[name] = []
        C.save(self.cfg)
        self.log(f"borrada la ruta {name}")
        self._refresh_counts()

    def _refresh_counts(self):
        self.counts_lbl.configure(
            text=(f"recolección: {len(self.cfg['gather_route'])} pts   "
                  f"ciudad: {len(self.cfg['town_route'])} pts   "
                  f"reparación: {len(self.cfg['repair_route'])} pts"))
        self.after(1200, self._refresh_counts)

    def toggle_bot(self):
        if self.engine.running():
            self.engine.stop()
            self.start_btn.configure(text="INICIAR", fg_color=ACCENT)
        else:
            self.save_settings()
            self.engine.start()
            self.start_btn.configure(text="DETENER", fg_color="#b23b3b")

    # -- callbacks del motor / grabador --------------------------------------
    def log(self, msg):
        def _append():
            self.log_box.configure(state="normal")
            self.log_box.insert("end", msg + "\n")
            self.log_box.see("end")
            self.log_box.configure(state="disabled")
        self.after(0, _append)

    def set_status(self, text):
        self.after(0, lambda: self.status_lbl.configure(text=text))
        if text == C.STATUS_IDLE:
            self.after(0, lambda: self.start_btn.configure(text="INICIAR", fg_color=ACCENT))

    def _on_close(self):
        self.engine.stop()
        self.recorder.stop()
        self.destroy()


if __name__ == "__main__":
    App().mainloop()
