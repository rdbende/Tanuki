# tools.py
#
# SPDX-FileCopyrightText: 2024  Benedek Dévényi
# SPDX-License-Identifier: GPL-3.0-or-later

from threading import Thread
from typing import Callable

import requests
from gi.repository import Gdk, Gio, GLib, GObject
from tanuki.architecture import async_job_finished


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


class RemoteImage(GObject.Object):
    image = GObject.Property(type=Gdk.Texture)

    def __init__(self, target: GObject.Object, target_property: str) -> None:
        super().__init__()
        target.connect("notify::" + target_property, self.update_image)

    def bind_to(self, target: GObject.Object, target_property: str) -> None:
        self.bind_property("image", target, target_property)

    def update_image(self, source: GObject.Object, param: GObject.ParamSpec) -> None:
        if url := source.get_property(param.name):
            self.do_update_image(RemoteImages.download, url)

    @async_job_finished
    def do_update_image(self, image: Gdk.Texture) -> None:
        self.props.image = image
