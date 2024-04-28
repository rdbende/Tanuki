# login.py
#
# SPDX-FileCopyrightText: 2024  Benedek Dévényi
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import base64
import hashlib
import random
import string
from dataclasses import dataclass
from typing import Callable, NoReturn, Protocol

import requests
from gi.repository import GLib, Gtk
from tanuki.tools import async_job_finished


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


# TODO: remove duct tape
class OAuthLogin:
    # FIXME: PKCE flow always returns a HTTP 400
    _instances = {}
    providers = {}

    def __init_subclass__(cls):
        super().__init_subclass__()
        OAuthLogin.providers[cls._base_url] = cls

    def __new__(
        cls,
        url: str | None = None,
        access_token: str | None = None,
        refresh_token: str | None = None
    ) -> OAuthLogin:
        klass = OAuthLogin.providers[url] if url else cls
        return super(OAuthLogin, klass).__new__(klass)

    def __init__(
        self,
        url: str | None = None,
        access_token: str | None = None,
        refresh_token: str | None = None,
    ) -> None:
        self.url = url
        self.access_token = access_token
        self.refresh_token = refresh_token

        self.callback = lambda _: None
        self.access_denied_callback = lambda _: None

        self._state = str(id(self))
        OAuthLogin._instances[self._state] = self

        self._code_verifier = "".join(random.choices(string.ascii_letters, k=64))
        code_sha256 = hashlib.sha256(self._code_verifier.encode()).digest()
        self._code_challenge = base64.urlsafe_b64encode(code_sha256).decode()

    def _construct_authorization_url(self):
        parameters = {
            "client_id": self._client_id,
            # "code_challenge_method": "S256",
            # "code_challenge": self._code_challenge,
            "redirect_uri": GLib.Uri.escape_string("tanuki://callback", "/", True),
            "response_type": "code",
            "scope": "api",
            "state": self._state,
        }

        return f"{self._base_url}/oauth/authorize?{generate_url_parameters(parameters)}"

    def _construct_token_url(self, code: str):
        parameters = {
            "client_id": self._client_id,
            "code": code,
            # "code_verifier": self._code_verifier,
            "grant_type": "authorization_code",
            "redirect_uri": GLib.Uri.escape_string("tanuki://callback", "/", True),
        }

        return f"{self._base_url}/oauth/token?{generate_url_parameters(parameters)}"

    def _construct_refresh_url(self, refresh_token: str):
        parameters = {
            "client_id": self._client_id,
            "refresh_token": refresh_token,
            "code_verifier": self._code_verifier,  # FIXME: why does this work?
            "grant_type": "refresh_token",
            "redirect_uri": GLib.Uri.escape_string("tanuki://callback", "/", True),
        }

        return f"{self._base_url}/oauth/token?{generate_url_parameters(parameters)}"

    @classmethod
    def redirect(cls, state: str, code: str) -> None:
        instance = cls._instances.get(state)
        if instance is not None:
            instance.continue_auth_flow(code)

    @classmethod
    def access_denied(cls, state: str) -> None:
        instance = cls._instances.get(state)
        if instance is not None:
            instance.access_denied_callback()

    def refresh_access_token(self):
        url = self._construct_refresh_url(self.refresh_token)
        response = requests.post(url)

        if response.ok:
            data = response.json()

            self.access_token = data["access_token"]
            self.refresh_token = data["refresh_token"]
        else:
            raise InvalidCredentialsError

    def start_auth_flow(
        self, callback: Callable[[Login], None], access_denied_callback: Callable[[], None]
    ):
        self.callback = callback
        self.access_denied_callback = access_denied_callback
        url = self._construct_authorization_url()
        uri_launcher = Gtk.UriLauncher(uri=url)
        uri_launcher.launch(None, None, lambda d, r: d.launch_finish(r))

    def continue_auth_flow(self, code: str) -> None:
        self.finish_auth_flow(requests.post, self._construct_token_url(code))

    @async_job_finished
    def finish_auth_flow(self, response) -> None | NoReturn:
        if response.ok:
            data = response.json()

            self.url = self._base_url
            self.access_token = data["access_token"]
            self.refresh_token = data["refresh_token"]
        else:
            raise InvalidCredentialsError

        self.callback(self)

    @property
    def gitlab_auth_kwargs(self) -> dict[str, str] | NoReturn:
        if self.access_token:
            return {"url": self.url, "oauth_token": self.access_token}
        else:
            raise InvalidCredentialsError


class GitLabDotComOAuthLogin(OAuthLogin):
    _client_id = "69cf882b9dbec27f748a4fada7cf82d392b564025d340b69f3b868c5119a86cb"
    _base_url = "https://gitlab.com"
    icon = "gitlab-fullcolor"
    display_name = "GitLab.com"
