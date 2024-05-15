# async_utils.py
#
# SPDX-FileCopyrightText: 2024  Benedek Dévényi
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from threading import Thread
from typing import Callable

from gi.repository import Gio, GLib, GObject


class AsyncWorker(GObject.Object):
    def __init__(
        self,
        *args,
        operation: Callable,
        callback: Callable[[AsyncWorker, Gio.Task, None], None] = None,
        **kwargs,
    ):
        super().__init__()
        self.operation = operation
        self.callback = callback
        self.data = {"args": args, "kwargs": kwargs}

    def _thread_callback(self, task, worker, *_):
        try:
            result = self.operation(*self.data["args"], **self.data["kwargs"])
        except Exception as e:
            task.return_error(GLib.Error(str(e)))
        else:
            task.return_value(result)

    def start(self):
        task = Gio.Task.new(self, None, self.callback, None)
        task.run_in_thread(self._thread_callback)

    def finish(self, result):
        if Gio.Task.is_valid(result, self):
            try:
                result = result.propagate_value().value
            except Exception as e:
                print(e)
            else:
                return result
        else:
            raise RuntimeError("Gio.Task.is_valid() returned False")


def async_job_finished(func: Callable):
    def wrapper(self, op: Callable, *args, **kwargs):
        direct_args = kwargs.pop("direct_args", ())

        def cb(w, r, _):
            func(self, w.finish(r), *direct_args)

        AsyncWorker(*args, operation=op, callback=cb, **kwargs).start()

    return wrapper


def threaded(func: Callable):
    def wrapper(*args, **kwargs):
        thread = Thread(target=func, args=args, kwargs=kwargs)
        thread.start()
        return None

    return wrapper


def run_in_thread(func: Callable, *args, **kwargs):
    Gio.Task().run_in_thread(lambda *_: func(*args, **kwargs))
