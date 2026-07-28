from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE_MAINNET_USDC = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
PRODUCTION_FACILITATORS = {
    "production-candidate-cdp": "https://api.cdp.coinbase.com/platform/v2/x402",
    "production-candidate-payai": "https://facilitator.payai.network",
    "production-candidate-thirdweb": "https://api.thirdweb.com/v1/payments/x402",
}
PLACEHOLDER_VALUES = {"", "PLACEHOLDER", "CHANGE_ME"}


def backup_age_hours(path: str, now: datetime | None = None) -> float | None:
    backup = Path(path)
    if not backup.is_file():
        return None
    current = now or datetime.now(timezone.utc)
    modified = datetime.fromtimestamp(backup.stat().st_mtime, timezone.utc)
    return max(0.0, (current - modified).total_seconds() / 3600)


def _credentials_ready(settings: Any) -> bool:
    values: tuple[str, ...]
    if settings.deployment_profile == "production-candidate-cdp":
        values = (settings.cdp_api_key_id, settings.cdp_api_key_secret)
    elif settings.deployment_profile == "production-candidate-payai":
        if settings.payai_api_key_id == "" and settings.payai_api_key_secret == "":
            return True
        values = (settings.payai_api_key_id, settings.payai_api_key_secret)
    elif settings.deployment_profile == "production-candidate-thirdweb":
        values = (settings.thirdweb_secret_key, settings.thirdweb_server_wallet)
    else:
        return False
    return all(value not in PLACEHOLDER_VALUES for value in values)


def mainnet_blockers(settings: Any, now: datetime | None = None) -> list[str]:
    blockers: list[str] = []
    expected_url = PRODUCTION_FACILITATORS.get(settings.deployment_profile)
    checks = (
        (settings.owner_mainnet_approved, "OWNER_MAINNET_APPROVED is not true"),
        (settings.app_env == "production", "APP_ENV is not production"),
        (settings.x402_environment == "mainnet", "X402_ENVIRONMENT is not mainnet"),
        (settings.x402_network == "eip155:8453", "X402_NETWORK is not eip155:8453"),
        (settings.x402_asset.lower() == BASE_MAINNET_USDC.lower(), "Base USDC contract mismatch"),
        (expected_url is not None, "production facilitator profile is not allowed"),
        (expected_url == settings.x402_facilitator_url, "production facilitator URL mismatch"),
        (not settings.development_bypass_enabled, "development bypass is enabled"),
        (_credentials_ready(settings), "production credentials are missing"),
        (settings.seller_address_confirmed, "seller address is not confirmed"),
        (
            not settings.mainnet_daily_settlement_limit_enabled
            or settings.mainnet_daily_settlement_limit > 0,
            "mainnet daily settlement limit must be positive when enabled",
        ),
        (
            not settings.mainnet_daily_revenue_limit_enabled
            or settings.mainnet_daily_revenue_limit_atomic >= 10_000,
            "mainnet daily revenue limit is below one pulse payment when enabled",
        ),
        (
            settings.x402_pay_to.startswith("0x")
            and len(settings.x402_pay_to) == 42
            and settings.x402_pay_to != "0x" + "0" * 40,
            "seller address is invalid",
        ),
    )
    blockers.extend(message for passed, message in checks if not passed)
    age = backup_age_hours(settings.mainnet_backup_path, now)
    if age is None:
        blockers.append("database backup is missing")
    elif age >= settings.mainnet_backup_max_age_hours:
        blockers.append("database backup is 24h or older")
    return blockers


def short_address(address: str) -> str:
    return f"{address[:6]}...{address[-4:]}" if len(address) == 42 else "invalid"
