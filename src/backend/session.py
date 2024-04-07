from threading import Thread
from typing import Callable

import gitlab
from gi.repository import GObject


def threaded(func: Callable):
    def wrapper(*args, **kwargs):
        thread = Thread(target=func, args=args, kwargs=kwargs)
        thread.start()
        return None

    return wrapper


def run_in_thread(func: Callable, *args, **kwargs):
    Thread(target=func, args=args, kwargs=kwargs).start()


class __TanukiSession(GObject.Object):
    @GObject.Signal
    def login_completed(self): ...

    @GObject.Signal
    def login_failed(self): ...

    def __auth(self):
        try:
            self.gl.auth()
        except Exception:
            self.emit("login-failed")
        else:
            self.emit("login-completed")

    def login(self, **kwargs):
        self.gl = gitlab.Gitlab(**kwargs)
        run_in_thread(self.__auth)

    @threaded
    def print_user(self, *_):
        print(self.gl.user)


session = __TanukiSession()
