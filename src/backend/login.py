# login.py
#
# SPDX-FileCopyrightText: 2024  Benedek Dévényi
# SPDX-License-Identifier: GPL-3.0-or-later

from dataclasses import dataclass
from typing import Protocol


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
