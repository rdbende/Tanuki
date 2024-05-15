# login.py
#
# SPDX-FileCopyrightText: 2024  Benedek Dévényi
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import random
import string
from dataclasses import dataclass
from typing import Callable, NoReturn, Protocol

import requests
from gi.repository import GLib, Gtk
from tanuki.architecture import async_job_finished


class InvalidCredentialsError(Exception): ...


class Login(Protocol):
    @property
    def gitlab_auth_kwargs(self) -> dict[str, str]: ...


@dataclass
class PersonalAccessTokenLogin:
    url: str
    token: str

    @property
    def gitlab_auth_kwargs(self) -> dict[str, str]:
        return {"url": self.url, "private_token": self.token}


def generate_url_parameters(parameters: dict[str, str]) -> str:
    return "&".join([f"{key}={value}" for key, value in parameters.items()])


class OAuthLoginManager:
    providers: dict[str, type[OAuthLogin]] = {}
    _login_state: dict[str, tuple[type[OAuthLogin], Callable, Callable]] = {}

    # FIXME: PKCE flow always returns a HTTP 400,
    # although this code should work based on GitLab docs:
    # code_verifier = "".join(random.choices(string.ascii_letters, k=64))
    # code_sha256 = hashlib.sha256(code_verifier.encode()).digest()
    # code_challenge = base64.urlsafe_b64encode(code_sha256).decode()

    @classmethod
    def get_login_class_from_url(cls, url: str) -> type[OAuthLogin] | None:
        return cls.providers.get(url)

    @classmethod
    def redirect(cls, state: str, code: str) -> None:
        login_class, *_ = cls._login_state[state]
        cls.finish_auth_flow(requests.post, login_class._get_token_url(code), direct_args=(state,))

    @classmethod
    def access_denied(cls, state: str) -> None:
        *_, access_denied_callback = cls._login_state[state]
        access_denied_callback()

    @classmethod
    def start_auth_flow(
        cls,
        login_type: type[OAuthLogin],
        callback: Callable[[Login], None],
        access_denied_callback: Callable[[], None],
    ) -> None:
        state = "".join(random.choices(string.ascii_letters, k=16))
        cls._login_state[state] = (login_type, callback, access_denied_callback)

        url = login_type._get_authorization_url(state)
        uri_launcher = Gtk.UriLauncher(uri=url)
        uri_launcher.launch(None, None, lambda d, r: d.launch_finish(r))

    @classmethod
    @async_job_finished
    def finish_auth_flow(cls, response: requests.Response, state: str) -> None | NoReturn:
        if response.ok:
            data = response.json()
            access_token, refresh_token = data["access_token"], data["refresh_token"]
        else:
            raise InvalidCredentialsError

        login_type, callback, _ = cls._login_state[state]
        callback(login_type(access_token, refresh_token))


class OAuthLogin:
    _client_id: str
    _base_url: str
    icon: str
    display_name: str

    def __init_subclass__(cls):
        super().__init_subclass__()
        OAuthLoginManager.providers[cls._base_url] = cls

    def __init__(self, access_token: str | None = None, refresh_token: str | None = None) -> None:
        self.access_token = access_token
        self.refresh_token = refresh_token

    @property
    def gitlab_auth_kwargs(self) -> dict[str, str] | NoReturn:
        if self.access_token:
            return {"url": self._base_url, "oauth_token": self.access_token}
        else:
            raise InvalidCredentialsError

    @property
    def url(self) -> str:
        return self._base_url

    @classmethod
    def _get_authorization_url(cls, state: str) -> str:
        parameters = {
            "client_id": cls._client_id,
            "redirect_uri": GLib.Uri.escape_string("tanuki://callback", "/", True),
            "response_type": "code",
            "scope": "api",
            "state": state,
        }

        return f"{cls._base_url}/oauth/authorize?{generate_url_parameters(parameters)}"

    @classmethod
    def _get_token_url(cls, code: str) -> str:
        parameters = {
            "client_id": cls._client_id,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": GLib.Uri.escape_string("tanuki://callback", "/", True),
        }

        return f"{cls._base_url}/oauth/token?{generate_url_parameters(parameters)}"

    def _get_refresh_url(self):
        verifier = "".join(random.choices(string.ascii_letters, k=64))
        parameters = {
            "client_id": self._client_id,
            "refresh_token": self.refresh_token,
            "code_verifier": verifier,  # FIXME: why does this work?
            "grant_type": "refresh_token",
            "redirect_uri": GLib.Uri.escape_string("tanuki://callback", "/", True),
        }

        return f"{self._base_url}/oauth/token?{generate_url_parameters(parameters)}"

    def refresh_access_token(self) -> None | NoReturn:
        url = self._get_refresh_url()
        response = requests.post(url)

        if response.ok:
            data = response.json()

            self.access_token = data["access_token"]
            self.refresh_token = data["refresh_token"]
        else:
            raise InvalidCredentialsError


class GitLabDotComOAuthLogin(OAuthLogin):
    _client_id = "69cf882b9dbec27f748a4fada7cf82d392b564025d340b69f3b868c5119a86cb"
    _base_url = "https://gitlab.com"
    icon = "gitlab-fullcolor"
    display_name = "GitLab.com"
