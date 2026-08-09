from functools import lru_cache
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: Literal["development", "test", "production"] = "development"
    app_name: str = "1cent"
    app_port: int = 8013
    app_timezone: str = "Asia/Almaty"
    public_base_url: str = "https://1cent.maxzoa.ru"
    database_url: str = "postgresql+asyncpg://onecent:local_dev_only@onecent-db:5432/onecent"
    telegram_bot_token: str = "CHANGE_ME"
    telegram_admin_ids: str = "123456789"
    telegram_report_chat_id: int = 123456789
    internal_api_token: str = "CHANGE_ME_LONG_RANDOM_VALUE"
    audit_hash_salt: str = ""
    audit_owner_buyer_addresses: str = ""
    service_enabled: bool = True
    emergency_pause_force: bool = False
    maintenance_message: str = "Service temporarily paused"

    x402_enabled: bool = True
    deployment_profile: Literal[
        "testnet",
        "mainnet-disabled",
        "production-candidate-cdp",
        "production-candidate-payai",
        "production-candidate-thirdweb",
    ] = "testnet"
    x402_environment: Literal["testnet", "mainnet"] = "testnet"
    x402_network: Literal["eip155:84532", "eip155:8453"] = "eip155:84532"
    x402_facilitator_url: str = "https://x402.org/facilitator"
    x402_asset: str = "0x036CbD53842c5426634e7929541eC2318f3dCF7e"
    x402_pay_to: str = "0x0000000000000000000000000000000000000000"
    development_bypass_enabled: bool = True
    x402_idempotency_ttl_seconds: int = 86400
    owner_mainnet_approved: bool = False
    seller_address_confirmed: bool = False
    owner_price_floor_approved: bool = False
    mainnet_backup_path: str = "/backups/onecent-latest.sql.gz"
    mainnet_backup_max_age_hours: int = 24
    mainnet_daily_settlement_limit_enabled: bool = False
    mainnet_daily_revenue_limit_enabled: bool = False
    mainnet_daily_settlement_limit: int = 10
    mainnet_daily_revenue_limit_atomic: int = 1_000_000
    cdp_api_key_id: str = "PLACEHOLDER"
    cdp_api_key_secret: str = "PLACEHOLDER"
    payai_api_key_id: str = "PLACEHOLDER"
    payai_api_key_secret: str = "PLACEHOLDER"
    thirdweb_secret_key: str = "PLACEHOLDER"
    thirdweb_server_wallet: str = "PLACEHOLDER"

    cost_facilitator_fee_usd: str = "0"
    cost_rpc_usd: str = "0"
    cost_fetch_usd: str = "0.0002"
    cost_margin_target_usd: str = "0.001"
    price_floor_pulse_usd: str = "0.003"
    price_floor_passport_usd: str = "0.010"
    price_floor_extract_usd: str = "0.010"
    price_floor_changed_usd: str = "0.003"

    price_pulse_usd: str = "0.003"
    price_passport_usd: str = "0.010"
    price_extract_usd: str = "0.010"
    price_changed_usd: str = "0.003"
    cache_pulse_ttl_seconds: int = 3600
    cache_passport_ttl_seconds: int = 21600
    cache_extract_ttl_seconds: int = 21600
    fetch_connect_timeout_seconds: float = 3
    fetch_read_timeout_seconds: float = 8
    fetch_total_timeout_seconds: float = 12
    fetch_max_redirects: int = 5
    fetch_max_body_bytes: int = 2_097_152
    fetch_max_extracted_text_bytes: int = 262_144
    fetch_allowed_ports: str = "80,443"
    fetch_user_agent: str = "1cent/0.1 (+https://1cent.maxzoa.ru/info)"
    demo_live_target_url: Literal["https://example.com/"] = "https://example.com/"
    demo_live_rate_per_hour: int = 3
    trial_preview_rate_per_day: int = 1
    offer_receipt_enabled: bool = False
    offer_receipt_signing_key_path: str = "/run/secrets/offer_receipt_ed25519.pem"
    offer_receipt_kid: str = "did:web:1cent.maxzoa.ru#offer-receipt-key-1"
    offer_receipt_include_transaction: bool = False

    @property
    def admin_ids(self) -> frozenset[int]:
        return frozenset(
            int(value.strip()) for value in self.telegram_admin_ids.split(",") if value.strip()
        )

    @property
    def allowed_ports(self) -> frozenset[int]:
        return frozenset(
            int(value.strip()) for value in self.fetch_allowed_ports.split(",") if value.strip()
        )

    @property
    def owner_buyer_addresses(self) -> frozenset[str]:
        return frozenset(
            value.strip().lower()
            for value in self.audit_owner_buyer_addresses.split(",")
            if value.strip()
        )

    @model_validator(mode="after")
    def validate_safety(self) -> "Settings":
        if not 1 <= self.demo_live_rate_per_hour <= 20:
            raise ValueError("DEMO_LIVE_RATE_PER_HOUR must be between 1 and 20")
        if not 1 <= self.trial_preview_rate_per_day <= 5:
            raise ValueError("TRIAL_PREVIEW_RATE_PER_DAY must be between 1 and 5")
        if self.offer_receipt_enabled and not self.offer_receipt_kid.startswith("did:web:"):
            raise ValueError("OFFER_RECEIPT_KID must use did:web")
        if self.app_env == "production" and self.development_bypass_enabled:
            raise ValueError("development bypass is forbidden in production")
        if not self.x402_pay_to.startswith("0x") or len(self.x402_pay_to) != 42:
            raise ValueError("X402_PAY_TO must be a public EVM address")
        if self.app_env == "production" and self.x402_pay_to == "0x" + "0" * 40:
            raise ValueError("X402_PAY_TO must be configured in production")
        if self.x402_network == "eip155:8453":
            from onecent.services.readiness import mainnet_blockers

            blockers = mainnet_blockers(self)
            if blockers:
                raise ValueError("mainnet readiness blocked: " + "; ".join(blockers))
        elif self.x402_environment != "testnet" or self.x402_network != "eip155:84532":
            raise ValueError("safe mode requires testnet eip155:84532")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
