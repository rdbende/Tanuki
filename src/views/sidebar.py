# sidebar.py
#
# SPDX-FileCopyrightText: 2024  Benedek Dévényi
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import Callable

from gi.repository import Adw, Gio, GObject, Gtk
from tanuki.backend import SessionManager, session, settings
from tanuki.dialogs.login import LoginDialog
from tanuki.tools import RemoteImage


class AvatarButton(Adw.Bin):
    __gtype_name__ = "AvatarButton"

    avatar_url = GObject.Property(type=str)
    size = GObject.Property(type=int)
    text = GObject.Property(type=str)

    def __init__(self) -> None:
        super().__init__()
        self.add_css_class("avatar-button")

        self.avatar = Adw.Avatar(show_initials=True)
        self.set_child(self.avatar)

        self.remote_image = RemoteImage(self, "avatar-url")
        self.remote_image.bind_to(self.avatar, "custom-image")
        self.bind_property("size", self.avatar, "size")
        self.bind_property("text", self.avatar, "text")
        self.bind_property("text", self, "tooltip-text")


@Gtk.Template(resource_path="/io/github/rdbende/Tanuki/views/sidebar/account_row.ui")
class AccountRow(Adw.ActionRow):
    __gtype_name__ = "AccountRow"

    display_name = GObject.Property(type=str)
    username = GObject.Property(type=str)
    avatar_url = GObject.Property(type=str)

    avatar: AvatarButton = Gtk.Template.Child()

    def __init__(self, username: str, display_name: str, avatar_url: str, session_id: str) -> None:
        super().__init__()
        self.connect("activated", self.switch_account)

        self._session_id = session_id

        self.props.display_name = display_name
        self.props.username = username
        self.props.avatar_url = avatar_url

    def set_avatar_size(self):
        self.avatar.props.size = 38 if self.is_selected() else 42

    def switch_account(self, *_) -> None:
        session.start_session(self._session_id)

    @Gtk.Template.Callback()
    def remove_account(self, *_) -> None:
        SessionManager.remove_session(self._session_id)


@Gtk.Template(resource_path="/io/github/rdbende/Tanuki/views/sidebar/account_chooser.ui")
class AccountChooser(Gtk.MenuButton):
    __gtype_name__ = "AccountChooser"

    avatar: AvatarButton = Gtk.Template.Child()
    accounts: Gtk.ListBox = Gtk.Template.Child()
    popover: Gtk.Popover = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        settings.connect("changed::sessions", self.reload_account_list)
        settings.connect("changed::current-session", self.set_active_account)
        session.connect("login-started", lambda *_: self.set_sensitive(False))
        session.connect("login-completed", lambda *_: self.set_sensitive(True))
        session.connect("login-failed", lambda *_: self.set_sensitive(True))
        self.accounts.connect("selected-rows-changed", self.set_avatar_sizes)

        self._rows = {}
        self.reload_account_list()

    def set_avatar_sizes(self, *_):
        row = self.accounts.get_first_child()
        while row:
            row.set_avatar_size()
            row = row.get_next_sibling()

    def set_active_account(self, obj: Gio.Settings, setting: str) -> None:
        session = obj.get_property(setting)
        if session:
            self.avatar.props.avatar_url = SessionManager.get_avatar_url_for_session(session)
            self.accounts.select_row(self._rows[session])
        else:
            self.avatar.props.avatar_url = ""

    def reload_account_list(self, *_):
        self.accounts.remove_all()
        self._rows.clear()

        for id, account in SessionManager.get_sessions().items():
            row = AccountRow(
                username=account["username"],
                display_name=account["name"],
                avatar_url=account["avatar"],
                session_id=id,
            )

            self.accounts.append(row)
            self._rows[id] = row

    @Gtk.Template.Callback()
    def on_add_new_account_clicked(self, *_):
        LoginDialog(first_login=False).present()


@Gtk.Template(resource_path="/io/github/rdbende/Tanuki/views/sidebar/item.ui")
class SidebarItem(Adw.ActionRow):
    __gtype_name__ = "SidebarItem"

    icon_name = GObject.Property(type=str)
    badge_number = GObject.Property(type=int)
    needs_attention = GObject.Property(type=bool, default=False)

    def __init__(self, title: str = "", icon_name: str = "") -> None:
        super().__init__()

        self.props.title = title
        self.props.icon_name = icon_name

        self.connect(
            "notify::needs-attention",
            lambda *_: (
                self.add_css_class("needs-attention")
                if self.props.needs_attention
                else self.remove_css_class("needs-attention")
            ),
        )

    @Gtk.Template.Callback()
    def is_not_zero(self, *_) -> bool:
        return self.props.badge_number != 0


@Gtk.Template(resource_path="/io/github/rdbende/Tanuki/views/sidebar/view.ui")
class Sidebar(Adw.Bin):
    __gtype_name__ = "Sidebar"

    menu_model = GObject.Property(type=Gio.MenuModel)

    list: Gtk.ListBox = Gtk.Template.Child()
    account_chooser: AccountChooser = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def add_item(self, item: SidebarItem, callback: Callable) -> None:
        item.connect("activated", callback)
        self.list.append(item)
