from AppKit import NSApp


class UILogic:
    def __init__(self):
        # Merkt den zuletzt aktiven "normalen" View, damit Abbrechen korrekt zurück navigiert.
        self._last_view = "home_view"

    def resolve(self, action_name, ui):
        return {
            "show_home":     lambda: self.show_home(ui),
            "show_user":     lambda: self.show_user(ui),
            "show_config":   lambda: self.show_config(ui),
            "show_help":     lambda: self.show_help(ui),
            "show_close":    lambda: self.show_close(ui),
            "close_cancel":  lambda: self.close_cancel(ui),
            "close_quit":    lambda: self.close_quit(ui),
        }.get(action_name, lambda: print(f"Unknown action: {action_name}"))

    def _show_only(self, ui, view_id):
        for vid in ("home_view", "user_view", "config_view", "help_view", "close_view"):
            ui.set_visible(vid, vid == view_id)

    def show_home(self, ui):
        self._last_view = "home_view"
        self._show_only(ui, "home_view")
        ui.set_text("breadcrumbs", f"{self._app_name(ui)} > Home")
        ui.set_icon_color("nav_home", "accent")
        ui.set_icon_color("nav_user", "secondary")
        ui.set_icon_color("nav_config", "secondary")

    def show_user(self, ui):
        self._last_view = "user_view"
        self._show_only(ui, "user_view")
        ui.set_text("breadcrumbs", f"{self._app_name(ui)} > User")
        ui.set_icon_color("nav_home", "secondary")
        ui.set_icon_color("nav_user", "accent")
        ui.set_icon_color("nav_config", "secondary")

    def show_config(self, ui):
        self._last_view = "config_view"
        self._show_only(ui, "config_view")
        ui.set_text("breadcrumbs", f"{self._app_name(ui)} > Config")
        ui.set_icon_color("nav_home", "secondary")
        ui.set_icon_color("nav_user", "secondary")
        ui.set_icon_color("nav_config", "accent")
        ui.set_icon_color("nav_help", "secondary")

    def show_help(self, ui):
        self._last_view = "help_view"
        self._show_only(ui, "help_view")
        ui.set_text("breadcrumbs", f"{self._app_name(ui)} > Hilfe")
        ui.set_icon_color("nav_home", "secondary")
        ui.set_icon_color("nav_user", "secondary")
        ui.set_icon_color("nav_config", "secondary")
        ui.set_icon_color("nav_help", "accent")

    def _app_name(self, ui):
        try:
            return ui.get_text("title").strip() or "App"
        except Exception:
            return "App"

    def show_close(self, ui):
        self._show_only(ui, "close_view")
        ui.set_text("breadcrumbs", f"{self._app_name(ui)} > Beenden")
        ui.set_icon_color("nav_home", "secondary")
        ui.set_icon_color("nav_user", "secondary")
        ui.set_icon_color("nav_config", "secondary")
        ui.set_icon_color("nav_help", "secondary")
        # Abbrechen ist "vor-ausgewählt" = Fokus
        try:
            ui.focus("close_cancel")
        except Exception:
            pass

    def close_cancel(self, ui):
        # Zurück zum vorherigen View (Home/User/Config).
        if self._last_view == "user_view":
            return self.show_user(ui)
        if self._last_view == "config_view":
            return self.show_config(ui)
        if self._last_view == "help_view":
            return self.show_help(ui)
        return self.show_home(ui)

    def close_quit(self, _ui):
        NSApp.terminate_(None)
