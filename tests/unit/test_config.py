import pytest
from pydantic import ValidationError

from onecent.config import Settings


def test_testnet_defaults() -> None:
    assert Settings(_env_file=None).x402_network == "eip155:84532"


def test_mainnet_rejected_without_owner_gates() -> None:
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            x402_environment="mainnet",
            x402_network="eip155:8453",
        )


def test_production_bypass_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            app_env="production",
            development_bypass_enabled=True,
        )


def test_production_without_bypass_allowed() -> None:
    settings = Settings(
        _env_file=None,
        app_env="production",
        development_bypass_enabled=False,
        x402_pay_to="0x1111111111111111111111111111111111111111",
    )
    assert settings.app_env == "production"


def test_mainnet_all_gates_allow_settings(tmp_path: object) -> None:
    from pathlib import Path

    backup = Path(str(tmp_path)) / "backup.dump"
    backup.write_bytes(b"safe-test-backup")
    settings = Settings(
        _env_file=None,
        deployment_profile="production-candidate-payai",
        app_env="production",
        x402_environment="mainnet",
        x402_network="eip155:8453",
        x402_asset="0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        x402_facilitator_url="https://facilitator.payai.network",
        x402_pay_to="0x1111111111111111111111111111111111111111",
        owner_mainnet_approved=True,
        seller_address_confirmed=True,
        development_bypass_enabled=False,
        mainnet_backup_path=str(backup),
        payai_api_key_id="configured-id",
        payai_api_key_secret="configured-secret",
    )
    assert settings.x402_network == "eip155:8453"
