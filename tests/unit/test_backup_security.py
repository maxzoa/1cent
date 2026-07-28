from pathlib import Path


def test_backup_script_restricts_directory_and_dump_permissions() -> None:
    script = (
        Path(__file__).resolve().parents[2] / "scripts" / "backup_db.sh"
    ).read_text(encoding="utf-8")

    assert "umask 077" in script
    assert 'chmod 711 "$BACKUP_DIR"' in script
    assert 'chmod 600 "$TARGET"' in script
