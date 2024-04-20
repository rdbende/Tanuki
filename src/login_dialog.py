# login_dialog.py
#
# SPDX-FileCopyrightText: 2024  Benedek Dévényi
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Adw, Gtk
from tanuki.backend import session
from tanuki.main import get_application
from tanuki.widgets import SpinnerButton


@Gtk.Template(resource_path="/io/github/rdbende/Tanuki/login_dialog.ui")
class LoginDialog(Adw.Dialog):
    __gtype_name__ = "LoginDialog"

    navigation_view = Gtk.Template.Child()
    toaster: Adw.ToastOverlay = Gtk.Template.Child()

    instance_select_button: Gtk.Button = Gtk.Template.Child()
    login_button: SpinnerButton = Gtk.Template.Child()

    instance_entry: Adw.EntryRow = Gtk.Template.Child()
    token_entry: Adw.EntryRow = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        session.connect("login-completed", self.login_completed)
        session.connect("login-failed", self.login_falied)

        self.connect("close-attempt", self.on_close_attempt)

    def on_close_attempt(self, *_):
        self.force_close()
        app = get_application()
        if app is not None and not session.logged_in:
            app.quit()

    @Gtk.Template.Callback()
    def string_is_not_empty(self, _, string) -> bool:
        return bool(string)

    @Gtk.Template.Callback()
    def on_complete_clicked(self, *_):
        self.close()

    @Gtk.Template.Callback()
    def go_to_login_page(self, *_):
        self.login_button.stop()
        self.login_button.set_sensitive(False)
        self.token_entry.set_text("")
        self.navigation_view.push_by_tag("login")

    @Gtk.Template.Callback()
    def on_login_clicked(self, *_):
        self.login_button.start()

        instance_url = self.instance_entry.get_text()
        if not instance_url.startswith("http"):
            instance_url = "https://" + instance_url

        session.login(url=instance_url, private_token=self.token_entry.get_text())

    def login_completed(self, *_):
        self.navigation_view.push_by_tag("finished")
        self.login_button.stop()
        session.print_user()

    def login_falied(self, *junk) -> None:
        self.navigation_view.pop_to_tag("instance")
        self.show_toast(_("Login Unsuccessful"))

    def show_toast(self, message: str) -> None:
        self.toaster.add_toast(Adw.Toast(title=message, timeout=3))
