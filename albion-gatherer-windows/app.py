"""Albion Gatherer — interfaz estilo overlay oscuro con acento oro.

El diseño (paleta negro-violeta + oro, pestañas horizontales arriba y paneles
en tarjeta) está inspirado en la estética de un menú overlay tipo ImGui. Aquí
es puramente visual: viste al bot de recolección. Toda la configuración vive
dentro de esta ventana; no hay archivos ni pasos externos.
"""
import customtkinter as ctk

import config as C
from engine import BotEngine
from recorder import Recorder

ctk.set_appearance_mode("dark")

# --- paleta (tomada del esquema del overlay: oscuros violáceos + oro) --------
BG        = "#141418"   # fondo ventana
PANEL     = "#1b1a21"   # tarjetas
PANEL_2   = "#17161b"   # campos / hundidos
BORDER    = "#26262f"   # bordes sutiles
LINE      = "#34344a"   # líneas / inactivo lavanda
ACCENT    = "#FFD700"   # oro
ACCENT_D  = "#d8c06f"   # oro apagado (hover / relleno)
ACCENT_DK = "#8a7a1f"   # oro oscuro (bordes de acento)
TXT       = "#ffffff"   # texto activo
TXT_DIM   = "#72718a"   # texto inactivo (lavanda)
OK        = "#3fae5a"
DANGER    = "#b23b3b"

FONT = "Segoe UI"


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.cfg = C.load()
        self.engine = BotEngine(self.cfg, self.log, self.set_status)
        self.recorder = Recorder(self.cfg, self.log)

        self.title("Albion Gatherer")
        self.geometry("860x660")
        self.minsize(820, 620)
        self.configure(fg_color=BG)

        self._res_vars = {}
        self._smart_switches = {}
        self._tab_btns = {}
        self._tab_frames = {}
        self._current_tab = None

        self._build_header()
        self._build_body()
        self._build_log()
        self._show_tab("General")
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ============================ layout base ============================
    def _build_header(self):
        bar = ctk.CTkFrame(self, fg_color="#111015", corner_radius=0, height=58)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        brand = ctk.CTkFrame(bar, fg_color="transparent")
        brand.pack(side="left", padx=20)
        ctk.CTkLabel(brand, text="ALBION", text_color=ACCENT,
                     font=ctk.CTkFont(FONT, 18, "bold")).pack(side="left")
        ctk.CTkLabel(brand, text="GATHERER", text_color=TXT,
                     font=ctk.CTkFont(FONT, 18, "bold")).pack(side="left", padx=(6, 0))

        tabs = ctk.CTkFrame(bar, fg_color="transparent")
        tabs.pack(side="right", padx=14)
        for name in ("General", "Rutas", "Control"):
            b = ctk.CTkButton(tabs, text=name.upper(), width=92, height=34,
                              corner_radius=8, fg_color="transparent",
                              hover_color=PANEL, text_color=TXT_DIM,
                              font=ctk.CTkFont(FONT, 13, "bold"),
                              command=lambda n=name: self._show_tab(n))
            b.pack(side="left", padx=3)
            self._tab_btns[name] = b

        self.status_lbl = ctk.CTkLabel(bar, text="●  " + C.STATUS_IDLE, text_color=TXT_DIM,
                                       font=ctk.CTkFont(FONT, 13, "bold"))
        self.status_lbl.pack(side="right", padx=(0, 18))

    def _build_body(self):
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.pack(fill="both", expand=True, padx=16, pady=(14, 6))
        for name in ("General", "Rutas", "Control"):
            f = ctk.CTkScrollableFrame(self.body, fg_color="transparent")
            self._tab_frames[name] = f
        self._tab_general(self._tab_frames["General"])
        self._tab_rutas(self._tab_frames["Rutas"])
        self._tab_control(self._tab_frames["Control"])

    def _show_tab(self, name):
        if self._current_tab:
            self._tab_frames[self._current_tab].pack_forget()
            self._tab_btns[self._current_tab].configure(text_color=TXT_DIM, fg_color="transparent")
        self._tab_frames[name].pack(fill="both", expand=True)
        self._tab_btns[name].configure(text_color="#141418", fg_color=ACCENT)
        self._current_tab = name

    # ============================ helpers de estilo ============================
    def _card(self, parent, title, col=None, row=None):
        card = ctk.CTkFrame(parent, fg_color=PANEL, corner_radius=12,
                            border_width=1, border_color=BORDER)
        if col is not None:
            card.grid(row=row, column=col, sticky="nsew", padx=6, pady=6)
        else:
            card.pack(fill="x", padx=2, pady=6)
        head = ctk.CTkFrame(card, fg_color="transparent")
        head.pack(fill="x", padx=16, pady=(13, 2))
        ctk.CTkFrame(head, fg_color=ACCENT, width=3, height=15, corner_radius=2).pack(side="left")
        ctk.CTkLabel(head, text=title.upper(), text_color=ACCENT,
                     font=ctk.CTkFont(FONT, 12, "bold")).pack(side="left", padx=(9, 0))
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=(6, 14))
        return inner

    def _switch(self, parent, text, key):
        sw = ctk.CTkSwitch(parent, text=text, font=ctk.CTkFont(FONT, 13),
                           text_color=TXT, progress_color=ACCENT, button_color=TXT,
                           button_hover_color=ACCENT_D, fg_color=PANEL_2)
        if self.cfg.get(key, True):
            sw.select()
        sw.pack(anchor="w", pady=6)
        self._smart_switches[key] = sw
        return sw

    def _slider(self, parent, label, key, lo, hi, steps, fmt="{:.2f}"):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=7)
        ctk.CTkLabel(row, text=label, text_color=TXT_DIM, width=190, anchor="w",
                     font=ctk.CTkFont(FONT, 12)).pack(side="left")
        val = ctk.CTkLabel(row, text=fmt.format(self.cfg[key]), text_color=ACCENT, width=52,
                           font=ctk.CTkFont(FONT, 12, "bold"))
        val.pack(side="right")

        def on_change(v, k=key, lbl=val, f=fmt):
            self.cfg[k] = round(float(v), 3)
            lbl.configure(text=f.format(self.cfg[k]))
        s = ctk.CTkSlider(row, from_=lo, to=hi, number_of_steps=steps, command=on_change,
                          progress_color=ACCENT, button_color=ACCENT, button_hover_color=ACCENT_D,
                          fg_color=PANEL_2, height=14)
        s.set(self.cfg[key])
        s.pack(side="left", fill="x", expand=True, padx=12)

    def _button(self, parent, text, command, color=ACCENT, txt="#141418", **kw):
        return ctk.CTkButton(parent, text=text, command=command, corner_radius=9,
                             fg_color=color, hover_color=ACCENT_D if color == ACCENT else color,
                             text_color=txt, font=ctk.CTkFont(FONT, 13, "bold"), **kw)

    # ============================ pestaña GENERAL ============================
    def _tab_general(self, tab):
        tab.grid_columnconfigure((0, 1), weight=1, uniform="col")

        c1 = self._card(tab, "Ciudad y recursos", col=0, row=0)
        ctk.CTkLabel(c1, text="Ciudad de origen", text_color=TXT_DIM,
                     font=ctk.CTkFont(FONT, 12)).pack(anchor="w")
        self.city_entry = ctk.CTkEntry(c1, fg_color=PANEL_2, border_color=BORDER,
                                       text_color=TXT, placeholder_text="Martlock")
        self.city_entry.insert(0, self.cfg["home_city"])
        self.city_entry.pack(fill="x", pady=(4, 12))
        ctk.CTkLabel(c1, text="Recursos a recolectar", text_color=TXT_DIM,
                     font=ctk.CTkFont(FONT, 12)).pack(anchor="w")
        grid = ctk.CTkFrame(c1, fg_color="transparent")
        grid.pack(fill="x", pady=(4, 0))
        for i, res in enumerate(self.cfg["resources_all"]):
            var = ctk.BooleanVar(value=res in self.cfg["resources_selected"])
            self._res_vars[res] = var
            ctk.CTkCheckBox(grid, text=res, variable=var, font=ctk.CTkFont(FONT, 12),
                            text_color=TXT, fg_color=ACCENT, hover_color=ACCENT_D,
                            checkmark_color="#141418", border_color=LINE, corner_radius=5,
                            width=20, height=20).grid(row=i // 2, column=i % 2,
                                                      sticky="w", padx=(0, 14), pady=5)

        c2 = self._card(tab, "Inteligencia", col=1, row=0)
        self._switch(c2, "Escaneo inteligente", "smart_scan")
        self._switch(c2, "Recolección adaptativa", "adaptive_gather")
        self._switch(c2, "Confianza adaptativa", "adaptive_threshold")
        self._switch(c2, "Humanizar (tiempos + descansos)", "humanize")
        self.resume_sw = ctk.CTkSwitch(c2, text="Reanudar al volver a casa",
                                       font=ctk.CTkFont(FONT, 13), text_color=TXT,
                                       progress_color=ACCENT, button_color=TXT,
                                       button_hover_color=ACCENT_D, fg_color=PANEL_2)
        if self.cfg["auto_resume"]:
            self.resume_sw.select()
        self.resume_sw.pack(anchor="w", pady=6)

        c3 = self._card(tab, "Afinado", col=None)
        self._slider(c3, "Confianza de coincidencia", "threshold", 0.5, 0.95, 45)
        self._slider(c3, "Retardo de viaje (s)", "travel_delay", 0.4, 5.0, 46)
        self._slider(c3, "Techo de recolección (s)", "gather_delay", 0.5, 6.0, 55)
        self._slider(c3, "Movimiento del cursor (s)", "move_time", 0.05, 1.0, 19)
        self._slider(c3, "Nodos por parada (máx)", "max_scan_nodes", 1, 8, 7, fmt="{:.0f}")
        self._slider(c3, "Volver a casa tras N recolecciones", "max_gathers", 0, 120, 120, fmt="{:.0f}")
        self._slider(c3, "Descanso cada (mín) recolecciones", "break_every_min", 5, 80, 75, fmt="{:.0f}")
        self._slider(c3, "Descanso cada (máx) recolecciones", "break_every_max", 10, 120, 110, fmt="{:.0f}")

        self._button(tab, "GUARDAR AJUSTES", self.save_settings, height=40).grid(
            row=2, column=0, columnspan=2, sticky="e", padx=8, pady=(4, 8))

    # ============================ pestaña RUTAS ============================
    def _tab_rutas(self, tab):
        tab.grid_columnconfigure(0, weight=1)
        c = self._card(tab, "Grabar movimiento", col=None)
        ctk.CTkLabel(c, text="Apunta con el ratón dentro del juego y usa los atajos:\n"
                            "F7 = añadir punto de ruta      F8 = capturar imagen de nodo/herramienta",
                     text_color=TXT_DIM, justify="left", font=ctk.CTkFont(FONT, 12)).pack(anchor="w", pady=(0, 10))

        self.target_seg = ctk.CTkSegmentedButton(
            c, values=["gather_route", "town_route", "repair_route"],
            command=self.recorder.set_target, fg_color=PANEL_2, selected_color=ACCENT,
            selected_hover_color=ACCENT_D, unselected_color=PANEL_2, unselected_hover_color=BORDER,
            text_color=TXT, font=ctk.CTkFont(FONT, 12, "bold"))
        self.target_seg.set("gather_route")
        self.target_seg.pack(fill="x", pady=5)

        self.type_seg = ctk.CTkSegmentedButton(
            c, values=["minimap", "screen"], command=self.recorder.set_type,
            fg_color=PANEL_2, selected_color=ACCENT, selected_hover_color=ACCENT_D,
            unselected_color=PANEL_2, unselected_hover_color=BORDER,
            text_color=TXT, font=ctk.CTkFont(FONT, 12, "bold"))
        self.type_seg.set("minimap")
        self.type_seg.pack(fill="x", pady=5)

        row = ctk.CTkFrame(c, fg_color="transparent")
        row.pack(fill="x", pady=8)
        ctk.CTkLabel(row, text="Nombre de plantilla", text_color=TXT_DIM,
                     font=ctk.CTkFont(FONT, 12)).pack(side="left")
        self.tpl_entry = ctk.CTkEntry(row, fg_color=PANEL_2, border_color=BORDER, text_color=TXT,
                                      placeholder_text="mineral / broken / ...")
        self.tpl_entry.insert(0, "mineral")
        self.tpl_entry.pack(side="left", fill="x", expand=True, padx=10)
        self.tpl_entry.bind("<KeyRelease>",
                            lambda e: self.recorder.set_tpl_name(self.tpl_entry.get()))

        self.arm_btn = self._button(c, "ARMAR GRABADOR  (F7 / F8)", self.toggle_recorder, height=40)
        self.arm_btn.pack(fill="x", pady=(6, 4))

        self.counts_lbl = ctk.CTkLabel(c, text="", text_color=TXT_DIM, justify="left",
                                       font=ctk.CTkFont(FONT, 12))
        self.counts_lbl.pack(anchor="w", pady=4)
        self._refresh_counts()

        clr = ctk.CTkFrame(c, fg_color="transparent")
        clr.pack(fill="x", pady=(4, 0))
        labels = {"gather_route": "recolección", "town_route": "ciudad", "repair_route": "reparación"}
        for name in ("gather_route", "town_route", "repair_route"):
            ctk.CTkButton(clr, text=f"Borrar {labels[name]}", width=120, height=32,
                          corner_radius=8, fg_color="#3a2323", hover_color="#4a2c2c",
                          text_color="#e6b8b8", font=ctk.CTkFont(FONT, 12, "bold"),
                          command=lambda n=name: self.clear_route(n)).pack(side="left", padx=4)

    # ============================ pestaña CONTROL ============================
    def _tab_control(self, tab):
        tab.grid_columnconfigure(0, weight=1)
        c = self._card(tab, "Control", col=None)
        self.start_btn = ctk.CTkButton(c, text="INICIAR", height=76, corner_radius=12,
                                       fg_color=ACCENT, hover_color=ACCENT_D, text_color="#141418",
                                       font=ctk.CTkFont(FONT, 24, "bold"), command=self.toggle_bot)
        self.start_btn.pack(fill="x", pady=(6, 12))
        ctk.CTkLabel(c, text="Ten el juego en tu MONITOR PRINCIPAL y no muevas la cámara "
                            "mientras farmea.\nParada de emergencia: pulsa INICIAR otra vez.",
                     text_color=TXT_DIM, justify="center", font=ctk.CTkFont(FONT, 12),
                     wraplength=560).pack(pady=4)

    def _build_log(self):
        wrap = ctk.CTkFrame(self, fg_color=PANEL, corner_radius=12,
                            border_width=1, border_color=BORDER)
        wrap.pack(fill="both", expand=False, padx=16, pady=(0, 14))
        head = ctk.CTkFrame(wrap, fg_color="transparent")
        head.pack(fill="x", padx=16, pady=(11, 0))
        ctk.CTkFrame(head, fg_color=ACCENT, width=3, height=14, corner_radius=2).pack(side="left")
        ctk.CTkLabel(head, text="REGISTRO", text_color=ACCENT,
                     font=ctk.CTkFont(FONT, 12, "bold")).pack(side="left", padx=(9, 0))
        self.log_box = ctk.CTkTextbox(wrap, height=132, fg_color=PANEL_2, text_color="#c9c9d6",
                                      border_width=0, wrap="word", font=ctk.CTkFont("Consolas", 12))
        self.log_box.pack(fill="both", expand=True, padx=14, pady=12)
        self.log_box.configure(state="disabled")

    # ============================ acciones ============================
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
            self.arm_btn.configure(text="ARMAR GRABADOR  (F7 / F8)", fg_color=ACCENT)
        else:
            self.recorder.set_tpl_name(self.tpl_entry.get())
            self.recorder.start()
            self.arm_btn.configure(text="GRABADOR ARMADO — pulsa para desarmar", fg_color="#c08a1f")
        self._refresh_counts()

    def clear_route(self, name):
        self.cfg[name] = []
        C.save(self.cfg)
        self.log(f"borrada la ruta {name}")
        self._refresh_counts()

    def _refresh_counts(self):
        self.counts_lbl.configure(
            text=(f"recolección: {len(self.cfg['gather_route'])} pts    "
                  f"ciudad: {len(self.cfg['town_route'])} pts    "
                  f"reparación: {len(self.cfg['repair_route'])} pts"))
        self.after(1200, self._refresh_counts)

    def toggle_bot(self):
        if self.engine.running():
            self.engine.stop()
            self.start_btn.configure(text="INICIAR", fg_color=ACCENT)
        else:
            self.save_settings()
            self.engine.start()
            self.start_btn.configure(text="DETENER", fg_color=DANGER, hover_color="#c74a4a")

    # ============================ callbacks ============================
    def log(self, msg):
        def _append():
            self.log_box.configure(state="normal")
            self.log_box.insert("end", msg + "\n")
            self.log_box.see("end")
            self.log_box.configure(state="disabled")
        self.after(0, _append)

    def set_status(self, text):
        color = ACCENT if text != C.STATUS_IDLE else TXT_DIM
        self.after(0, lambda: self.status_lbl.configure(text="●  " + text, text_color=color))
        if text == C.STATUS_IDLE:
            self.after(0, lambda: self.start_btn.configure(text="INICIAR", fg_color=ACCENT))

    def _on_close(self):
        self.engine.stop()
        self.recorder.stop()
        self.destroy()


if __name__ == "__main__":
    App().mainloop()
