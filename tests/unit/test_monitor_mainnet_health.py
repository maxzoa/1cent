from __future__ import annotations

import os
import shutil
import stat
import subprocess
import time
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parents[2] / "scripts" / "monitor_mainnet_health.sh"
pytestmark = pytest.mark.skipif(os.name == "nt", reason="POSIX monitor integration test")


def _write_executable(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


@pytest.fixture
def monitor_project(tmp_path: Path) -> tuple[Path, dict[str, str]]:
    project = tmp_path / "onecent"
    scripts = project / "scripts"
    bin_dir = project / "bin"
    scripts.mkdir(parents=True)
    bin_dir.mkdir()
    shutil.copy2(SCRIPT, scripts / SCRIPT.name)
    (project / "runtime.txt").write_text(
        "development|testnet|eip155:84532|false\n", encoding="utf-8"
    )
    (project / "probe.txt").write_text("fail\n", encoding="utf-8")
    (project / "public-probe.txt").write_text("fail\n", encoding="utf-8")
    _write_executable(
        bin_dir / "docker",
        "#!/bin/sh\n"
        'case "$*" in\n'
        '  *onecent-api*) cat "$ONECENT_PROJECT_DIR/runtime.txt" ;;\n'
        '  *onecent-bot*) echo alert >>"$ONECENT_PROJECT_DIR/alerts.log" ;;\n'
        "  *) echo forbidden-docker-call >&2; exit 90 ;;\n"
        "esac\n",
    )
    _write_executable(
        bin_dir / "curl",
        "#!/bin/sh\n"
        'case "$*" in\n'
        '  *http://local/*) probe="$ONECENT_PROJECT_DIR/probe.txt" ;;\n'
        '  *) probe="$ONECENT_PROJECT_DIR/public-probe.txt" ;;\n'
        'esac\n'
        'test "$(cat "$probe")" = pass || exit 22\n'
        'case "$*" in */health) printf \'{"status":"ok"}\' ;; '
        '*/info) printf \'{"network":"eip155:8453"}\' ;; esac\n',
    )
    _write_executable(
        scripts / "rollback_testnet.sh",
        "#!/bin/sh\n"
        'echo rollback >>"$ONECENT_PROJECT_DIR/rollbacks.log"\n'
        "printf '%s\\n' 'development|testnet|eip155:84532|false' "
        '>"$ONECENT_PROJECT_DIR/runtime.txt"\n',
    )
    env = os.environ.copy()
    env.update(
        ONECENT_PROJECT_DIR=str(project),
        DOCKER=str(bin_dir / "docker"),
        CURL=str(bin_dir / "curl"),
        LOCAL_BASE_URL="http://local",
    )
    return project, env


def _run(project: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["sh", str(project / "scripts" / SCRIPT.name)],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def _count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines()) if path.exists() else 0


def test_testnet_normal_is_noop(monitor_project: tuple[Path, dict[str, str]]) -> None:
    project, env = monitor_project
    result = _run(project, env)
    assert result.returncode == 0
    assert "testnet_noop=PASS" in result.stdout
    assert _count(project / "alerts.log") == 0
    assert _count(project / "rollbacks.log") == 0


def test_testnet_forced_failure_is_ignored(
    monitor_project: tuple[Path, dict[str, str]],
) -> None:
    project, env = monitor_project
    env.update(FORCE_FAILURE="true", DRY_RUN="true")
    result = _run(project, env)
    assert result.returncode == 0
    assert "testnet_noop=PASS" in result.stdout
    assert (project / ".state" / "mainnet-health.failures").read_text().strip() == "0"
    assert _count(project / "alerts.log") == 0
    assert _count(project / "rollbacks.log") == 0


def test_testnet_missing_approval_is_fail_closed_noop(
    monitor_project: tuple[Path, dict[str, str]],
) -> None:
    project, env = monitor_project
    (project / "runtime.txt").write_text(
        "development|testnet|eip155:84532|\n", encoding="utf-8"
    )
    result = _run(project, env)
    assert result.returncode == 0
    assert "testnet_noop=PASS" in result.stdout
    assert _count(project / "alerts.log") == 0
    assert _count(project / "rollbacks.log") == 0


def test_public_tls_failure_never_rolls_back_healthy_local_mainnet(
    monitor_project: tuple[Path, dict[str, str]],
) -> None:
    project, env = monitor_project
    (project / "runtime.txt").write_text(
        "production|mainnet|eip155:8453|true\n", encoding="utf-8"
    )
    (project / "probe.txt").write_text("pass\n", encoding="utf-8")
    state = project / ".state"
    state.mkdir()
    (state / "public-mainnet-active.env").write_text(
        "PUBLIC_MAINNET_ACTIVE=true\n", encoding="utf-8"
    )

    results = [_run(project, env) for _ in range(4)]

    assert all(item.returncode == 1 for item in results)
    assert "local_mainnet_health=PASS" in results[-1].stdout
    assert "public_probe=DEGRADED" in results[-1].stdout
    assert _count(project / "rollbacks.log") == 0
    assert _count(project / "alerts.log") == 1
    assert (state / "public-mainnet-active.env").read_text().strip().endswith("true")


def test_mainnet_third_failure_rolls_back_once_then_noops(
    monitor_project: tuple[Path, dict[str, str]],
) -> None:
    project, env = monitor_project
    (project / "runtime.txt").write_text("production|mainnet|eip155:8453|true\n", encoding="utf-8")
    state = project / ".state"
    state.mkdir()
    (state / "public-mainnet-active.env").write_text(
        "PUBLIC_MAINNET_ACTIVE=true\n", encoding="utf-8"
    )
    first = _run(project, env)
    second = _run(project, env)
    assert first.returncode == 1 and "mainnet_failure_count=1" in first.stdout
    assert second.returncode == 1 and "mainnet_failure_count=2" in second.stdout
    assert _count(project / "alerts.log") == 0
    assert _count(project / "rollbacks.log") == 0

    third = _run(project, env)
    assert third.returncode == 1
    assert "mainnet_failure_count=3" in third.stdout
    assert "telegram_alert=PASS" in third.stdout
    assert "rollback=PASS" in third.stdout
    assert _count(project / "alerts.log") == 1
    assert _count(project / "rollbacks.log") == 1
    assert (state / "public-mainnet-active.env").read_text().strip().endswith("false")

    after = _run(project, env)
    assert after.returncode == 0
    assert "testnet_noop=PASS" in after.stdout
    assert _count(project / "alerts.log") == 1
    assert _count(project / "rollbacks.log") == 1


def test_overlapping_run_is_blocked(monitor_project: tuple[Path, dict[str, str]]) -> None:
    project, env = monitor_project
    state = project / ".state"
    state.mkdir()
    lock = state / "mainnet-health.lock"
    holder = subprocess.Popen(["flock", str(lock), "sleep", "2"])
    try:
        time.sleep(0.1)
        result = _run(project, env)
    finally:
        holder.wait(timeout=3)
    assert result.returncode == 0
    assert "overlap_blocked=PASS" in result.stdout


def test_stale_test_files_are_removed_and_ignored(
    monitor_project: tuple[Path, dict[str, str]],
) -> None:
    project, env = monitor_project
    state = project / ".state"
    state.mkdir()
    (state / "monitor-force-failure").write_text("true\n", encoding="utf-8")
    (state / "monitor-dry-run").write_text("true\n", encoding="utf-8")
    result = _run(project, env)
    assert result.returncode == 0
    assert "testnet_noop=PASS" in result.stdout
    assert not (state / "monitor-force-failure").exists()
    assert not (state / "monitor-dry-run").exists()
