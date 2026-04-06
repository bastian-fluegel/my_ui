import os
import warnings
import xml.etree.ElementTree as ET

import objc

from AppKit import (
    NSBackingStoreBuffered,
    NSBezierPath,
    NSBox,
    NSButton,
    NSColor,
    NSColorWell,
    NSComboBox,
    NSCursor,
    NSDatePicker,
    NSFloatingWindowLevel,
    NSFont,
    NSImage,
    NSImageView,
    NSImageScaleProportionallyUpOrDown,
    NSPanel,
    NSPopover,
    NSPopUpButton,
    NSProgressIndicator,
    NSScrollView,
    NSSearchField,
    NSSegmentedControl,
    NSSlider,
    NSStepper,
    NSTabView,
    NSTabViewItem,
    NSTextField,
    NSTextView,
    NSTokenField,
    NSTrackingActiveAlways,
    NSTrackingInVisibleRect,
    NSTrackingMouseEnteredAndExited,
    NSTrackingArea,
    NSView,
    NSViewController,
    NSViewHeightSizable,
    NSViewMaxXMargin,
    NSViewMaxYMargin,
    NSViewMinXMargin,
    NSViewMinYMargin,
    NSViewWidthSizable,
    NSVisualEffectBlendingModeBehindWindow,
    NSVisualEffectMaterialUnderWindowBackground,
    NSVisualEffectStateActive,
    NSVisualEffectStateFollowsWindowActiveState,
    NSVisualEffectView,
    NSWindow,
    NSWindowStyleMaskBorderless,
    NSWindowStyleMaskResizable,
)
from Foundation import NSMakeRect, NSMakeSize, NSObject

import phosphor_icons

try:
    from AppKit import NSSwitch as _NSSwitch
except ImportError:
    _NSSwitch = None

warnings.filterwarnings("ignore", category=objc.ObjCPointerWarning)

# Global highlight / accent color for this app (FF8000).
_HIGHLIGHT_HEX = "D96C00"


def _hex_to_color(hex_str: str, alpha: float = 1.0) -> NSColor:
    s = (hex_str or "").strip().lstrip("#")
    if len(s) == 3:
        s = "".join([c * 2 for c in s])
    if len(s) != 6:
        return NSColor.controlAccentColor()
    r = int(s[0:2], 16) / 255.0
    g = int(s[2:4], 16) / 255.0
    b = int(s[4:6], 16) / 255.0
    return NSColor.colorWithSRGBRed_green_blue_alpha_(r, g, b, float(alpha))


def highlight_color(alpha: float = 1.0) -> NSColor:
    return _hex_to_color(_HIGHLIGHT_HEX, alpha=alpha)


# Numeric constants — robust across PyObjC versions
_BUTTON_TYPE_CHECKBOX      = 3   # NSSwitchButton
_BUTTON_TYPE_RADIO         = 4   # NSRadioButton
_BOX_TYPE_SEPARATOR        = 2   # NSBoxSeparator
_BOX_TYPE_CUSTOM           = 4   # NSBoxCustom
_BORDER_TYPE_BEZEL         = 2   # NSBezelBorder
_BORDER_TYPE_NONE          = 0   # NSNoBorder
_PROGRESS_STYLE_BAR        = 0   # NSProgressIndicatorStyleBar
_PROGRESS_STYLE_SPINNING   = 1   # NSProgressIndicatorStyleSpinning
_TITLE_POSITION_NONE       = 0   # NSNoTitle
_DATEPICKER_STEPPER        = 0   # NSDatePickerStyleTextFieldAndStepper
_DATEPICKER_CALENDAR       = 1   # NSDatePickerStyleClockAndCalendar
_DATEPICKER_TEXT           = 2   # NSDatePickerStyleTextField


def _to_float(value, default=0.0):
    if value is None:
        return default
    return float(value)


def _to_bool(value, default=False):
    if value is None:
        return default
    return str(value).lower() in ("true", "1", "yes")


class AppWindow(NSWindow):
    def canBecomeKeyWindow(self):
        return True

    def canBecomeMainWindow(self):
        return True


class ControlActionHandler(NSObject):
    def initWithCallback_(self, callback):
        self = self.init()
        if self is None:
            return None
        self.callback = callback
        return self

    def onAction_(self, _sender):
        self.callback()


# Backwards-compatible alias
ButtonActionHandler = ControlActionHandler


# ------------------------------------------------------------------
# Custom element classes
# ------------------------------------------------------------------

class _FabView(NSView):
    """Circular Floating Action Button drawn via NSBezierPath."""
    _icon  = None
    _handler = None

    def initWithFrame_icon_handler_(self, frame, icon, handler):
        self = objc.super(_FabView, self).initWithFrame_(frame)
        if self is None:
            return None
        self._icon    = icon
        self._handler = handler
        return self

    def drawRect_(self, rect):
        path = NSBezierPath.bezierPathWithOvalInRect_(self.bounds())
        highlight_color().set()
        path.fill()
        if self._icon:
            s = self.bounds().size
            pad = s.width * 0.25
            self._icon.drawInRect_(NSMakeRect(pad, pad, s.width - pad * 2, s.height - pad * 2))

    def mouseDown_(self, event):
        if self._handler:
            self._handler.onAction_(self)

    def mouseDownCanMoveWindow(self):
        return False

    def isOpaque(self):
        return False


class _IconActionView(NSView):
    _glyph = "?"
    _font = None
    _color = None
    _hover_color = None
    _hover = False
    _handler = None
    _tracking = None

    def initWithFrame_glyph_font_color_hoverColor_handler_(
        self, frame, glyph, font, color, hover_color, handler
    ):
        self = objc.super(_IconActionView, self).initWithFrame_(frame)
        if self is None:
            return None
        self._glyph = glyph
        self._font = font
        self._color = color
        self._hover_color = hover_color
        self._handler = handler
        self.setWantsLayer_(True)
        return self

    def setBaseColor_(self, color):
        self._color = color
        self.setNeedsDisplay_(True)

    def updateTrackingAreas(self):
        if self._tracking is not None:
            self.removeTrackingArea_(self._tracking)
            self._tracking = None
        opts = (
            NSTrackingMouseEnteredAndExited
            | NSTrackingActiveAlways
            | NSTrackingInVisibleRect
        )
        self._tracking = NSTrackingArea.alloc().initWithRect_options_owner_userInfo_(
            self.bounds(), opts, self, None
        )
        self.addTrackingArea_(self._tracking)
        objc.super(_IconActionView, self).updateTrackingAreas()

    def mouseEntered_(self, _event):
        self._hover = True
        NSCursor.pointingHandCursor().set()
        self.setNeedsDisplay_(True)

    def mouseExited_(self, _event):
        self._hover = False
        NSCursor.arrowCursor().set()
        self.setNeedsDisplay_(True)

    def mouseDown_(self, _event):
        if self._handler:
            self._handler.onAction_(self)

    def mouseDownCanMoveWindow(self):
        return False

    def drawRect_(self, rect):
        (self._hover_color if (self._hover and self._hover_color) else self._color).set()
        attrs = {  # NSStringDrawing / NSAttributedString attributes
            "NSFont": self._font,
            "NSColor": (self._hover_color if (self._hover and self._hover_color) else self._color),
        }
        # Use attributed string drawing via NSString API
        from Foundation import NSString

        s = NSString.stringWithString_(self._glyph)
        size = s.sizeWithAttributes_(attrs)
        b = self.bounds()
        x = (b.size.width - size.width) / 2.0
        y = (b.size.height - size.height) / 2.0
        s.drawAtPoint_withAttributes_((x, y), attrs)

    def isOpaque(self):
        return False


class _DimOverlay(NSView):
    """Halbtransparentes Abdunkel-Overlay ohne CGColor."""
    def drawRect_(self, rect):
        NSColor.blackColor().colorWithAlphaComponent_(0.40).set()
        NSBezierPath.fillRect_(self.bounds())

    def mouseDown_(self, _event):
        pass  # Klick auf Overlay absorbieren, kein Drag, kein Pass-Through

    def mouseDownCanMoveWindow(self):
        return False

    def isOpaque(self):
        return False


class _ToastDismisser(NSObject):
    """Closes a Toast panel after a delay."""
    _panel = None

    def initWithPanel_(self, panel):
        self = self.init()
        if self is None:
            return None
        self._panel = panel
        return self

    def dismiss_(self, _sender):
        if self._panel:
            self._panel.close()
            self._panel = None


class _PopoverContentVC(NSViewController):
    """Minimal view-controller for show_popover()."""
    _pop_text   = ""
    _pop_width  = 220
    _pop_height = 80

    def initWithText_width_height_(self, text, width, height):
        self = objc.super(_PopoverContentVC, self).initWithNibName_bundle_(None, None)
        if self is None:
            return None
        self._pop_text   = text
        self._pop_width  = width
        self._pop_height = height
        return self

    def loadView(self):
        w, h = self._pop_width, self._pop_height
        content = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, w, h))
        label = NSTextField.alloc().initWithFrame_(NSMakeRect(14, 14, w - 28, h - 28))
        label.setStringValue_(self._pop_text)
        label.setBezeled_(False)
        label.setDrawsBackground_(False)
        label.setEditable_(False)
        label.setSelectable_(False)
        label.setTextColor_(NSColor.labelColor())
        label.setFont_(NSFont.systemFontOfSize_(13.0))
        label.setWraps_(True)
        content.addSubview_(label)
        self.setView_(content)


class XMLUIBuilder:
    def __init__(self, xml_path, logic=None):
        self.xml_path = xml_path
        self.logic = logic
        self.handlers = []
        self.views_by_id = {}
        self.window = None
        self.container = None
        self._toast_refs   = []   # keep strong refs to _ToastDismisser + NSPanel
        self._popover_refs = []   # keep strong refs to NSPopover + _PopoverContentVC

    # ------------------------------------------------------------------
    # Window
    # ------------------------------------------------------------------

    def build_window(self):
        if not os.path.exists(self.xml_path):
            raise FileNotFoundError(f"UI XML not found: {self.xml_path}")

        tree = ET.parse(self.xml_path)
        root = tree.getroot()
        if root.tag != "window":
            raise ValueError("Root element must be <window>.")

        width  = _to_float(root.get("width"),  800)
        height = _to_float(root.get("height"), 500)
        title  = root.get("title", "Native macOS App")

        style_mask = NSWindowStyleMaskBorderless | NSWindowStyleMaskResizable
        window = AppWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(100.0, 100.0, width, height),
            style_mask,
            NSBackingStoreBuffered,
            False,
        )
        window.setTitle_(title)
        window.setMovableByWindowBackground_(True)
        window.setOpaque_(False)
        window.setBackgroundColor_(NSColor.clearColor())
        window.setHasShadow_(True)

        content_rect = NSMakeRect(0.0, 0.0, width, height)

        container = NSView.alloc().initWithFrame_(content_rect)
        container.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        container.setWantsLayer_(True)
        container.layer().setCornerRadius_(14.0)
        container.layer().setMasksToBounds_(True)

        background = NSVisualEffectView.alloc().initWithFrame_(content_rect)
        background.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        background.setBlendingMode_(NSVisualEffectBlendingModeBehindWindow)
        background.setMaterial_(NSVisualEffectMaterialUnderWindowBackground)
        background.setState_(NSVisualEffectStateFollowsWindowActiveState)
        container.addSubview_(background)

        window.setContentView_(container)

        for child in root:
            view = self._build_view(child, width, height)
            if view is not None:
                container.addSubview_(view)

        self.window = window
        self.container = container
        return window

    # ------------------------------------------------------------------
    # View dispatch
    # ------------------------------------------------------------------

    _BUILDERS = [
        "label", "textfield", "textarea", "button",
        "checkbox", "radio", "switch",
        "slider", "stepper", "colorwell",
        "dropdown", "combobox", "searchfield", "tokenfield",
        "segmented", "datepicker",
        "progressbar", "spinner",
        "separator", "image",
        "tabs", "card",
    ]

    def _build_view(self, node, parent_width, parent_height):
        view_id = node.get("id")
        if not view_id:
            raise ValueError(f"Element <{node.tag}> is missing required attribute 'id'.")

        method = getattr(self, f"_build_{node.tag.lower()}", None)
        if method is None:
            return None

        result = method(node, parent_width, parent_height)
        if result is None:
            return None

        # Builders may return (view_to_add, view_to_register) for wrappers
        if isinstance(result, tuple):
            view_to_add, view_to_register = result
        else:
            view_to_add = view_to_register = result

        self._register_view(view_id, view_to_register)
        self._apply_common_attrs(view_to_add, node)
        return view_to_add

    def _register_view(self, view_id, view):
        if view_id in self.views_by_id:
            raise ValueError(f"Duplicate id found in XML: '{view_id}'")
        self.views_by_id[view_id] = view

    def _apply_common_attrs(self, view, node):
        tooltip = node.get("tooltip")
        if tooltip and hasattr(view, "setToolTip_"):
            view.setToolTip_(tooltip)

        visible_attr = node.get("visible")
        if visible_attr is not None and hasattr(view, "setHidden_"):
            view.setHidden_(not _to_bool(visible_attr, default=True))

    # ------------------------------------------------------------------
    # Layout helpers
    # ------------------------------------------------------------------

    def _layout_from_node(self, node, parent_width, parent_height):
        left   = node.get("left")
        right  = node.get("right")
        top    = node.get("top")
        bottom = node.get("bottom")
        center_x = node.get("centerX")
        center_y = node.get("centerY")

        width_attr  = node.get("width")
        height_attr = node.get("height")

        left_val   = _to_float(left)   if left   is not None else None
        right_val  = _to_float(right)  if right  is not None else None
        top_val    = _to_float(top)    if top    is not None else None
        bottom_val = _to_float(bottom) if bottom is not None else None

        has_width  = width_attr  is not None
        has_height = height_attr is not None
        width_val  = _to_float(width_attr,  200)
        height_val = _to_float(height_attr,  24)

        if left_val is not None and right_val is not None and not has_width:
            width_val = parent_width - left_val - right_val
        if top_val is not None and bottom_val is not None and not has_height:
            height_val = parent_height - top_val - bottom_val

        if center_x is not None and _to_bool(center_x, True):
            x = (parent_width - width_val) / 2.0
        elif left_val is not None:
            x = left_val
        elif right_val is not None:
            x = parent_width - right_val - width_val
        else:
            x = _to_float(node.get("x"), 20)

        if center_y is not None and _to_bool(center_y, True):
            y = (parent_height - height_val) / 2.0
        elif bottom_val is not None:
            y = bottom_val
        elif top_val is not None:
            y = parent_height - top_val - height_val
        else:
            y = _to_float(node.get("y"), 20)

        mask = 0
        if center_x is not None and _to_bool(center_x, True):
            mask |= NSViewMinXMargin | NSViewMaxXMargin
        elif left_val is not None and right_val is not None:
            mask |= NSViewWidthSizable
        elif left_val is not None:
            mask |= NSViewMaxXMargin
        elif right_val is not None:
            mask |= NSViewMinXMargin
        else:
            mask |= NSViewMinXMargin | NSViewMaxXMargin

        if center_y is not None and _to_bool(center_y, True):
            mask |= NSViewMinYMargin | NSViewMaxYMargin
        elif top_val is not None and bottom_val is not None:
            mask |= NSViewHeightSizable
        elif top_val is not None:
            mask |= NSViewMinYMargin
        elif bottom_val is not None:
            mask |= NSViewMaxYMargin
        else:
            mask |= NSViewMinYMargin | NSViewMaxYMargin

        return NSMakeRect(x, y, width_val, height_val), mask

    # ------------------------------------------------------------------
    # Simple container (no border)
    # ------------------------------------------------------------------

    def _build_container(self, node, pw, ph):
        frame, mask = self._layout_from_node(node, pw, ph)
        v = NSView.alloc().initWithFrame_(frame)
        v.setAutoresizingMask_(mask)
        for child in node:
            child_view = self._build_view(child, frame.size.width, frame.size.height)
            if child_view is not None:
                v.addSubview_(child_view)
        return v

    def _name_to_color(self, name):
        return {
            "red":    NSColor.redColor(),
            "green":  NSColor.greenColor(),
            "blue":   NSColor.blueColor(),
            "orange": NSColor.orangeColor(),
            "purple": NSColor.purpleColor(),
            "gray":   NSColor.grayColor(),
            "black":  NSColor.blackColor(),
            "white":  NSColor.whiteColor(),
            "accent": highlight_color(),
        }.get(str(name).lower(), highlight_color())

    def _bind_action(self, control, node):
        action_name = node.get("action")
        if action_name and self.logic is not None:
            callback = self.logic.resolve(action_name, self)
            handler = ControlActionHandler.alloc().initWithCallback_(callback)
            self.handlers.append(handler)
            control.setTarget_(handler)
            control.setAction_("onAction:")

    # ------------------------------------------------------------------
    # Text / Input
    # ------------------------------------------------------------------

    _LABEL_COLORS = {
        "label":     lambda: NSColor.labelColor(),
        "secondary": lambda: NSColor.secondaryLabelColor(),
        "tertiary":  lambda: NSColor.tertiaryLabelColor(),
        "accent":    lambda: highlight_color(),
        "red":       lambda: NSColor.redColor(),
        "green":     lambda: NSColor.greenColor(),
        "blue":      lambda: NSColor.blueColor(),
        "orange":    lambda: NSColor.orangeColor(),
        "white":     lambda: NSColor.whiteColor(),
    }

    def _build_label(self, node, pw, ph):
        frame, mask = self._layout_from_node(node, pw, ph)
        v = NSTextField.alloc().initWithFrame_(frame)
        v.setAutoresizingMask_(mask)
        v.setStringValue_(node.get("text", ""))
        v.setBezeled_(False)
        v.setDrawsBackground_(False)
        v.setEditable_(False)
        v.setSelectable_(False)
        size = _to_float(node.get("fontSize"), 13)
        bold = _to_bool(node.get("bold"))
        v.setFont_(NSFont.boldSystemFontOfSize_(size) if bold else NSFont.systemFontOfSize_(size))
        color_fn = self._LABEL_COLORS.get(node.get("color", "label"), lambda: NSColor.labelColor())
        v.setTextColor_(color_fn())
        return v

    def _build_textfield(self, node, pw, ph):
        frame, mask = self._layout_from_node(node, pw, ph)
        v = NSTextField.alloc().initWithFrame_(frame)
        v.setAutoresizingMask_(mask)
        v.setPlaceholderString_(node.get("placeholder", ""))
        self._bind_action(v, node)
        return v

    def _build_textarea(self, node, pw, ph):
        frame, mask = self._layout_from_node(node, pw, ph)
        scroll = NSScrollView.alloc().initWithFrame_(frame)
        scroll.setAutoresizingMask_(mask)
        scroll.setHasVerticalScroller_(True)
        scroll.setBorderType_(_BORDER_TYPE_BEZEL)
        inner_bounds = scroll.contentView().bounds()
        tv = NSTextView.alloc().initWithFrame_(inner_bounds)
        tv.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        tv.setRichText_(False)
        tv.setDrawsBackground_(False)
        scroll.setDocumentView_(tv)
        return scroll, tv  # register NSTextView, add NSScrollView

    def _build_searchfield(self, node, pw, ph):
        frame, mask = self._layout_from_node(node, pw, ph)
        v = NSSearchField.alloc().initWithFrame_(frame)
        v.setAutoresizingMask_(mask)
        v.setPlaceholderString_(node.get("placeholder", "Suchen…"))
        self._bind_action(v, node)
        return v

    def _build_combobox(self, node, pw, ph):
        frame, mask = self._layout_from_node(node, pw, ph)
        v = NSComboBox.alloc().initWithFrame_(frame)
        v.setAutoresizingMask_(mask)
        v.setPlaceholderString_(node.get("placeholder", ""))
        items_str = node.get("items", "")
        if items_str:
            for item in items_str.split(","):
                v.addItemWithObjectValue_(item.strip())
        self._bind_action(v, node)
        return v

    def _build_tokenfield(self, node, pw, ph):
        frame, mask = self._layout_from_node(node, pw, ph)
        v = NSTokenField.alloc().initWithFrame_(frame)
        v.setAutoresizingMask_(mask)
        v.setPlaceholderString_(node.get("placeholder", ""))
        return v

    # ------------------------------------------------------------------
    # Buttons / Toggles
    # ------------------------------------------------------------------

    def _build_button(self, node, pw, ph):
        frame, mask = self._layout_from_node(node, pw, ph)
        v = NSButton.alloc().initWithFrame_(frame)
        v.setAutoresizingMask_(mask)
        v.setTitle_(node.get("text", "Button"))
        v.setBezelStyle_(1)
        self._bind_action(v, node)
        return v

    def _build_checkbox(self, node, pw, ph):
        frame, mask = self._layout_from_node(node, pw, ph)
        v = NSButton.alloc().initWithFrame_(frame)
        v.setAutoresizingMask_(mask)
        v.setButtonType_(_BUTTON_TYPE_CHECKBOX)
        v.setTitle_(node.get("text", ""))
        v.setState_(1 if _to_bool(node.get("checked")) else 0)
        self._bind_action(v, node)
        return v

    def _build_radio(self, node, pw, ph):
        frame, mask = self._layout_from_node(node, pw, ph)
        v = NSButton.alloc().initWithFrame_(frame)
        v.setAutoresizingMask_(mask)
        v.setButtonType_(_BUTTON_TYPE_RADIO)
        v.setTitle_(node.get("text", ""))
        v.setState_(1 if _to_bool(node.get("checked")) else 0)
        self._bind_action(v, node)
        return v

    def _build_switch(self, node, pw, ph):
        frame, mask = self._layout_from_node(node, pw, ph)
        if _NSSwitch is not None:
            v = _NSSwitch.alloc().initWithFrame_(frame)
            v.setAutoresizingMask_(mask)
            v.setState_(1 if _to_bool(node.get("on")) else 0)
            self._bind_action(v, node)
            return v
        v = NSButton.alloc().initWithFrame_(frame)
        v.setAutoresizingMask_(mask)
        v.setButtonType_(_BUTTON_TYPE_CHECKBOX)
        v.setTitle_(node.get("text", ""))
        v.setState_(1 if _to_bool(node.get("on")) else 0)
        self._bind_action(v, node)
        return v

    def _build_colorwell(self, node, pw, ph):
        frame, mask = self._layout_from_node(node, pw, ph)
        v = NSColorWell.alloc().initWithFrame_(frame)
        v.setAutoresizingMask_(mask)
        color_name = node.get("color", "blue")
        color_map = {
            "red":    NSColor.redColor(),
            "green":  NSColor.greenColor(),
            "blue":   NSColor.blueColor(),
            "black":  NSColor.blackColor(),
            "white":  NSColor.whiteColor(),
            "gray":   NSColor.grayColor(),
            "orange": NSColor.orangeColor(),
            "purple": NSColor.purpleColor(),
        }
        v.setColor_(color_map.get(color_name, NSColor.blueColor()))
        self._bind_action(v, node)
        return v

    # ------------------------------------------------------------------
    # Selection
    # ------------------------------------------------------------------

    def _build_slider(self, node, pw, ph):
        frame, mask = self._layout_from_node(node, pw, ph)
        v = NSSlider.alloc().initWithFrame_(frame)
        v.setAutoresizingMask_(mask)
        v.setMinValue_(_to_float(node.get("min"),    0))
        v.setMaxValue_(_to_float(node.get("max"),  100))
        v.setDoubleValue_(_to_float(node.get("value"), 50))
        self._bind_action(v, node)
        return v

    def _build_stepper(self, node, pw, ph):
        frame, mask = self._layout_from_node(node, pw, ph)
        v = NSStepper.alloc().initWithFrame_(frame)
        v.setAutoresizingMask_(mask)
        v.setMinValue_(_to_float(node.get("min"),   0))
        v.setMaxValue_(_to_float(node.get("max"), 100))
        v.setIncrement_(_to_float(node.get("increment"), 1))
        v.setDoubleValue_(_to_float(node.get("value"), 0))
        self._bind_action(v, node)
        return v

    def _build_dropdown(self, node, pw, ph):
        frame, mask = self._layout_from_node(node, pw, ph)
        v = NSPopUpButton.alloc().initWithFrame_(frame)
        v.setAutoresizingMask_(mask)
        items_str = node.get("items", "")
        if items_str:
            for item in items_str.split(","):
                v.addItemWithTitle_(item.strip())
        selected = node.get("selected")
        if selected is not None:
            v.selectItemAtIndex_(int(selected))
        self._bind_action(v, node)
        return v

    def _build_segmented(self, node, pw, ph):
        frame, mask = self._layout_from_node(node, pw, ph)
        v = NSSegmentedControl.alloc().initWithFrame_(frame)
        v.setAutoresizingMask_(mask)
        items = [i.strip() for i in node.get("items", "").split(",") if i.strip()]
        v.setSegmentCount_(len(items))
        for i, label in enumerate(items):
            v.setLabel_forSegment_(label, i)
        v.setSelectedSegment_(int(node.get("selected", "0")))
        self._bind_action(v, node)
        return v

    def _build_datepicker(self, node, pw, ph):
        frame, mask = self._layout_from_node(node, pw, ph)
        v = NSDatePicker.alloc().initWithFrame_(frame)
        v.setAutoresizingMask_(mask)
        style_map = {
            "text":     _DATEPICKER_STEPPER,
            "stepper":  _DATEPICKER_STEPPER,
            "calendar": _DATEPICKER_CALENDAR,
            "textonly": _DATEPICKER_TEXT,
        }
        v.setDatePickerStyle_(style_map.get(node.get("style", "text"), _DATEPICKER_STEPPER))
        self._bind_action(v, node)
        return v

    # ------------------------------------------------------------------
    # Indicators
    # ------------------------------------------------------------------

    def _build_progressbar(self, node, pw, ph):
        frame, mask = self._layout_from_node(node, pw, ph)
        v = NSProgressIndicator.alloc().initWithFrame_(frame)
        v.setAutoresizingMask_(mask)
        v.setStyle_(_PROGRESS_STYLE_BAR)
        v.setMinValue_(_to_float(node.get("min"),   0))
        v.setMaxValue_(_to_float(node.get("max"), 100))
        v.setDoubleValue_(_to_float(node.get("value"), 0))
        v.setIndeterminate_(_to_bool(node.get("indeterminate")))
        return v

    def _build_spinner(self, node, pw, ph):
        frame, mask = self._layout_from_node(node, pw, ph)
        v = NSProgressIndicator.alloc().initWithFrame_(frame)
        v.setAutoresizingMask_(mask)
        v.setStyle_(_PROGRESS_STYLE_SPINNING)
        v.setIndeterminate_(True)
        if _to_bool(node.get("spinning", "true")):
            v.startAnimation_(None)
        return v

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    def _build_separator(self, node, pw, ph):
        frame, mask = self._layout_from_node(node, pw, ph)
        v = NSBox.alloc().initWithFrame_(frame)
        v.setAutoresizingMask_(mask)
        v.setBoxType_(_BOX_TYPE_SEPARATOR)
        return v

    def _build_image(self, node, pw, ph):
        frame, mask = self._layout_from_node(node, pw, ph)
        v = NSImageView.alloc().initWithFrame_(frame)
        v.setAutoresizingMask_(mask)
        src = node.get("src", "")
        if src:
            img = NSImage.imageWithSystemSymbolName_accessibilityDescription_(src, None)
            if img is None:
                img = NSImage.imageNamed_(src)
            if img is not None:
                v.setImage_(img)
        v.setImageScaling_(NSImageScaleProportionallyUpOrDown)
        return v

    def _build_icon(self, node, pw, ph):
        """Phosphor Icon.

        XML-Attribute:
          name   — Icon-Name aus phosphoricons.com  (z.B. "house", "star", "gear")
          size   — Schriftgröße in pt               (default: 24)
          weight — regular | bold | fill            (default: regular)
          color  — label | secondary | accent | ... (default: label)
          hoverColor — optionaler Hover-Farbname (nur wenn action gesetzt ist)
          action — wenn gesetzt: hover + klickbar
        """
        frame, mask = self._layout_from_node(node, pw, ph)

        name   = node.get("name", "question")
        size   = _to_float(node.get("size"), 24)
        weight = node.get("weight", "regular")

        glyph = phosphor_icons.char(name)
        pfont = phosphor_icons.font(size=size, weight=weight)

        color_name = node.get("color", "label")
        color_map = {
            "label":     NSColor.labelColor(),
            "secondary": NSColor.secondaryLabelColor(),
            "tertiary":  NSColor.tertiaryLabelColor(),
            "accent":    highlight_color(),
            "red":       NSColor.redColor(),
            "green":     NSColor.greenColor(),
            "blue":      NSColor.blueColor(),
            "orange":    NSColor.orangeColor(),
            "white":     NSColor.whiteColor(),
        }
        base_color = color_map.get(color_name, NSColor.labelColor())

        action_name = node.get("action")
        if action_name and self.logic is not None:
            hover_name = node.get("hoverColor")
            hover_color = color_map.get(hover_name, None) if hover_name else None
            callback = self.logic.resolve(action_name, self)
            handler = ControlActionHandler.alloc().initWithCallback_(callback)
            self.handlers.append(handler)
            v = _IconActionView.alloc().initWithFrame_glyph_font_color_hoverColor_handler_(
                frame, glyph, pfont, base_color, hover_color, handler
            )
            v.setAutoresizingMask_(mask)
            return v

        # Dekorativ (nicht klickbar)
        lbl = NSTextField.alloc().initWithFrame_(frame)
        lbl.setAutoresizingMask_(mask)
        lbl.setStringValue_(glyph)
        lbl.setFont_(pfont)
        lbl.setBezeled_(False)
        lbl.setDrawsBackground_(False)
        lbl.setEditable_(False)
        lbl.setSelectable_(False)
        lbl.setAlignment_(1)  # NSTextAlignmentCenter
        lbl.setTextColor_(base_color)
        return lbl

    # ------------------------------------------------------------------
    # Container elements (support nested children)
    # ------------------------------------------------------------------

    def _build_card(self, node, pw, ph):
        frame, mask = self._layout_from_node(node, pw, ph)
        box = NSBox.alloc().initWithFrame_(frame)
        box.setAutoresizingMask_(mask)
        box.setBoxType_(_BOX_TYPE_CUSTOM)
        box.setTitle_("")
        box.setTitlePosition_(_TITLE_POSITION_NONE)
        box.setFillColor_(NSColor.windowBackgroundColor())
        box.setBorderColor_(NSColor.separatorColor())
        box.setBorderWidth_(1.0)
        box.setCornerRadius_(8.0)

        # Build children inside the card's content view
        inner_w = frame.size.width  - 10
        inner_h = frame.size.height - 10
        for child in node:
            child_view = self._build_view(child, inner_w, inner_h)
            if child_view is not None:
                box.contentView().addSubview_(child_view)
        return box

    # ------------------------------------------------------------------
    # Custom / compound elements
    # ------------------------------------------------------------------

    def _build_badge(self, node, pw, ph):
        """Colored pill with a number/text — e.g. notification count."""
        frame, mask = self._layout_from_node(node, pw, ph)
        container = NSView.alloc().initWithFrame_(frame)
        container.setAutoresizingMask_(mask)

        bg = NSBox.alloc().initWithFrame_(NSMakeRect(0, 0, frame.size.width, frame.size.height))
        bg.setBoxType_(_BOX_TYPE_CUSTOM)
        bg.setTitle_("")
        bg.setTitlePosition_(_TITLE_POSITION_NONE)
        bg.setFillColor_(self._name_to_color(node.get("color", "red")))
        bg.setBorderWidth_(0.0)
        bg.setCornerRadius_(frame.size.height / 2.0)
        container.addSubview_(bg)

        lbl = NSTextField.alloc().initWithFrame_(
            NSMakeRect(2, 0, frame.size.width - 4, frame.size.height)
        )
        lbl.setStringValue_(node.get("text", "0"))
        lbl.setBezeled_(False)
        lbl.setDrawsBackground_(False)
        lbl.setEditable_(False)
        lbl.setSelectable_(False)
        lbl.setTextColor_(NSColor.whiteColor())
        lbl.setFont_(NSFont.boldSystemFontOfSize_(11.0))
        lbl.setAlignment_(1)  # NSTextAlignmentCenter
        container.addSubview_(lbl)
        return container

    def _build_breadcrumbs(self, node, pw, ph):
        """Horizontal nav trail: Home › Category › Page."""
        frame, mask = self._layout_from_node(node, pw, ph)
        container = NSView.alloc().initWithFrame_(frame)
        container.setAutoresizingMask_(mask)

        items    = [i.strip() for i in node.get("items", "").split(",") if i.strip()]
        selected = int(node.get("selected", str(len(items) - 1)))
        h        = frame.size.height
        x        = 0.0

        for i, text in enumerate(items):
            item_w = max(len(text) * 7.5 + 10, 32)
            lbl = NSTextField.alloc().initWithFrame_(NSMakeRect(x, 0, item_w, h))
            lbl.setStringValue_(text)
            lbl.setBezeled_(False)
            lbl.setDrawsBackground_(False)
            lbl.setEditable_(False)
            lbl.setSelectable_(False)
            lbl.setFont_(NSFont.systemFontOfSize_(13.0))
            lbl.setTextColor_(
                NSColor.labelColor() if i == selected else NSColor.secondaryLabelColor()
            )
            container.addSubview_(lbl)
            x += item_w

            if i < len(items) - 1:
                sep = NSTextField.alloc().initWithFrame_(NSMakeRect(x, 0, 14, h))
                sep.setStringValue_("›")
                sep.setBezeled_(False)
                sep.setDrawsBackground_(False)
                sep.setEditable_(False)
                sep.setSelectable_(False)
                sep.setTextColor_(NSColor.tertiaryLabelColor())
                sep.setFont_(NSFont.systemFontOfSize_(13.0))
                container.addSubview_(sep)
                x += 14

        return container

    def _build_fab(self, node, pw, ph):
        """Circular Floating Action Button with SF Symbol icon."""
        size  = _to_float(node.get("size"), 52)
        frame, mask = self._layout_from_node(node, pw, ph)
        # Force square frame for circle
        frame = NSMakeRect(frame.origin.x, frame.origin.y, size, size)

        icon = None
        src  = node.get("src", "plus")
        if src:
            icon = NSImage.imageWithSystemSymbolName_accessibilityDescription_(src, None)
            if icon:
                # Render white symbol on colored background
                icon = icon.copy()
                icon.setTemplate_(True)

        handler = None
        action_name = node.get("action")
        if action_name and self.logic is not None:
            callback = self.logic.resolve(action_name, self)
            handler  = ControlActionHandler.alloc().initWithCallback_(callback)
            self.handlers.append(handler)

        fab = _FabView.alloc().initWithFrame_icon_handler_(frame, icon, handler)
        fab.setAutoresizingMask_(mask)
        return fab

    def _build_carousel(self, node, pw, ph):
        """Horizontally scrollable row of slide-container views."""
        frame, mask = self._layout_from_node(node, pw, ph)
        scroll = NSScrollView.alloc().initWithFrame_(frame)
        scroll.setAutoresizingMask_(mask)
        scroll.setHasHorizontalScroller_(True)
        scroll.setHasVerticalScroller_(False)
        scroll.setBorderType_(_BORDER_TYPE_NONE)

        slides  = [n for n in node if n.tag.lower() == "slide"]
        n       = len(slides)
        slide_w = frame.size.width
        slide_h = frame.size.height
        total_w = slide_w * max(n, 1)

        content = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, total_w, slide_h))

        for i, slide_node in enumerate(slides):
            slide = NSView.alloc().initWithFrame_(
                NSMakeRect(i * slide_w, 0, slide_w, slide_h)
            )
            for child in slide_node:
                child_view = self._build_view(child, slide_w, slide_h)
                if child_view is not None:
                    slide.addSubview_(child_view)
            content.addSubview_(slide)

        scroll.setDocumentView_(content)
        return scroll

    def _build_tabs(self, node, pw, ph):
        frame, mask = self._layout_from_node(node, pw, ph)
        tv = NSTabView.alloc().initWithFrame_(frame)
        tv.setAutoresizingMask_(mask)

        # Approx inner content dimensions (tab header ≈ 28px)
        inner_w = frame.size.width
        inner_h = frame.size.height - 28

        for tab_node in node:
            if tab_node.tag.lower() != "tab":
                continue
            item = NSTabViewItem.alloc().init()
            item.setLabel_(tab_node.get("title", "Tab"))
            tv.addTabViewItem_(item)

            content = item.view()
            for child in tab_node:
                child_view = self._build_view(child, inner_w, inner_h)
                if child_view is not None:
                    content.addSubview_(child_view)
        return tv

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_view(self, view_id):
        view = self.views_by_id.get(view_id)
        if view is None:
            raise KeyError(f"No UI element found with id '{view_id}'.")
        return view

    def set_visible(self, view_id, visible: bool):
        """Show/hide any view by id."""
        view = self.get_view(view_id)
        if hasattr(view, "setHidden_"):
            view.setHidden_(not bool(visible))
            return
        raise TypeError(f"'{view_id}' does not support visibility updates.")

    def focus(self, view_id):
        """Set keyboard focus to a control/view by id."""
        if self.window is None:
            return
        v = self.get_view(view_id)
        try:
            self.window.makeFirstResponder_(v)
        except Exception:
            pass

    def set_icon_color(self, view_id, color_name: str):
        """Update an <icon> color at runtime (works for clickable icons)."""
        v = self.get_view(view_id)
        color_map = {
            "label":     NSColor.labelColor(),
            "secondary": NSColor.secondaryLabelColor(),
            "tertiary":  NSColor.tertiaryLabelColor(),
            "accent":    highlight_color(),
            "red":       NSColor.redColor(),
            "green":     NSColor.greenColor(),
            "blue":      NSColor.blueColor(),
            "orange":    NSColor.orangeColor(),
            "white":     NSColor.whiteColor(),
        }
        c = color_map.get(color_name, NSColor.labelColor())
        if hasattr(v, "setBaseColor_"):
            v.setBaseColor_(c)
            return
        if hasattr(v, "setTextColor_"):
            v.setTextColor_(c)
            return
        raise TypeError(f"'{view_id}' does not support icon color updates.")

    def show_confirm_modal(self, title: str, message: str, on_confirm):
        """Custom modal: dim background + centered blur panel."""
        if self.container is None:
            return

        parent = self.container
        b = parent.bounds()

        overlay = _DimOverlay.alloc().initWithFrame_(b)
        overlay.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)

        mw, mh = 360, 170
        mx = (b.size.width - mw) / 2.0
        my = (b.size.height - mh) / 2.0
        modal = NSVisualEffectView.alloc().initWithFrame_(NSMakeRect(mx, my, mw, mh))
        modal.setAutoresizingMask_(NSViewMinXMargin | NSViewMaxXMargin | NSViewMinYMargin | NSViewMaxYMargin)
        modal.setBlendingMode_(NSVisualEffectBlendingModeBehindWindow)
        modal.setMaterial_(NSVisualEffectMaterialUnderWindowBackground)
        modal.setState_(NSVisualEffectStateActive)
        modal.setWantsLayer_(True)
        modal.layer().setCornerRadius_(12.0)
        modal.layer().setMasksToBounds_(True)

        title_lbl = NSTextField.alloc().initWithFrame_(NSMakeRect(18, mh - 44, mw - 36, 22))
        title_lbl.setStringValue_(title)
        title_lbl.setBezeled_(False)
        title_lbl.setDrawsBackground_(False)
        title_lbl.setEditable_(False)
        title_lbl.setSelectable_(False)
        title_lbl.setFont_(NSFont.boldSystemFontOfSize_(14.0))
        title_lbl.setTextColor_(NSColor.labelColor())

        msg_lbl = NSTextField.alloc().initWithFrame_(NSMakeRect(18, mh - 92, mw - 36, 44))
        msg_lbl.setStringValue_(message)
        msg_lbl.setBezeled_(False)
        msg_lbl.setDrawsBackground_(False)
        msg_lbl.setEditable_(False)
        msg_lbl.setSelectable_(False)
        msg_lbl.setFont_(NSFont.systemFontOfSize_(13.0))
        msg_lbl.setTextColor_(NSColor.secondaryLabelColor())
        msg_lbl.setWraps_(True)

        cancel_btn = NSButton.alloc().initWithFrame_(NSMakeRect(mw - 110 - 18, 18, 110, 30))
        cancel_btn.setTitle_("Abbrechen")
        cancel_btn.setBezelStyle_(1)
        cancel_btn.setKeyEquivalent_("\x1b")  # Escape

        ok_btn = NSButton.alloc().initWithFrame_(NSMakeRect(18, 18, 110, 30))
        ok_btn.setTitle_("Beenden")
        ok_btn.setBezelStyle_(1)

        def close_modal():
            overlay.removeFromSuperview()

        cancel_handler = ControlActionHandler.alloc().initWithCallback_(close_modal)
        ok_handler = ControlActionHandler.alloc().initWithCallback_(lambda: (close_modal(), on_confirm()))
        self.handlers.extend([cancel_handler, ok_handler])
        cancel_btn.setTarget_(cancel_handler)
        cancel_btn.setAction_("onAction:")
        ok_btn.setTarget_(ok_handler)
        ok_btn.setAction_("onAction:")

        modal.addSubview_(title_lbl)
        modal.addSubview_(msg_lbl)
        modal.addSubview_(cancel_btn)
        modal.addSubview_(ok_btn)
        overlay.addSubview_(modal)
        parent.addSubview_(overlay)

    def get_text(self, view_id):
        """label, textfield, textarea, combobox, searchfield, tokenfield, button, dropdown."""
        view = self.get_view(view_id)
        if hasattr(view, "string"):
            return str(view.string())                       # NSTextView
        if hasattr(view, "stringValue"):
            return str(view.stringValue())                  # NSTextField et al.
        if hasattr(view, "titleOfSelectedItem"):
            return str(view.titleOfSelectedItem() or "")   # NSPopUpButton
        if hasattr(view, "title"):
            return str(view.title())                        # NSButton
        raise TypeError(f"'{view_id}' does not expose readable text.")

    def set_text(self, view_id, text):
        """label, textfield, textarea, button."""
        view = self.get_view(view_id)
        if hasattr(view, "setString_"):
            view.setString_(text)
            return
        if hasattr(view, "setStringValue_"):
            view.setStringValue_(text)
            return
        if hasattr(view, "setTitle_"):
            view.setTitle_(text)
            return
        raise TypeError(f"'{view_id}' does not support text updates.")

    def get_value(self, view_id):
        """slider, stepper, progressbar, spinner."""
        view = self.get_view(view_id)
        if hasattr(view, "doubleValue"):
            return view.doubleValue()
        raise TypeError(f"'{view_id}' does not expose a numeric value.")

    def set_value(self, view_id, value):
        """slider, stepper, progressbar."""
        view = self.get_view(view_id)
        if hasattr(view, "setDoubleValue_"):
            view.setDoubleValue_(float(value))
            return
        raise TypeError(f"'{view_id}' does not support numeric updates.")

    def get_state(self, view_id):
        """checkbox, radio, switch → bool."""
        view = self.get_view(view_id)
        if hasattr(view, "state"):
            return bool(view.state())
        raise TypeError(f"'{view_id}' does not expose a state.")

    def set_state(self, view_id, value):
        """checkbox, radio, switch."""
        view = self.get_view(view_id)
        if hasattr(view, "setState_"):
            view.setState_(1 if value else 0)
            return
        raise TypeError(f"'{view_id}' does not support state updates.")

    def get_selected(self, view_id):
        """dropdown, segmented → int index."""
        view = self.get_view(view_id)
        if hasattr(view, "indexOfSelectedItem"):
            return view.indexOfSelectedItem()
        if hasattr(view, "selectedSegment"):
            return view.selectedSegment()
        raise TypeError(f"'{view_id}' does not expose a selection.")

    def set_selected(self, view_id, index):
        """dropdown, segmented."""
        view = self.get_view(view_id)
        if hasattr(view, "selectItemAtIndex_"):
            view.selectItemAtIndex_(int(index))
            return
        if hasattr(view, "setSelectedSegment_"):
            view.setSelectedSegment_(int(index))
            return
        raise TypeError(f"'{view_id}' does not support selection updates.")

    def get_color(self, view_id):
        """colorwell → NSColor."""
        view = self.get_view(view_id)
        if hasattr(view, "color"):
            return view.color()
        raise TypeError(f"'{view_id}' does not expose a color.")

    def set_color(self, view_id, ns_color):
        """colorwell."""
        view = self.get_view(view_id)
        if hasattr(view, "setColor_"):
            view.setColor_(ns_color)
            return
        raise TypeError(f"'{view_id}' does not support color updates.")

    def get_date(self, view_id):
        """datepicker → NSDate."""
        view = self.get_view(view_id)
        if hasattr(view, "dateValue"):
            return view.dateValue()
        raise TypeError(f"'{view_id}' does not expose a date.")

    def set_date(self, view_id, ns_date):
        """datepicker."""
        view = self.get_view(view_id)
        if hasattr(view, "setDateValue_"):
            view.setDateValue_(ns_date)
            return
        raise TypeError(f"'{view_id}' does not support date updates.")

    def start_spinner(self, view_id):
        """spinner → startet Animation."""
        view = self.get_view(view_id)
        if hasattr(view, "startAnimation_"):
            view.startAnimation_(None)

    def stop_spinner(self, view_id):
        """spinner → stoppt Animation."""
        view = self.get_view(view_id)
        if hasattr(view, "stopAnimation_"):
            view.stopAnimation_(None)

    # ------------------------------------------------------------------
    # Overlay / transient UI
    # ------------------------------------------------------------------

    def show_toast(self, text, duration=3.0):
        """
        Zeigt einen Toast (Snackbar) unten-mittig im Fenster.
        Verschwindet nach `duration` Sekunden automatisch.
        """
        pw, ph = 320, 48

        if self.window:
            wf = self.window.frame()
            x  = wf.origin.x + (wf.size.width - pw) / 2
            y  = wf.origin.y + 24
        else:
            x, y = 300, 80

        panel = NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(x, y, pw, ph),
            NSWindowStyleMaskBorderless,
            1,      # NSBackingStoreBuffered
            False,
        )
        panel.setOpaque_(False)
        panel.setBackgroundColor_(NSColor.clearColor())
        panel.setHasShadow_(True)
        panel.setLevel_(NSFloatingWindowLevel)

        bg = NSVisualEffectView.alloc().initWithFrame_(NSMakeRect(0, 0, pw, ph))
        bg.setBlendingMode_(NSVisualEffectBlendingModeBehindWindow)
        bg.setMaterial_(NSVisualEffectMaterialUnderWindowBackground)
        bg.setState_(NSVisualEffectStateActive)
        bg.setWantsLayer_(True)
        bg.layer().setCornerRadius_(10.0)
        bg.layer().setMasksToBounds_(True)

        lbl = NSTextField.alloc().initWithFrame_(NSMakeRect(16, 0, pw - 32, ph))
        lbl.setStringValue_(text)
        lbl.setBezeled_(False)
        lbl.setDrawsBackground_(False)
        lbl.setEditable_(False)
        lbl.setSelectable_(False)
        lbl.setTextColor_(NSColor.labelColor())
        lbl.setFont_(NSFont.systemFontOfSize_(14.0))
        lbl.setAlignment_(1)  # NSTextAlignmentCenter
        bg.addSubview_(lbl)

        panel.setContentView_(bg)
        panel.orderFront_(None)

        dismisser = _ToastDismisser.alloc().initWithPanel_(panel)
        self._toast_refs.append((dismisser, panel))
        dismisser.performSelector_withObject_afterDelay_("dismiss:", None, duration)

    def show_popover(self, anchor_id, text, width=240, height=80):
        """
        Zeigt einen nativen macOS-Popover über dem Element `anchor_id`.
        Der Popover schließt sich automatisch wenn der Nutzer klickt.
        """
        anchor = self.get_view(anchor_id)
        vc = _PopoverContentVC.alloc().initWithText_width_height_(text, width, height)

        pop = NSPopover.alloc().init()
        pop.setContentSize_(NSMakeSize(float(width), float(height)))
        pop.setContentViewController_(vc)
        pop.setBehavior_(1)  # NSPopoverBehaviorTransient

        pop.showRelativeToRect_ofView_preferredEdge_(
            anchor.bounds(),
            anchor,
            3,    # NSMaxYEdge → erscheint oberhalb des Anchors
        )
        self._popover_refs.append((pop, vc))
