# window.py
#
# SPDX-FileCopyrightText: 2024  Benedek Dévényi
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Adw, Gtk


@Gtk.Template(resource_path="/io/github/rdbende/Tanuki/window.ui")
class TanukiWindow(Adw.ApplicationWindow):
    __gtype_name__ = "TanukiWindow"

    label = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
