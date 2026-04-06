from AppKit import NSApp


class UILogic:
    def resolve(self, action_name, ui):
        return {
            "show_home":     lambda: self.show_home(ui),
            "show_user":     lambda: self.show_user(ui),
            "show_config":   lambda: self.show_config(ui),
            "quit_app":      lambda: self.quit_app(ui),
        }.get(action_name, lambda: print(f"Unknown action: {action_name}"))

    def _show_only(self, ui, view_id):
        for vid in ("home_view", "user_view", "config_view"):
            ui.set_visible(vid, vid == view_id)

    def show_home(self, ui):
        self._show_only(ui, "home_view")
        ui.set_text("breadcrumbs", f"{self._app_name(ui)} > Home")
        ui.set_icon_color("nav_home", "label")
        ui.set_icon_color("nav_user", "secondary")
        ui.set_icon_color("nav_config", "secondary")

    def show_user(self, ui):
        self._show_only(ui, "user_view")
        ui.set_text("breadcrumbs", f"{self._app_name(ui)} > User")
        ui.set_icon_color("nav_home", "secondary")
        ui.set_icon_color("nav_user", "label")
        ui.set_icon_color("nav_config", "secondary")

    def show_config(self, ui):
        self._show_only(ui, "config_view")
        ui.set_text("breadcrumbs", f"{self._app_name(ui)} > Config")
        ui.set_icon_color("nav_home", "secondary")
        ui.set_icon_color("nav_user", "secondary")
        ui.set_icon_color("nav_config", "label")

    def _app_name(self, ui):
        try:
            return ui.get_text("title").strip() or "App"
        except Exception:
            return "App"

    def quit_app(self, ui):
        ui.show_confirm_modal(
            "Wirklich beenden?",
            "Die Anwendung wird geschlossen.",
            on_confirm=lambda: NSApp.terminate_(None),
        )
