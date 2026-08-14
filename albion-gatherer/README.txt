Albion Gatherer — bot de recolección por visión de pantalla (Linux / X11)
=========================================================================

INSTALACIÓN (un solo comando, desde dentro de esta carpeta)
    bash install.sh

EJECUTAR
    albion-gatherer
    (o directamente: ~/.local/share/albion-gatherer/.venv/bin/python app.py)

CÓMO FUNCIONA
-------------
Es un bot de visión de pantalla: lee píxeles con mss + OpenCV y hace clic con
pynput. NO lee la memoria del juego. Eso significa que necesita una calibración
breve, una sola vez, en TU resolución/interfaz antes de poder farmear — nadie
puede dejarla preparada de antemano.

QUÉ LO HACE "INTELIGENTE"
-------------------------
- Escaneo inteligente: en cada parada ve TODOS los nodos visibles (no solo el
  mejor) y farmea varios, empezando por el más cercano al cursor.
- Recolección adaptativa: detecta cuándo el nodo DESAPARECE (recolección real
  terminada) en vez de esperar un tiempo fijo -> más rápido y más fiable.
- Confianza adaptativa: si lleva rato sin ver nada baja el umbral, y lo sube de
  nuevo al acertar -> se autocalibra sobre la marcha.
- Humanización: ruido gaussiano en los tiempos, cursor que se mueve en curva con
  pequeñas correcciones, y descansos tipo humano cada cierto número aleatorio de
  recolecciones.
Todo esto se enciende/apaga desde la pestaña Ajustes.

CALIBRACIÓN DEL PRIMER USO (5 minutos)
1. Pestaña Ajustes: elige tu ciudad de origen, marca los recursos que quieras,
   ajusta la inteligencia y guarda.
2. Pestaña Rutas -> "Armar grabador".
   - Objetivo "gather_route", tipo "minimap": dentro del juego, pasa el ratón
     por puntos del MINIMAPA trazando tu bucle de farmeo y pulsa F7 en cada uno.
     (Los clics en el minimapa apuntan a puntos fijos del mundo local — mucho
     más fiable que clicar el mundo 3D en movimiento.)
   - Objetivo "town_route", tipo "minimap": traza en el minimapa el camino de
     vuelta a tu ciudad, F7 en cada punto.
   - "repair_route" opcional, tipo "screen": F7 sobre el NPC de reparación/banco
     y los botones del menú que pulsas al llegar a casa.
   - Imágenes de nodos: pon un nombre de plantilla (p. ej. "mineral"), pasa el
     ratón sobre un nodo de recurso en pantalla y pulsa F8. Captura 2-3 ángulos.
     Para detectar herramienta rota, nombra una plantilla "broken" y pulsa F8
     sobre el icono de herramienta gastada / "herramientas destruidas".
   - Desarma el grabador.
3. Pestaña Control -> INICIAR. Pulsa INICIAR otra vez para detener al instante.

AJUSTE FINO
- Confianza demasiado alta = se salta nodos; demasiado baja = clics falsos.
  Empieza entre 0.72 y 0.80 (con la confianza adaptativa puedes empezar un poco
  más alto y dejar que baje sola).
- "Techo de recolección" es el tiempo MÁXIMO por nodo; con recolección adaptativa
  normalmente terminará antes.
- "Volver a casa tras N recolecciones" es el tope de seguridad si ninguna
  plantilla "broken" coincide.
- "Nodos por parada" limita cuántos nodos farmea antes de avanzar a la siguiente
  parada de la ruta.

NOTAS / LÍMITES (léelos)
- Solo X11. En Wayland, pynput no puede inyectar entradas — usa una sesión Xorg.
- Mantén el juego en tu monitor PRINCIPAL y la cámara quieta mientras farmeas.
- Las plantillas dependen de la resolución/zoom. Vuelve a capturarlas si cambias
  cualquiera de las dos.
- Esto automatiza un cliente de juego en vivo y viola los Términos de Servicio de
  Albion Online; usarlo puede acarrear el baneo de la cuenta. Esa decisión es tuya.

ARCHIVOS
- app.py               Interfaz gráfica (customtkinter)
- engine.py            Máquina de estados de recolección con la lógica inteligente (hilo)
- vision.py            Captura de pantalla + coincidencia de plantillas (mss + OpenCV)
- input_controller.py  Control humanizado del ratón (pynput)
- recorder.py          Grabador de puntos y plantillas por atajos globales F7/F8
- config.py            Carga/guardado de configuración JSON (~/.config/albion-gatherer/)
- install.sh           Instalador de un solo comando
