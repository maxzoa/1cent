from __future__ import annotations

import importlib
import os
from dataclasses import dataclass
from typing import Protocol, cast

from eth_account import Account

KEYRING_SERVICE = "onecent-buyer"
KEYRING_USERNAME = "base-mainnet"
PRIVATE_KEY_ENV = "ONECENT_BUYER_PRIVATE_KEY"


class BuyerWalletError(RuntimeError):
    pass


class _Keyring(Protocol):
    def get_password(self, service_name: str, username: str) -> str | None: ...

    def set_password(self, service_name: str, username: str, password: str) -> None: ...

    def delete_password(self, service_name: str, username: str) -> None: ...


@dataclass(frozen=True)
class WalletStatus:
    configured: bool
    source: str | None
    address: str | None


def _keyring() -> _Keyring:
    try:
        module = importlib.import_module("keyring")
    except ImportError as exc:
        raise BuyerWalletError(
            "secure wallet store unavailable; install the buyer extra: onecent[buyer]"
        ) from exc
    return cast(_Keyring, module)


def _validated_key(private_key: str) -> tuple[str, str]:
    value = private_key.strip()
    try:
        address = str(Account.from_key(value).address)
    except Exception as exc:
        raise BuyerWalletError("buyer private key is invalid") from exc
    return value, address


def store_private_key(private_key: str) -> str:
    value, address = _validated_key(private_key)
    try:
        _keyring().set_password(KEYRING_SERVICE, KEYRING_USERNAME, value)
    except Exception as exc:
        raise BuyerWalletError("OS keyring refused the buyer wallet secret") from exc
    return address


def delete_private_key() -> None:
    try:
        _keyring().delete_password(KEYRING_SERVICE, KEYRING_USERNAME)
    except Exception as exc:
        raise BuyerWalletError("buyer wallet secret was not found or could not be deleted") from exc


def load_private_key(*, required: bool) -> tuple[str | None, str | None]:
    environment_value = os.getenv(PRIVATE_KEY_ENV)
    if environment_value:
        value, _ = _validated_key(environment_value)
        return value, "environment"
    try:
        stored = _keyring().get_password(KEYRING_SERVICE, KEYRING_USERNAME)
    except BuyerWalletError:
        if required:
            raise
        return None, None
    except Exception as exc:
        if required:
            raise BuyerWalletError("OS keyring could not read the buyer wallet secret") from exc
        return None, None
    if not stored:
        if required:
            raise BuyerWalletError("buyer wallet is not configured; run: onecent wallet set")
        return None, None
    value, _ = _validated_key(stored)
    return value, "keyring"


def wallet_status() -> WalletStatus:
    private_key, source = load_private_key(required=False)
    if not private_key:
        return WalletStatus(configured=False, source=None, address=None)
    _, address = _validated_key(private_key)
    return WalletStatus(configured=True, source=source, address=address)
