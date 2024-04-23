# settings.py
#
# SPDX-FileCopyrightText: 2024  Benedek Dévényi
# SPDX-License-Identifier: GPL-3.0-or-later


from gi.repository import Gio, GObject


class TanukiSettings(Gio.Settings):
    current_session = GObject.Property(type=str)
    sessions = GObject.Property(type=str)

    def __init__(self):
        super().__init__("io.github.rdbende.Tanuki")

        bind_settings = lambda setting, propetry: self.bind(
            setting, self, propetry, Gio.SettingsBindFlags.DEFAULT
        )

        bind_settings("sessions", "sessions")
        bind_settings("current-session", "current-session")


settings = TanukiSettings()
