# tools.py
#
# SPDX-FileCopyrightText: 2024  Benedek Dévényi
# SPDX-License-Identifier: GPL-3.0-or-later

from threading import Thread
from typing import Callable

from gi.repository import Gio


def threaded(func: Callable):
    def wrapper(*args, **kwargs):
        thread = Thread(target=func, args=args, kwargs=kwargs)
        thread.start()
        return None

    return wrapper


def run_in_thread(func: Callable, *args, **kwargs):
    Gio.Task().run_in_thread(lambda *_: func(*args, **kwargs))
