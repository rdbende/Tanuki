# window.py
#
# SPDX-FileCopyrightText: 2024  Benedek Dévényi
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Adw, Gio, Gtk
from tanuki import settings
from tanuki.backend import session
from tanuki.dialogs.login import LoginDialog
from tanuki.views.sidebar import Sidebar


@Gtk.Template(resource_path="/io/github/rdbende/Tanuki/window.ui")
class MainWindow(Adw.ApplicationWindow):
    __gtype_name__ = "MainWindow"

    sidebar: Sidebar = Gtk.Template.Child()
    navigation_view: Adw.NavigationView = Gtk.Template.Child()

    primary_menu: Gio.MenuModel = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        current_session = settings.get_string("current-session")
        if not current_session:
            LoginDialog().present(self)
        else:
            session.start_session(current_session)

        self.setup_components()

    def setup_components(self):
        self.sidebar.menu_model = self.primary_menu
