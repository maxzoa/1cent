from pathlib import Path


def test_backup_script_restricts_directory_and_dump_permissions() -> None:
    script = (
        Path(__file__).resolve().parents[2] / "scripts" / "backup_db.sh"
    ).read_text(encoding="utf-8")

    assert "umask 077" in script
    assert 'chmod 711 "$BACKUP_DIR"' in script
    assert 'chmod 600 "$TARGET"' in script
    assert 'LATEST="$BACKUP_DIR/onecent-latest.sql.gz"' in script
    assert 'ln "$TARGET" "$LATEST_TMP"' in script
    assert 'mv -f "$LATEST_TMP" "$LATEST"' in script
    assert "! -name 'onecent-latest.sql.gz'" in script


def test_monitor_reads_only_safe_runtime_environment() -> None:
    script = (
        Path(__file__).resolve().parents[2] / "scripts" / "monitor_mainnet_health.sh"
    ).read_text(encoding="utf-8")

    assert "from onecent.config import get_settings" not in script
    assert '"$APP_ENV" "$X402_ENVIRONMENT" "$X402_NETWORK"' in script
    assert '"$OWNER_MAINNET_APPROVED"' in script


def test_marketplace_deploy_uses_canonical_backup_without_echoing_env() -> None:
    script = (
        Path(__file__).resolve().parents[2] / "scripts" / "deploy_marketplace_050.sh"
    ).read_text(encoding="utf-8")

    assert "sh scripts/restore_drill.sh backups/onecent-latest.sql.gz" in script
    assert "set_env_value MAINNET_BACKUP_PATH /backups/onecent-latest.sql.gz" in script
    assert "cp .env .env.production.marketplace-050.saved" in script
    assert "cat .env" not in script
