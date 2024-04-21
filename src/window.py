# window.py
#
# SPDX-FileCopyrightText: 2024  Benedek Dévényi
# SPDX-License-Identifier: GPL-3.0-or-later


from gi.repository import Adw, Gio, GObject, Gtk
from tanuki import settings
from tanuki.backend import session
from tanuki.dialogs.login import LoginDialog
from tanuki.views.sidebar import Sidebar, SidebarItem


@Gtk.Template(resource_path="/io/github/rdbende/Tanuki/window.ui")
class MainWindow(Adw.ApplicationWindow):
    __gtype_name__ = "MainWindow"

    sidebar: Sidebar = Gtk.Template.Child()
    home_stack: Adw.ViewStack = Gtk.Template.Child()
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

        for page in self.home_stack.get_pages():
            self.add_sidebar_item_for_view_stack_page(page)

    def add_sidebar_item_for_view_stack_page(self, page: Adw.ViewStackPage) -> None:
        item = SidebarItem()

        cool_flags = GObject.BindingFlags.SYNC_CREATE | GObject.BindingFlags.BIDIRECTIONAL

        for property in ("title", "icon-name", "badge-number", "needs-attention"):
            page.bind_property(property, item, property, cool_flags)

        def callback(*_):
            self.home_stack.set_visible_child_name(page.get_name())

        self.sidebar.add_item(item, callback)
