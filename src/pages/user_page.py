# user_page.py
#
# SPDX-FileCopyrightText: 2024  Benedek Dévényi
# SPDX-License-Identifier: GPL-3.0-or-later


from gi.repository import Adw, GObject, Gtk
from gitlab.base import RESTObject
from tanuki.architecture import RemoteImage, async_job_finished
from tanuki.backend import session


@Gtk.Template(resource_path="/io/github/rdbende/Tanuki/pages/user.ui")
class UserPage(Adw.Bin):
    __gtype_name__ = "UserPage"

    username = GObject.Property(type=str)
    bio = GObject.Property(type=str)
    avatar_url = GObject.Property(type=str)

    status_page: Adw.StatusPage = Gtk.Template.Child()

    def __init__(self, username: str):
        super().__init__()
        self.set_user_data(session.get_user, username)
        self.set_user_projects(session.get_projects_of_user, username)

        self.remote_image = RemoteImage(self, "avatar-url")
        self.remote_image.bind_to(self.status_page, "paintable")

    @async_job_finished
    def set_user_data(self, model: RESTObject) -> None:
        self.avatar_url = model.avatar_url
        self.username = model.name
        self.bio = model.bio

    @async_job_finished
    def set_user_projects(self, model: RESTObject) -> None:
        print(model)
