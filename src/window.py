# window.py
#
# SPDX-FileCopyrightText: 2024  Benedek Dévényi
# SPDX-License-Identifier: GPL-3.0-or-later


from gi.repository import Adw, Gio, GLib, GObject, Gtk
from tanuki.backend import session, settings
from tanuki.pages import UserPage
from tanuki.views.sidebar import Sidebar, SidebarItem


@Gtk.Template(resource_path="/io/github/rdbende/Tanuki/window.ui")
class MainWindow(Adw.ApplicationWindow):
    __gtype_name__ = "MainWindow"

    sidebar: Sidebar = Gtk.Template.Child()
    home_stack: Adw.ViewStack = Gtk.Template.Child()
    navigation_view: Adw.NavigationView = Gtk.Template.Child()

    loading_stack: Gtk.Stack = Gtk.Template.Child()
    spinner_box: Gtk.Box = Gtk.Template.Child()
    logging_in_spinner: Gtk.Spinner = Gtk.Template.Child()

    primary_menu: Gio.MenuModel = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.setup_components()

        session.connect("login-started", self.show_loading_spinner)
        session.connect("login-completed", self.hide_loading_spinner)

        current_session = settings.props.current_session
        if not current_session:
            self.set_up_account()
        else:
            session.start_session(current_session)

        settings.connect(
            "changed::current-session",
            lambda o, s: self.set_up_account() if not o.get_property(s) else None,
        )

    def show_loading_spinner(self, *_) -> None:
        self.loading_stack.set_visible_child(self.spinner_box)
        self.logging_in_spinner.set_spinning(True)

    def hide_loading_spinner(self, *_) -> None:
        self.loading_stack.set_visible_child(self.home_stack)
        self.logging_in_spinner.set_spinning(False)

    @Gtk.Template.Callback()
    def user_own_profile(self, *_):
        self.add_page(UserPage(session.get_account_info().username))

    def set_up_account(self, *_) -> None:
        self.get_application().activate_action("add_new_account", GLib.Variant.new_boolean(True))

    def add_page(self, page: Adw.Bin) -> None:
        nav_page = Adw.NavigationPage(title="Page")
        toolbar_view = Adw.ToolbarView()
        toolbar_view.set_content(page)
        toolbar_view.add_top_bar(Adw.HeaderBar())
        nav_page.set_child(toolbar_view)
        self.navigation_view.push(nav_page)

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
