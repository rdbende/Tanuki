# window.py
#
# SPDX-FileCopyrightText: 2024  Benedek Dévényi
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Adw, Gio, Gtk
from tanuki import LoginDialog


@Gtk.Template(resource_path="/io/github/rdbende/Tanuki/window.ui")
class TanukiWindow(Adw.ApplicationWindow):
    __gtype_name__ = "TanukiWindow"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        logged_in = False

        if not logged_in:
            LoginDialog().present(self)

        self.settings = Gio.Settings("io.github.rdbende.Tanuki")
