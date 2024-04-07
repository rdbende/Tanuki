# spinner_button.py
#
# SPDX-FileCopyrightText: 2024  Benedek Dévényi
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import GObject, Gtk


@Gtk.Template(resource_path="/io/github/rdbende/Tanuki/widgets/spinner_button.ui")
class SpinnerButton(Gtk.Button):
    __gtype_name__ = "SpinnerButton"

    content: Gtk.Label = Gtk.Template.Child()
    spinner: Gtk.Spinner = Gtk.Template.Child()
    stack: Gtk.Stack = Gtk.Template.Child()

    label = GObject.Property(type=str)
    icon_name = GObject.Property(type=str)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def start(self):
        self.set_sensitive(False)
        self.spinner.set_spinning(True)
        self.stack.set_visible_child(self.spinner)

    def stop(self):
        self.set_sensitive(True)
        self.spinner.set_spinning(False)
        self.stack.set_visible_child(self.content)
