# main.py
#
# SPDX-FileCopyrightText: 2024  Benedek Dévényi
# SPDX-License-Identifier: GPL-3.0-or-later

import sys

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gio

from .window import TanukiWindow


class TanukiApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self):
        super().__init__(
            application_id="io.github.rdbende.Tanuki", flags=Gio.ApplicationFlags.DEFAULT_FLAGS
        )
        self.create_action("quit", lambda *_: self.quit(), ["<primary>q"])
        self.create_action("about", self.on_about_action)

    def do_activate(self):
        """Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.
        """
        win = self.props.active_window
        if not win:
            win = TanukiWindow(application=self)
        win.present()

    def on_about_action(self, widget, _):
        """Callback for the app.about action."""
        about = Adw.AboutWindow(
            transient_for=self.props.active_window,
            application_name="Tanuki",
            application_icon="io.github.rdbende.Tanuki",
            developer_name="Benedek Dévényi",
            version="0.1.0",
            developers=["Benedek Dévényi"],
            copyright="© 2024 Benedek Dévényi",
        )
        about.present()

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
    app = TanukiApplication()
    return app.run(sys.argv)
