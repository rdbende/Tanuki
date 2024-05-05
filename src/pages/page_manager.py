# page_manager.py
#
# SPDX-FileCopyrightText: 2024  Benedek Dévényi
# SPDX-License-Identifier: GPL-3.0-or-later


from gi.repository import Adw, Gio, GLib, GObject, Gtk
from tanuki.main import get_main_window


class PageManager(GObject.Object):
    __gtype_name__ = "PageManager"

    @classmethod
    def add_page(cls, page: Adw.Bin) -> None:
        nav_page = Adw.NavigationPage(title="Page")
        toolbar_view = Adw.ToolbarView()
        toolbar_view.set_content(page)
        toolbar_view.add_top_bar(Adw.HeaderBar())
        nav_page.set_child(toolbar_view)
        get_main_window().navigation_view.push(nav_page)

    def go_back_home():
        ...
