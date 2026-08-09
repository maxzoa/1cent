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


def test_backup_sidecar_is_bounded_and_does_not_use_docker_socket() -> None:
    root = Path(__file__).resolve().parents[2]
    script = (root / "scripts" / "backup_db_container.sh").read_text(encoding="utf-8")
    compose = (root / "docker-compose.yml").read_text(encoding="utf-8")

    assert "BACKUP_INTERVAL_SECONDS" in script
    assert "pg_dump" in script
    assert "umask 077" in script
    assert "onecent-latest.sql.gz" in script
    assert "onecent-backup:" in compose
    assert 'user: "${BACKUP_UID:-1026}:${BACKUP_GID:-100}"' in compose
    assert 'user: "0:0"' not in compose
    assert "backup_db_container.sh:/scripts/backup_db_container.sh:ro" in compose
    assert "/var/run/docker.sock" not in compose
    assert "--remove-orphans" not in compose


def test_docker_build_context_excludes_runtime_secrets_and_state() -> None:
    root = Path(__file__).resolve().parents[2]
    ignored = (root / ".dockerignore").read_text(encoding="utf-8").splitlines()
    for required in (".env", ".env.*", ".state", "secrets", "backups", "logs"):
        assert required in ignored


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
    assert "SELECT version_num FROM alembic_version" in script
    assert "onecent-api alembic current" not in script
    assert "$DOCKER compose exec -T onecent-api python scripts/verify_public_release.py" in script
    assert "--base-url http://127.0.0.1:8013" in script
    assert "\npython scripts/verify_public_release.py\n" not in script
    assert "cat .env" not in script


def test_restore_drill_waits_for_final_postgres_not_temporary_init_server() -> None:
    script = (
        Path(__file__).resolve().parents[2] / "scripts" / "restore_drill.sh"
    ).read_text(encoding="utf-8")

    assert 'test "$(cat /proc/1/comm)" = postgres' in script
    assert "-c 'SELECT 1'" in script
    assert 'while [ "$attempt" -lt 60 ]' in script
    assert 'exec "$NAME" pg_isready' not in script
