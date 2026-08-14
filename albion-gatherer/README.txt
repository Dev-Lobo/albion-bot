Albion Gatherer — screen-vision gathering bot (Linux / X11)
===========================================================

INSTALL (one command, from inside this folder)
    bash install.sh

RUN
    albion-gatherer
    (or directly: ~/.local/share/albion-gatherer/.venv/bin/python app.py)

HOW IT WORKS
------------
This is a screen-vision bot: it reads pixels with mss + OpenCV and clicks with
pynput. It does NOT read game memory. That means it needs a short one-time
calibration on YOUR resolution/UI before it can farm — nobody can pre-bake that.

FIRST-RUN CALIBRATION (5 minutes)
1. Setup tab: pick your home city, tick the resources you want, save.
2. Routes tab -> "Arm recorder".
   - Target "gather_route", type "minimap": in-game, hover your mouse over
     points on the MINIMAP tracing your farming loop, press F7 at each.
     (Minimap clicks map to fixed local world points — far more reliable than
     clicking the moving 3D world.)
   - Target "town_route": trace the minimap path back to your city, F7 each.
   - Optional "repair_route", type "screen": F7 on the repair/bank NPC + menu
     buttons you click once home.
   - Node images: set template name (e.g. "ore"), hover a resource node on
     screen and press F8. Grab 2-3 angles. For tool-break detection, name a
     template "broken" and F8 the worn-tool / "tools destroyed" icon.
   - Disarm the recorder.
3. Control tab -> START. Press START again to stop instantly.

TUNING
- Match confidence too high = misses nodes; too low = false clicks. 0.72-0.80 start.
- "Return home after N gathers" is a safety fallback if no "broken" template matches.

NOTES / LIMITS (read these)
- X11 only. On Wayland, pynput cannot inject input — use an Xorg login session.
- Keep the game on your PRIMARY monitor and keep the camera steady while farming.
- Templates are resolution/zoom specific. Re-capture if you change either.
- This automates a live game client and violates Albion Online's Terms of
  Service; using it can get the account banned. That is your call to make.

FILES
- app.py               GUI (customtkinter)
- engine.py            gathering state machine (thread)
- vision.py            screen capture + template matching (mss + OpenCV)
- input_controller.py  humanized mouse control (pynput)
- recorder.py          F7/F8 global-hotkey waypoint + template recorder
- config.py            JSON config load/save (~/.config/albion-gatherer/)
- install.sh           one-command installer
