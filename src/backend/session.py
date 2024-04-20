import hashlib
import json

import gitlab
from gi.repository import GObject
from tanuki import settings
from tanuki.tools import run_in_thread, threaded


class SessionManager:
    @classmethod
    def get_session_id(cls, gitlab: gitlab.Gitlab) -> str:
        some_string = (gitlab.url + gitlab.user.username).encode()
        return hashlib.md5(some_string).hexdigest()

    @classmethod
    def get_session_from_id(cls, id: str) -> dict[str, str]:
        return cls.get_sessions()[id]

    @staticmethod
    def get_sessions() -> dict[str, dict[str, str]]:
        serialized_sessions = settings.get_string("sessions")
        return json.loads(serialized_sessions)

    @classmethod
    def save_session(cls, gitlab) -> None:
        sessions = cls.get_sessions()
        sessions[cls.get_session_id(gitlab)] = {
            "token": gitlab.private_token,
            "username": gitlab.user.username,
            "name": gitlab.user.name,
            "url": gitlab.url,
            "avatar": gitlab.user.avatar_url,
        }

        serialized_sessions = json.dumps(sessions)
        settings.set_string("sessions", serialized_sessions)

    @classmethod
    def authenticate(cls, gitlab: gitlab.Gitlab) -> bool:
        try:
            gitlab.auth()
        except Exception:
            return False

        if cls.get_session_id(gitlab) not in cls.get_sessions():
            cls.save_session(gitlab)

        settings.set_string("current-session", cls.get_session_id(gitlab))

        return True


class Tanuki(GObject.Object):
    @GObject.Signal
    def login_completed(self): ...

    @GObject.Signal
    def login_failed(self): ...

    @GObject.Signal
    def login_started(self): ...

    def _authenticate(self, *args):
        self.emit("login-started")
        if SessionManager.authenticate(self.gl):
            self.emit("login-completed")
        else:
            self.emit("login-failed")

    def login(self, **kwargs):
        self.gl = gitlab.Gitlab(**kwargs)
        run_in_thread(self._authenticate)

    def start_session(self, session_id: str):
        data = SessionManager.get_session_from_id(session_id)
        self.gl = gitlab.Gitlab(url=data["url"], private_token=data["token"])
        run_in_thread(self._authenticate)

    @threaded
    def print_user(self, *_):
        print(self.gl.user)

    @property
    def logged_in(self) -> bool:
        return hasattr(self, "gl")


session = Tanuki()
