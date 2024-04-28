# session.py
#
# SPDX-FileCopyrightText: 2024  Benedek Dévényi
# SPDX-License-Identifier: GPL-3.0-or-later


import hashlib
import json
from collections import namedtuple
from typing import Callable

import gitlab
from gi.repository import Gio, GObject, Secret
from tanuki.tools import async_job_finished, run_in_thread, threaded

from .login import Login, OAuthLogin, PersonalAccessTokenLogin
from .settings import settings
from urllib.parse import urlparse

schema = Secret.Schema.new(
    "io.github.rdbende.Tanuki",
    Secret.SchemaFlags.NONE,
    {"session-id": Secret.SchemaAttributeType.STRING},
)


AccountInfo = namedtuple("AccountInfo", ["username", "name", "avatar_url", "url"])


class SessionManager:
    # TODO: make this class private, at least somewhat
    _sessions = {}

    @classmethod
    def get_session_id(cls, account_info: AccountInfo) -> str:
        id_string = account_info.url + account_info.username
        return hashlib.md5(id_string.encode()).hexdigest()

    @classmethod
    def get_session_from_id(cls, id: str) -> dict[str, str]:
        return AccountInfo(**cls.get_sessions()[id])

    @classmethod
    def any_sessions(cls) -> bool:
        return len(cls.get_sessions()) > 0

    @classmethod
    def get_sessions(cls) -> dict[str, dict[str, str]]:
        if not cls._sessions:
            cls._cache_sessions()
            settings.connect("notify::sessions", cls._cache_sessions)
        return cls._sessions

    @classmethod
    def _cache_sessions(cls, *_) -> None:
        serialized_sessions = settings.props.sessions
        cls._sessions = json.loads(serialized_sessions)

    @classmethod
    def save_login(cls, session_id: str, login: Login) -> None:
        if isinstance(login, OAuthLogin):
            secret_data = {
                "type": "oauth",
                "access_token": login.access_token,
                "refresh_token": login.refresh_token
            }
        else:
            secret_data = {"type": "pat", "access_token": login.token}

        Secret.password_store(
            schema,
            {"session-id": session_id},
            Secret.COLLECTION_DEFAULT,
            f"Login with {urlparse(login.url).netloc}",
            json.dumps(secret_data),
            None,
            lambda _, task: Secret.password_store_finish(task),
        )

    @classmethod
    def query_login(cls, session_id: str, callback: Callable[[Login], None]) -> None:
        def finish(_, task: Gio.Task) -> None:
            secret = Secret.password_lookup_finish(task)
            if secret is None:
                callback(None)
                return

            account_info = SessionManager.get_session_from_id(session_id)
            data = json.loads(secret)
            if data["type"] == "oauth":
                login = OAuthLogin(account_info.url, data["access_token"], data["refresh_token"])
            else:
                login = PersonalAccessTokenLogin(account_info.url, data["access_token"])

            callback(login)

        Secret.password_lookup(schema, {"session-id": session_id}, None, finish)

    @classmethod
    def delete_secret(cls, session_id: str) -> None:
        Secret.password_clear(
            schema,
            {"session-id": session_id},
            None,
            lambda _, task: Secret.password_clear_finish(task),
        )

    @classmethod
    def delete_session(cls, session_id: str) -> None:
        sessions = cls.get_sessions()
        sessions.pop(session_id)

        cls.delete_secret(session_id)

        serialized_sessions = json.dumps(sessions)
        settings.props.sessions = serialized_sessions
        settings.props.current_session = ""

    @classmethod
    def create_session_if_not_exists(cls, account_info: AccountInfo, login: Login) -> str:
        session_id = cls.get_session_id(account_info)
        sessions = cls.get_sessions()

        if session_id in sessions:
            return session_id

        cls.save_login(session_id, login)

        sessions[session_id] = {
            "username": account_info.username,
            "name": account_info.name,
            "avatar_url": account_info.avatar_url,
            "url": account_info.url,
        }

        serialized_sessions = json.dumps(sessions)
        settings.props.sessions = serialized_sessions

        return session_id


class Tanuki(GObject.Object):
    # Signals
    @GObject.Signal
    def login_started(self): ...

    @GObject.Signal
    def login_completed(self): ...

    @GObject.Signal
    def login_failed(self): ...

    def _validate_login(self, login: Login) -> bool:
        gitlab_ = gitlab.Gitlab(**login.gitlab_auth_kwargs)
        try:
            gitlab_.auth()
        except Exception:
            return None
        else:
            self._gitlab = gitlab_
            return login

    def create_session(self, login: Login) -> None:
        self._save_and_start_session(self._validate_login, login)

    @async_job_finished
    def _save_and_start_session(self, login: Login) -> None:
        if login is None:
            self.emit("login-failed")
            return

        session_id = SessionManager.create_session_if_not_exists(self.get_account_info(), login)
        self.start_session(session_id, _fallback_login_if_keyring_is_slow=login)

    def start_session(
        self, session_id: str, *, refresh_oauth_token: bool = False, _fallback_login_if_keyring_is_slow: Login | None = None
    ) -> None:
        self.emit("login-started")

        @threaded
        def login_queried_callback(login: Login) -> None:
            if refresh_oauth_token:
                login.refresh_access_token()
                SessionManager.save_login(session_id, login)

            self._manage_login_ui(login or _fallback_login_if_keyring_is_slow)

        SessionManager.query_login(session_id, login_queried_callback)

    def _manage_login_ui(self, login: Login) -> None:
        if self._validate_login(login) is not None:
            settings.props.current_session = SessionManager.get_session_id(self.get_account_info())
            self.emit("login-completed")
        else:
            self.emit("login-failed")

    def remove_session(self, session_id: str) -> None:
        self._gitlab = None
        SessionManager.delete_session(session_id)

    def get_user(self, username: str):
        return self._gitlab.users.get(self._gitlab.users.list(username=username)[0].id)

    def get_account_info(self):
        return AccountInfo(
            username=self._gitlab.user.username,
            name=self._gitlab.user.name,
            avatar_url=self._gitlab.user.avatar_url,
            url=self._gitlab.url,
        )


session = Tanuki()
