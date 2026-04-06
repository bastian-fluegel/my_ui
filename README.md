# Native macOS GUI — Python + XML

Echte macOS-Oberfläche mit `PyObjC` (`AppKit`), deklarativ per XML beschrieben.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

---

## Alle unterstützten XML-Elemente

### Text / Eingabe

```xml
<label       id="x" ... text="Text" fontSize="13" />
<textfield   id="x" ... placeholder="..." tooltip="..." />
<textarea    id="x" ... />
<searchfield id="x" ... placeholder="Suchen…" />
<combobox    id="x" ... placeholder="..." items="A,B,C" />
<tokenfield  id="x" ... placeholder="Tags..." />
```

### Buttons / Toggles

```xml
<button      id="x" ... text="Klick" action="my_action" tooltip="..." />
<checkbox    id="x" ... text="Option" checked="true"  action="..." />
<radio       id="x" ... text="Wahl"   checked="false" action="..." />
<switch      id="x" ... on="true"                     action="..." />
<colorwell   id="x" ... color="blue"                  action="..." />
```

### Auswahl

```xml
<slider      id="x" ... min="0" max="100" value="50"  action="..." />
<stepper     id="x" ... min="0" max="10"  value="1" increment="1" />
<dropdown    id="x" ... items="A,B,C" selected="0"    action="..." />
<segmented   id="x" ... items="X,Y,Z" selected="0"    action="..." />
<datepicker  id="x" ... style="text|stepper|calendar|textonly" />
```

### Indikatoren

```xml
<progressbar id="x" ... min="0" max="100" value="40" indeterminate="false" />
<spinner     id="x" ... spinning="true" />
<separator   id="x" ... />
<image       id="x" ... src="star.fill" />   <!-- SF Symbols -->

<!-- Phosphor Icons — 1530 Icons, 3 Gewichte -->
<icon id="x" left="30" top="30" width="28" height="28"
      name="house"
      weight="regular|bold|fill"
      size="24"
      color="label|secondary|accent|red|green|blue|orange|white" />
```

Alle Icon-Namen: [phosphoricons.com](https://phosphoricons.com)

```python
# Direkter Zugriff aus Python
import phosphor_icons
glyph = phosphor_icons.char("house")      # Unicode-Zeichen
font  = phosphor_icons.font(24, "fill")   # NSFont
icons = phosphor_icons.all_icons()        # Liste aller 1530 Namen
```

### Container (unterstützen verschachtelte Elemente)

```xml
<card id="x" left="30" right="30" top="100" height="120">
    <label  id="card_title" left="12" top="10" ... />
    <button id="card_btn"   left="12" top="40" ... />
</card>

<tabs id="x" left="30" right="30" top="200" height="200">
    <tab title="Tab 1">
        <label id="t1_label" left="10" top="10" ... />
    </tab>
    <tab title="Tab 2">
        <button id="t2_btn"  left="10" top="10" ... />
    </tab>
</tabs>
```

---

## Responsive Layout

| Attribut | Bedeutung |
|---|---|
| `left` | Abstand links |
| `right` | Abstand rechts |
| `top` | Abstand oben |
| `bottom` | Abstand unten |
| `width` / `height` | Feste Größe (optional wenn beide Seiten gesetzt) |
| `x` / `y` | Fixe Koordinate (Fallback) |
| `tooltip` | Tooltip-Text (auf jedem Element) |

- `left` + `right` → Breite wächst mit Fenster
- `top` + `bottom` → Höhe wächst mit Fenster
- `right` + `bottom` → rechts/unten verankert

---

## Python API

```python
builder = XMLUIBuilder("ui.xml", logic=UILogic())
window  = builder.build_window()

# Rohes NSView-Objekt
view = builder.get_view("id")

# Text  (label, textfield, textarea, combobox, searchfield, button, dropdown)
builder.get_text("id")
builder.set_text("id", "Neuer Text")

# Numerischer Wert  (slider, stepper, progressbar)
builder.get_value("id")            # → float
builder.set_value("id", 75.0)

# Boolean-Zustand  (checkbox, radio, switch)
builder.get_state("id")            # → bool
builder.set_state("id", True)

# Auswahl-Index  (dropdown, segmented)
builder.get_selected("id")         # → int
builder.set_selected("id", 2)

# Farbe  (colorwell)
builder.get_color("id")            # → NSColor
builder.set_color("id", NSColor.redColor())

# Datum  (datepicker)
builder.get_date("id")             # → NSDate
builder.set_date("id", ns_date)

# Spinner
builder.start_spinner("id")
builder.stop_spinner("id")
```

---

## Actions (ui_logic.py)

```python
class UILogic:
    def resolve(self, action_name, ui):
        return {
            "my_action": lambda: self.my_action(ui),
            "quit_app":  lambda: self.quit_app(),
        }.get(action_name, lambda: print(f"Unknown: {action_name}"))

    def my_action(self, ui):
        name = ui.get_text("name_input")
        ui.set_text("title_label", f"Hallo, {name}!")

    def quit_app(self):
        from AppKit import NSApp
        NSApp.terminate_(None)
```

---

### Custom / Compound Elements

```xml
<!-- Badge: farbige Zahl-Pille -->
<badge id="x" left="30" top="30" width="24" height="18" text="3" color="red" />

<!-- Breadcrumbs: Navigations-Pfad -->
<breadcrumbs id="x" left="30" top="30" width="320" height="20"
             items="Home,Kategorie,Seite" selected="2" />

<!-- FAB: schwebender Rund-Button mit SF Symbol -->
<fab id="x" right="24" bottom="66" size="52" src="plus" action="my_action" tooltip="..." />

<!-- Carousel: horizontal scrollbar mit Slides -->
<carousel id="x" left="30" right="30" top="100" height="160">
    <slide id="slide_1">
        <label id="s1_title" left="12" top="10" width="200" height="20" text="Slide 1" />
    </slide>
    <slide id="slide_2">
        <label id="s2_title" left="12" top="10" width="200" height="20" text="Slide 2" />
    </slide>
</carousel>
```

```python
# Toast / Snackbar (programmatisch)
builder.show_toast("Gespeichert!", duration=3.0)

# Popover (programmatisch, anchor = beliebiges Element-ID)
builder.show_popover("button_id", "Info-Text hier.", width=240, height=80)
```

---

## Nicht in der Liste (bewusst weggelassen)

Diese Elemente sind **kein nativer macOS-Standard** und würden Custom Drawing benötigen:

- Knob / Virtual Knob
- Pie / Radial Menu
- FAB (Floating Action Button)
- Carousel / Lightbox
- Ribbon
- Toast / Snackbar (wäre ein eigenes floating NSPanel)
- 2D Matrix / Wheel Picker
- Megamenu / Breadcrumbs (nicht macOS-Paradigma)
