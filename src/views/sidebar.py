# sidebar.py
#
# SPDX-FileCopyrightText: 2024  Benedek Dévényi
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Adw, Gio, GObject, Gtk


@Gtk.Template(resource_path="/io/github/rdbende/Tanuki/views/sidebar/view.ui")
class Sidebar(Adw.Bin):
    __gtype_name__ = "Sidebar"

    menu_model = GObject.Property(type=Gio.MenuModel)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
