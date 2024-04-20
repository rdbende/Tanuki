# settings.py
#
# SPDX-FileCopyrightText: 2024  Benedek Dévényi
# SPDX-License-Identifier: GPL-3.0-or-later


from gi.repository import Gio


class TanukiSettings(Gio.Settings):
    def __init__(self):
        super().__init__("io.github.rdbende.Tanuki")


settings = TanukiSettings()
