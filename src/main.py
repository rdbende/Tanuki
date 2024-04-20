# main.py
#
# SPDX-FileCopyrightText: 2024  Benedek Dévényi
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import sys

from gi.repository import Adw, Gio

app = None


def get_application() -> TanukiApplication:
    assert app is not None
    return app


class TanukiApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self):
        super().__init__(
            application_id="io.github.rdbende.Tanuki", flags=Gio.ApplicationFlags.DEFAULT_FLAGS
        )
        self.create_action("quit", lambda *_: self.quit(), ["<primary>q"])
        self.create_action("about", self.on_about_action, ["F1"])

    def do_activate(self):
        """Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.
        """
        win = self.props.active_window

        if not win:
            from .window import MainWindow

            win = MainWindow(application=self)

        win.present()

    def on_about_action(self, widget, _):
        """Callback for the app.about action."""
        about = Adw.AboutDialog(
            application_name="Tanuki",
            application_icon="io.github.rdbende.Tanuki",
            developer_name="Benedek Dévényi",
            version="0.1.0",
            developers=["Benedek Dévényi"],
            copyright="© 2024 Benedek Dévényi",
        )
        about.present(self.props.active_window)

    def create_action(self, name, callback, shortcuts=None):
        """Add an application action.

        Args:
            name: the name of the action
            callback: the function to be called when the action is
              activated
            shortcuts: an optional list of accelerators
        """
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)


def main(version):
    """The application's entry point."""
    global app
    app = TanukiApplication()
    return app.run(sys.argv)
