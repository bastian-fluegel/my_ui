from AppKit import (
    NSApp,
    NSApplication,
    NSApplicationActivationPolicyRegular,
)
from Foundation import NSObject
from PyObjCTools import AppHelper

import phosphor_icons
from ui_logic import UILogic
from xml_loader import XMLUIBuilder


class AppDelegate(NSObject):
    def applicationDidFinishLaunching_(self, _notification):
        logic = UILogic()
        self.builder = XMLUIBuilder("ui.xml", logic=logic)
        self.window = self.builder.build_window()
        logic.show_home(self.builder)   # set initial icon highlight + breadcrumb
        self.window.makeKeyAndOrderFront_(None)
        NSApp.activateIgnoringOtherApps_(True)


def main():
    phosphor_icons.register()

    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyRegular)

    delegate = AppDelegate.alloc().init()
    app.setDelegate_(delegate)

    AppHelper.runEventLoop()


if __name__ == "__main__":
    main()
