"""
Phosphor Icons — Font-Registrierung und Icon-Lookup für PyObjC/AppKit.

Verwendung:
    import phosphor_icons
    phosphor_icons.register()          # einmalig beim App-Start
    char = phosphor_icons.char("house")
    font = phosphor_icons.font(size=20, weight="regular")
"""

import os

from CoreText import CTFontManagerRegisterFontsForURL
from Foundation import NSURL

from AppKit import NSFont

from _phosphor_map import ICONS

# PostScript-Name je Gewicht
_FONT_NAMES = {
    "regular": "Phosphor",
    "bold":    "Phosphor-Bold",
    "fill":    "Phosphor-Fill",
}

_FONTS_DIR = os.path.join(os.path.dirname(__file__), "assets", "fonts")

_FONT_FILES = {
    "regular": os.path.join(_FONTS_DIR, "Phosphor.ttf"),
    "bold":    os.path.join(_FONTS_DIR, "Phosphor-Bold.ttf"),
    "fill":    os.path.join(_FONTS_DIR, "Phosphor-Fill.ttf"),
}

_registered = False


def register():
    """Registriert alle Phosphor-Fonts für den aktuellen Prozess.
    Muss einmalig vor der ersten Verwendung aufgerufen werden.
    """
    global _registered
    if _registered:
        return
    for weight, path in _FONT_FILES.items():
        if os.path.exists(path):
            url = NSURL.fileURLWithPath_(path)
            CTFontManagerRegisterFontsForURL(url, 1, None)  # scope = process
        else:
            print(f"[phosphor_icons] Font nicht gefunden: {path}")
    _registered = True


def char(name: str) -> str:
    """Gibt das Unicode-Zeichen für ein Icon zurück.

    Beispiel: char("house") → '\ue22a'
    Gibt '?' zurück wenn das Icon unbekannt ist.
    """
    return ICONS.get(name.lower().replace("_", "-"), "?")


def font(size: float = 20.0, weight: str = "regular") -> NSFont:
    """Gibt einen NSFont für das gewünschte Gewicht und die Größe zurück.

    weight: 'regular' | 'bold' | 'fill'
    """
    ps_name = _FONT_NAMES.get(weight.lower(), "Phosphor")
    f = NSFont.fontWithName_size_(ps_name, size)
    if f is None:
        register()
        f = NSFont.fontWithName_size_(ps_name, size)
    return f or NSFont.systemFontOfSize_(size)


def all_icons() -> list:
    """Gibt alle verfügbaren Icon-Namen zurück (alphabetisch)."""
    return sorted(ICONS.keys())
