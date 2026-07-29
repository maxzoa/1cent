from typing import Any

from onecent import glama_stdio


def test_glama_entrypoint_runs_canonical_server_over_stdio(
    monkeypatch: Any,
) -> None:
    calls: list[str] = []

    def fake_run(*, transport: str) -> None:
        calls.append(transport)

    monkeypatch.setattr(glama_stdio.mcp, "run", fake_run)

    glama_stdio.main()

    assert calls == ["stdio"]
