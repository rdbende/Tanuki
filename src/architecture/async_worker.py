# async.py
#
# SPDX-FileCopyrightText: 2024  Benedek Dévényi
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Gio, GObject
from typing import Callable


class AsyncWorker(GObject.Object):
    def __init__(
        self,
        *args,
        operation=None,
        callback=None,
        **kwargs
    ):
        super().__init__()
        self.operation = operation
        self.callback = callback
        self.data = {"args": args, "kwargs": kwargs}

    def _thread_callback(self, task, worker, *_):
        result = self.operation(*self.data["args"], **self.data["kwargs"])
        task.return_value(result)

    def start(self):
        task = Gio.Task.new(self, None, self.callback, None)
        task.run_in_thread(self._thread_callback)

    def finish(self, result):
        if Gio.Task.is_valid(result, self):
            return result.propagate_value().value
        else:
            raise RuntimeError("Gio.Task.is_valid() returned False")


def async_job_finished(func: Callable):
    def wrapper(self, op: Callable, *args, **kwargs):
        def cb(w, r, _):
            func(self, w.finish(r))
        AsyncWorker(*args, operation=op, callback=cb, **kwargs).start()

    return wrapper
