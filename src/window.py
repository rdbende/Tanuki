# window.py
#
# SPDX-FileCopyrightText: 2024  Benedek Dévényi
# SPDX-License-Identifier: GPL-3.0-or-later

import gi

from gi.repository import Adw, Gtk
from tanuki.backend import session
from tanuki.widgets import SpinnerButton


@Gtk.Template(resource_path="/io/github/rdbende/Tanuki/window.ui")
class TanukiWindow(Adw.ApplicationWindow):
    __gtype_name__ = "TanukiWindow"

    login_button: SpinnerButton = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.login_button.connect("clicked", self.login)
        session.connect("login-completed", self.logged_in)

    def login(self, *_):
        self.login_button.start()
        # session.login()

    def logged_in(self, *_):
        self.login_button.stop()
        session.print_user()
