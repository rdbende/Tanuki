# main.py
#
# SPDX-FileCopyrightText: 2024  Benedek Dévényi
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import sys

from gi.repository import Adw, Gio, GLib
from tanuki.backend import OAuthLogin


class TanukiApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self):
        super().__init__(
            application_id="io.github.rdbende.Tanuki", flags=Gio.ApplicationFlags.HANDLES_OPEN
        )
        self.create_action("quit", lambda *_: self.quit(), ["<primary>q"])
        self.create_action(
            "add_new_account", self.on_add_new_account, parameter_type=GLib.VariantType("b")
        )
        self.create_action("about", self.on_about_action, ["F1"])

    def do_open(self, files: list[Gio.File], *_):
        uri = GLib.Uri.parse(files[0].get_uri(), GLib.UriFlags.NONE)
        if uri.get_scheme() == "tanuki":
            query = uri.get_query()
            if query:
                uri_params = GLib.Uri.parse_params(
                    uri.get_query(), -1, "&", GLib.UriParamsFlags.NONE
                )

                if "code" in uri_params and "state" in uri_params:
                    OAuthLogin.redirect(uri_params.get("state"), uri_params.get("code"))
                elif uri_params.get("error", "") == "access_denied":
                    OAuthLogin.access_denied(uri_params.get("state"))

        self.do_activate()

    def do_activate(self):
        """Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.
        """
        win = self.props.active_window

        if not win:
            from tanuki.window import MainWindow

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

    def on_add_new_account(self, _, value):
        from tanuki.dialogs.account_setup import LoginDialog

        win = self.props.active_window
        win.sidebar.account_chooser.popdown()
        LoginDialog(skip_welcome_page=value.get_boolean()).present(win)

    def create_action(self, name, callback, shortcuts=None, parameter_type=None):
        """Add an application action.

        Args:
            name: the name of the action
            callback: the function to be called when the action is
              activated
            shortcuts: an optional list of accelerators
        """
        action = Gio.SimpleAction.new(name, parameter_type)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)


app = None


def get_application() -> TanukiApplication:
    assert app is not None
    return app


def get_main_window() -> MainWindow | None:
    assert app is not None
    return app.get_active_window()


def main(version):
    """The application's entry point."""
    global app
    app = TanukiApplication()
    return app.run(sys.argv)
