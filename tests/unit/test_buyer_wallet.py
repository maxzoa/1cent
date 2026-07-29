from __future__ import annotations

import pytest

from onecent import buyer_wallet

TEST_PRIVATE_KEY = "0x" + "22" * 32


class FakeKeyring:
    def __init__(self) -> None:
        self.secret: str | None = None

    def get_password(self, service_name: str, username: str) -> str | None:
        assert service_name == buyer_wallet.KEYRING_SERVICE
        assert username == buyer_wallet.KEYRING_USERNAME
        return self.secret

    def set_password(self, service_name: str, username: str, password: str) -> None:
        assert service_name == buyer_wallet.KEYRING_SERVICE
        assert username == buyer_wallet.KEYRING_USERNAME
        self.secret = password

    def delete_password(self, service_name: str, username: str) -> None:
        assert service_name == buyer_wallet.KEYRING_SERVICE
        assert username == buyer_wallet.KEYRING_USERNAME
        self.secret = None


def test_wallet_uses_os_keyring_and_reports_only_address(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = FakeKeyring()
    monkeypatch.delenv(buyer_wallet.PRIVATE_KEY_ENV, raising=False)
    monkeypatch.setattr(buyer_wallet, "_keyring", lambda: fake)

    address = buyer_wallet.store_private_key(TEST_PRIVATE_KEY)
    status = buyer_wallet.wallet_status()
    assert status.configured is True
    assert status.source == "keyring"
    assert status.address == address
    assert fake.secret == TEST_PRIVATE_KEY

    buyer_wallet.delete_private_key()
    assert buyer_wallet.wallet_status().configured is False


def test_environment_signer_is_supported_for_headless_agents(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(buyer_wallet.PRIVATE_KEY_ENV, TEST_PRIVATE_KEY)
    private_key, source = buyer_wallet.load_private_key(required=True)
    assert private_key == TEST_PRIVATE_KEY
    assert source == "environment"


def test_invalid_key_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(buyer_wallet.PRIVATE_KEY_ENV, "not-a-key")
    with pytest.raises(buyer_wallet.BuyerWalletError, match="invalid"):
        buyer_wallet.load_private_key(required=True)
