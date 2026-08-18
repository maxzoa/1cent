from __future__ import annotations

import os
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path


class BuyerStateError(RuntimeError):
    pass


@dataclass(frozen=True)
class LedgerEntry:
    entry_id: str
    fingerprint: str
    tool: str
    amount_atomic: int
    network: str
    asset: str
    pay_to: str
    resource: str
    status: str
    expires_at: str


def default_state_path() -> Path:
    return Path.home() / ".onecent" / "buyer-bridge.sqlite3"


def _utc_now() -> datetime:
    return datetime.now(UTC)


class BuyerLedger:
    """Local payment approvals and spend ledger. Never stores wallet secrets."""

    _SCHEMA = """
    CREATE TABLE IF NOT EXISTS bridge_payments (
        entry_id TEXT PRIMARY KEY,
        fingerprint TEXT NOT NULL,
        tool TEXT NOT NULL,
        amount_atomic INTEGER NOT NULL CHECK (amount_atomic > 0),
        network TEXT NOT NULL,
        asset TEXT NOT NULL,
        pay_to TEXT NOT NULL,
        resource TEXT NOT NULL,
        status TEXT NOT NULL CHECK (
            status IN ('quote', 'approved', 'pending', 'success', 'unknown', 'expired')
        ),
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        utc_date TEXT NOT NULL,
        request_id TEXT,
        payment_response_present INTEGER NOT NULL DEFAULT 0
    );
    CREATE INDEX IF NOT EXISTS ix_bridge_fingerprint
        ON bridge_payments(fingerprint, status);
    CREATE INDEX IF NOT EXISTS ix_bridge_daily
        ON bridge_payments(utc_date, status);
    """

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path).expanduser()
        self._prepare_path()
        with self._connect() as connection:
            connection.executescript(self._SCHEMA)

    def _prepare_path(self) -> None:
        parent = self.path.parent
        parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        if self.path.is_symlink():
            raise BuyerStateError("buyer bridge state path must not be a symlink")
        if not self.path.exists():
            self.path.touch(mode=0o600)
        if os.name != "nt":
            os.chmod(parent, 0o700)
            os.chmod(self.path, 0o600)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=5.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    @staticmethod
    def _entry(row: sqlite3.Row) -> LedgerEntry:
        return LedgerEntry(
            entry_id=str(row["entry_id"]),
            fingerprint=str(row["fingerprint"]),
            tool=str(row["tool"]),
            amount_atomic=int(row["amount_atomic"]),
            network=str(row["network"]),
            asset=str(row["asset"]),
            pay_to=str(row["pay_to"]),
            resource=str(row["resource"]),
            status=str(row["status"]),
            expires_at=str(row["expires_at"]),
        )

    @staticmethod
    def _expire(connection: sqlite3.Connection, now: datetime) -> None:
        timestamp = now.isoformat()
        connection.execute(
            """
            UPDATE bridge_payments
            SET status='expired', updated_at=?
            WHERE status IN ('quote', 'approved') AND expires_at <= ?
            """,
            (timestamp, timestamp),
        )

    def ensure_quote(
        self,
        *,
        fingerprint: str,
        tool: str,
        amount_atomic: int,
        network: str,
        asset: str,
        pay_to: str,
        resource: str,
        ttl_seconds: int = 600,
    ) -> LedgerEntry:
        now = _utc_now()
        expires = now + timedelta(seconds=ttl_seconds)
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            self._expire(connection, now)
            existing = connection.execute(
                """
                SELECT * FROM bridge_payments
                WHERE fingerprint=? AND status IN ('quote', 'approved')
                ORDER BY created_at DESC LIMIT 1
                """,
                (fingerprint,),
            ).fetchone()
            if existing is not None:
                connection.commit()
                return self._entry(existing)
            entry_id = str(uuid.uuid4())
            values = (
                entry_id,
                fingerprint,
                tool,
                amount_atomic,
                network,
                asset,
                pay_to,
                resource,
                "quote",
                now.isoformat(),
                now.isoformat(),
                expires.isoformat(),
                now.date().isoformat(),
            )
            connection.execute(
                """
                INSERT INTO bridge_payments (
                    entry_id, fingerprint, tool, amount_atomic, network, asset, pay_to,
                    resource, status, created_at, updated_at, expires_at, utc_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                values,
            )
            connection.commit()
            return LedgerEntry(
                entry_id=entry_id,
                fingerprint=fingerprint,
                tool=tool,
                amount_atomic=amount_atomic,
                network=network,
                asset=asset,
                pay_to=pay_to,
                resource=resource,
                status="quote",
                expires_at=expires.isoformat(),
            )

    def approve(self, entry_id: str) -> LedgerEntry:
        now = _utc_now()
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            self._expire(connection, now)
            row = connection.execute(
                "SELECT * FROM bridge_payments WHERE entry_id=?",
                (entry_id,),
            ).fetchone()
            if row is None:
                raise BuyerStateError("approval request not found")
            if row["status"] != "quote":
                raise BuyerStateError(f"approval request is {row['status']}, not pending")
            connection.execute(
                "UPDATE bridge_payments SET status='approved', updated_at=? WHERE entry_id=?",
                (now.isoformat(), entry_id),
            )
            approved = connection.execute(
                "SELECT * FROM bridge_payments WHERE entry_id=?",
                (entry_id,),
            ).fetchone()
            connection.commit()
            if approved is None:
                raise BuyerStateError("approval request disappeared")
            return self._entry(approved)

    @staticmethod
    def _daily_total(connection: sqlite3.Connection, utc_date: str) -> int:
        row = connection.execute(
            """
            SELECT COALESCE(SUM(amount_atomic), 0) AS total
            FROM bridge_payments
            WHERE utc_date=? AND status IN ('pending', 'success', 'unknown')
            """,
            (utc_date,),
        ).fetchone()
        return int(row["total"] if row is not None else 0)

    @staticmethod
    def _assert_no_unresolved(connection: sqlite3.Connection, fingerprint: str) -> None:
        row = connection.execute(
            """
            SELECT entry_id, status FROM bridge_payments
            WHERE fingerprint=? AND status IN ('pending', 'unknown')
            ORDER BY created_at DESC LIMIT 1
            """,
            (fingerprint,),
        ).fetchone()
        if row is not None:
            raise BuyerStateError(
                "same request has unresolved payment outcome; automatic retry is blocked"
            )

    def reserve_approved(
        self,
        *,
        fingerprint: str,
        daily_limit_atomic: int | None,
    ) -> LedgerEntry:
        now = _utc_now()
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            self._expire(connection, now)
            self._assert_no_unresolved(connection, fingerprint)
            row = connection.execute(
                """
                SELECT * FROM bridge_payments
                WHERE fingerprint=? AND status='approved'
                ORDER BY created_at DESC LIMIT 1
                """,
                (fingerprint,),
            ).fetchone()
            if row is None:
                raise BuyerStateError("payment needs a fresh one-call approval")
            if daily_limit_atomic is not None:
                total = self._daily_total(connection, now.date().isoformat())
                if total + int(row["amount_atomic"]) > daily_limit_atomic:
                    raise BuyerStateError("local daily spend cap would be exceeded")
            connection.execute(
                "UPDATE bridge_payments SET status='pending', updated_at=? WHERE entry_id=?",
                (now.isoformat(), row["entry_id"]),
            )
            connection.commit()
            updated = dict(row)
            updated["status"] = "pending"
            return LedgerEntry(
                entry_id=str(updated["entry_id"]),
                fingerprint=str(updated["fingerprint"]),
                tool=str(updated["tool"]),
                amount_atomic=int(updated["amount_atomic"]),
                network=str(updated["network"]),
                asset=str(updated["asset"]),
                pay_to=str(updated["pay_to"]),
                resource=str(updated["resource"]),
                status="pending",
                expires_at=str(updated["expires_at"]),
            )

    def reserve_auto(
        self,
        *,
        fingerprint: str,
        tool: str,
        amount_atomic: int,
        network: str,
        asset: str,
        pay_to: str,
        resource: str,
        daily_limit_atomic: int,
    ) -> LedgerEntry:
        now = _utc_now()
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            self._assert_no_unresolved(connection, fingerprint)
            total = self._daily_total(connection, now.date().isoformat())
            if total + amount_atomic > daily_limit_atomic:
                raise BuyerStateError("local daily spend cap would be exceeded")
            entry_id = str(uuid.uuid4())
            expires = now + timedelta(minutes=10)
            connection.execute(
                """
                INSERT INTO bridge_payments (
                    entry_id, fingerprint, tool, amount_atomic, network, asset, pay_to,
                    resource, status, created_at, updated_at, expires_at, utc_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?, ?)
                """,
                (
                    entry_id,
                    fingerprint,
                    tool,
                    amount_atomic,
                    network,
                    asset,
                    pay_to,
                    resource,
                    now.isoformat(),
                    now.isoformat(),
                    expires.isoformat(),
                    now.date().isoformat(),
                ),
            )
            connection.commit()
            return LedgerEntry(
                entry_id=entry_id,
                fingerprint=fingerprint,
                tool=tool,
                amount_atomic=amount_atomic,
                network=network,
                asset=asset,
                pay_to=pay_to,
                resource=resource,
                status="pending",
                expires_at=expires.isoformat(),
            )

    def finish(
        self,
        entry_id: str,
        *,
        status: str,
        request_id: str | None = None,
        payment_response_present: bool = False,
    ) -> None:
        if status not in {"success", "unknown"}:
            raise BuyerStateError("invalid terminal bridge payment status")
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE bridge_payments
                SET status=?, updated_at=?, request_id=?, payment_response_present=?
                WHERE entry_id=? AND status='pending'
                """,
                (
                    status,
                    _utc_now().isoformat(),
                    request_id,
                    int(payment_response_present),
                    entry_id,
                ),
            )
            if cursor.rowcount != 1:
                raise BuyerStateError("bridge payment entry is not pending")

    def snapshot(self) -> dict[str, int]:
        now = _utc_now()
        with self._connect() as connection:
            self._expire(connection, now)
            daily = self._daily_total(connection, now.date().isoformat())
            unresolved_row = connection.execute(
                """
                SELECT COUNT(*) AS count FROM bridge_payments
                WHERE status IN ('pending', 'unknown')
                """
            ).fetchone()
            approvals_row = connection.execute(
                "SELECT COUNT(*) AS count FROM bridge_payments WHERE status='approved'"
            ).fetchone()
        return {
            "daily_reserved_atomic": daily,
            "unresolved": int(unresolved_row["count"] if unresolved_row else 0),
            "approved": int(approvals_row["count"] if approvals_row else 0),
        }
