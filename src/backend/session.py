# session.py
#
# SPDX-FileCopyrightText: 2024  Benedek Dévényi
# SPDX-License-Identifier: GPL-3.0-or-later


import hashlib
import json

import gitlab
from gi.repository import Gio, GObject, Secret
from tanuki.tools import async_job_finished, run_in_thread

from .login import Login
from .settings import settings

schema = Secret.Schema.new(
    "io.github.rdbende.Tanuki",
    Secret.SchemaFlags.NONE,
    {"session-id": Secret.SchemaAttributeType.STRING},
)


class SessionManager:
    # TODO: make this class private, at least somewhat
    _sessions = {}

    @classmethod
    def get_session_id(cls, gitlab: gitlab.Gitlab) -> str:
        some_string = (gitlab.url + gitlab.user.username).encode()
        return hashlib.md5(some_string).hexdigest()

    @classmethod
    def get_session_from_id(cls, id: str) -> dict[str, str]:
        return cls.get_sessions()[id]

    @classmethod
    def _cache_sessions(cls, *_) -> None:
        serialized_sessions = settings.props.sessions
        cls._sessions = json.loads(serialized_sessions)

    @classmethod
    def get_sessions(cls) -> dict[str, dict[str, str]]:
        if not cls._sessions:
            settings.connect("notify::sessions", cls._cache_sessions)
            cls._cache_sessions()
        return cls._sessions

    @classmethod
    def any_sessions(cls) -> bool:
        return len(cls.get_sessions()) > 0

    @classmethod
    def get_avatar_url_for_session(cls, session: str) -> str:
        return cls.get_session_from_id(session)["avatar"]

    @classmethod
    def save_secret(cls, session_id: str, description: str, secret: str) -> None:
        Secret.password_store(
            schema,
            {"session-id": session_id},
            Secret.COLLECTION_DEFAULT,
            description,
            secret,
            None,
            lambda _, task: Secret.password_store_finish(task),
        )

    @classmethod
    def delete_secret(cls, session_id: str) -> None:
        Secret.password_clear(
            schema,
            {"session-id": session_id},
            None,
            lambda _, task: Secret.password_clear_finish(task),
        )

    @classmethod
    def save_session(cls, gitlab: gitlab.Gitlab) -> None:
        sessions = cls.get_sessions()
        session_id = cls.get_session_id(gitlab)

        cls.save_secret(session_id, f"{gitlab.user.username} at {gitlab.url}", gitlab.private_token)

        sessions[session_id] = {
            "username": gitlab.user.username,
            "name": gitlab.user.name,
            "url": gitlab.url,
            "avatar": gitlab.user.avatar_url,
        }

        serialized_sessions = json.dumps(sessions)
        settings.props.sessions = serialized_sessions

    @classmethod
    def delete_session(cls, session_id: str) -> None:
        sessions = cls.get_sessions()
        sessions.pop(session_id)

        cls.delete_secret(session_id)

        serialized_sessions = json.dumps(sessions)
        settings.props.sessions = serialized_sessions
        settings.props.current_session = ""

    @classmethod
    def create_session_if_not_exists(cls, gitlab: gitlab.Gitlab) -> str:
        session_id = cls.get_session_id(gitlab)
        if session_id not in cls.get_sessions():
            cls.save_session(gitlab)

        return session_id


class Tanuki(GObject.Object):
    # Signals
    @GObject.Signal
    def login_completed(self): ...

    @GObject.Signal
    def login_failed(self): ...

    @GObject.Signal
    def login_started(self): ...

    def _check_login(self, gitlab: gitlab.Gitlab) -> bool:
        try:
            gitlab.auth()
        except Exception:
            return False
        else:
            return True

    def _authenticate(self, *_) -> None:
        self.emit("login-started")
        if self._check_login(self._gitlab):
            settings.props.current_session = SessionManager.get_session_id(self._gitlab)
            self.emit("login-completed")
        else:
            self.emit("login-failed")

    def create_session(self, login: Login) -> None:
        self._gitlab = gitlab.Gitlab(**login.gitlab_auth_kwargs)
        self._save_and_start_session(self._check_login, self._gitlab)

    @async_job_finished
    def _save_and_start_session(self, auth_succeded: bool) -> None:
        if auth_succeded:
            session_id = SessionManager.create_session_if_not_exists(self._gitlab)
            self.start_session(session_id, _dont_reload_if_token_is_none=True)
        else:
            self.emit("login-failed")

    def start_session(
        self, session_id: str, *, _dont_reload_if_token_is_none: bool = False
    ) -> None:
        url = SessionManager.get_session_from_id(session_id)["url"]

        def finish(_, task: Gio.Task) -> None:
            token = Secret.password_lookup_finish(task)

            if token is None and _dont_reload_if_token_is_none:
                # This sucks, I know, but the keyring is being slow sometimes when storing secrets
                settings.props.current_session = SessionManager.get_session_id(self._gitlab)
                self.emit("login-completed")
                return
            else:
                self._gitlab = gitlab.Gitlab(url=url, private_token=token)
                run_in_thread(self._authenticate)

        Secret.password_lookup(schema, {"session-id": session_id}, None, finish)

    def remove_session(self, session_id: str) -> None:
        self._gitlab = None
        SessionManager.delete_session(session_id)


session = Tanuki()
