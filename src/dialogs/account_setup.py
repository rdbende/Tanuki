# account_setup.py
#
# SPDX-FileCopyrightText: 2024  Benedek Dévényi
# SPDX-License-Identifier: GPL-3.0-or-later


from functools import partial, partialmethod
from urllib.parse import urlparse

from gi.repository import Adw, Gtk
from tanuki.backend import (
    GitLabDotComOAuthLogin,
    OAuthLogin,
    PersonalAccessTokenLogin,
    SessionManager,
    session,
)
from tanuki.main import get_application
from tanuki.tools import RemoteImages
from tanuki.widgets import SpinnerButton


@Gtk.Template(resource_path="/io/github/rdbende/Tanuki/dialogs/account_setup.ui")
class LoginDialog(Adw.Dialog):
    __gtype_name__ = "LoginDialog"

    navigation_view: Adw.NavigationView = Gtk.Template.Child()
    login_page: Adw.NavigationPage = Gtk.Template.Child()
    login_status_page: Adw.StatusPage = Gtk.Template.Child()
    all_set_page: Adw.StatusPage = Gtk.Template.Child()
    toaster: Adw.ToastOverlay = Gtk.Template.Child()

    instance_select_button: Gtk.Button = Gtk.Template.Child()
    login_button: SpinnerButton = Gtk.Template.Child()

    instance_entry: Adw.EntryRow = Gtk.Template.Child()
    token_entry: Adw.EntryRow = Gtk.Template.Child()

    oauth_providers_box: Gtk.Box = Gtk.Template.Child()

    def __init__(self, skip_welcome_page: bool = True, **kwargs):
        super().__init__(**kwargs)

        if skip_welcome_page:
            self.navigation_view.replace_with_tags(["auth_methods"])

        self._callback_handler_ids = [
            session.connect("login-completed", self.on_login_completed),
            session.connect("login-failed", self.on_login_falied),
        ]

        self.connect("close-attempt", self.on_close_attempt)

        self.set_up_oauth_provider_buttons()

    def set_up_oauth_provider_buttons(self):
        for provider in OAuthLogin.providers:
            button = Gtk.Button(icon_name=provider.icon, tooltip_text=provider.display_name)
            button.set_css_classes(["oauth-provider-button", "icon-button", "card"])
            button.connect("clicked", partial(self.add_oauth_account, provider))
            self.oauth_providers_box.append(button)

    def add_oauth_account(self, provider: OAuthLogin, *_) -> bool:
        provider().start_auth_flow(session.create_session, self.access_denied_callback)
        self.navigation_view.push_by_tag("confirm_oauth")

    def add_pat_account(self, url: str, token: str) -> bool:
        session.create_session(PersonalAccessTokenLogin(url=self.get_instance_url(), token=token))

    def access_denied_callback(self):
        self.navigation_view.push_by_tag("oauth_access_denied")

    def get_instance_url(self):
        instance_url = self.instance_entry.get_text()
        if not instance_url.startswith("http"):
            instance_url = f"https://{instance_url}"
        return instance_url

    @Gtk.Template.Callback()
    def string_is_not_empty(self, _, string: str) -> bool:
        return bool(string)

    @Gtk.Template.Callback()
    def go_to_login_page(self, *__):
        self.login_button.stop(sensitive=False)
        self.token_entry.set_sensitive(True)
        self.token_entry.set_text("")
        self.navigation_view.push_by_tag("login")

        self.login_status_page.props.title = _("Log in to {domain}").format(
            domain=urlparse(self.get_instance_url()).netloc
        )

    @Gtk.Template.Callback()
    def go_to_auth_methods_page(self, *_):
        if self.navigation_view.find_page("auth_methods"):
            self.navigation_view.pop_to_tag("auth_methods")
        else:
            self.navigation_view.push_by_tag("auth_methods")

    @Gtk.Template.Callback()
    def finish_clicked(self, *_):
        self.close()

    @Gtk.Template.Callback()
    def start_login_clicked(self, *_):
        self.login_button.start()
        self.token_entry.set_sensitive(False)
        self.login_page.set_can_pop(False)

        self.add_pat_account(url=self.get_instance_url(), token=self.token_entry.get_text())

    def show_toast(self, message: str) -> None:
        self.toaster.add_toast(Adw.Toast(title=message, timeout=3))

    def on_login_completed(self, *_):
        self.navigation_view.push_by_tag("completed")
        self.login_button.stop()

    def on_login_falied(self, *__) -> None:
        self.navigation_view.pop_to_tag("instance")
        self.show_toast(_("Login Failed"))

    def on_close_attempt(self, *_):
        if not SessionManager.any_sessions():
            get_application().quit()

        self.force_close()

        del self.navigation_view  # not sure why this is needed

        for handler in self._callback_handler_ids:
            session.disconnect(handler)
