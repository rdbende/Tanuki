# tools.py
#
# SPDX-FileCopyrightText: 2024  Benedek Dévényi
# SPDX-License-Identifier: GPL-3.0-or-later

from threading import Thread
from typing import Callable

import requests
from gi.repository import Gdk, Gio, GLib


def threaded(func: Callable):
    def wrapper(*args, **kwargs):
        thread = Thread(target=func, args=args, kwargs=kwargs)
        thread.start()
        return None

    return wrapper


def run_in_thread(func: Callable, *args, **kwargs):
    Gio.Task().run_in_thread(lambda *_: func(*args, **kwargs))


class RemoteImages:
    _downloaded_images = {}

    @classmethod
    def download(cls, image_url: str) -> None:
        if image_url in cls._downloaded_images:
            return cls._downloaded_images[image_url]

        content = requests.get(image_url).content
        image = Gdk.Texture.new_from_bytes(GLib.Bytes(content))
        cls._downloaded_images[image_url] = image
        return image
