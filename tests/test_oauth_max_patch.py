"""Sentinel test for the OAuth Max workaround.

This file is OWNED by the fork at RLuf/hermes-agent (branch oauth-max).
It guards the patch from issue NousResearch/hermes-agent#28849: the
``mcp_`` tool-name prefix loop in ``build_anthropic_kwargs`` must remain
removed on the OAuth path, otherwise every tool-bearing request on a Max
subscription without overage is rejected with HTTP 400 "out of extra usage".

The test is intentionally text-based (greps the source file) so it can
run in CI without installing the full hermes-agent dependency stack.
If upstream renames the function or moves the block, this test fails
loudly and the AI conflict-resolver step in
``.github/workflows/sync-upstream.yml`` must re-apply the patch.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest


ADAPTER = (
    Path(__file__).resolve().parent.parent
    / "agent"
    / "anthropic_adapter.py"
)


def _read_adapter() -> str:
    assert ADAPTER.exists(), f"Adapter file missing: {ADAPTER}"
    return ADAPTER.read_text(encoding="utf-8")


def test_mcp_prefix_loop_is_absent() -> None:
    """The exact loop that broke Max OAuth must not be present."""
    src = _read_adapter()
    # Patterns from the upstream version of the loop (commit c94d664a4).
    forbidden_patterns = [
        # Mutating tool definitions:
        r'tool\["name"\]\s*=\s*_MCP_TOOL_PREFIX\s*\+\s*tool\["name"\]',
        # Mutating tool_use blocks in message history:
        r'block\["name"\]\s*=\s*_MCP_TOOL_PREFIX\s*\+\s*block\["name"\]',
    ]
    for pat in forbidden_patterns:
        assert not re.search(pat, src), (
            f"OAuth Max patch regressed: pattern {pat!r} is back in "
            f"{ADAPTER}. See issue NousResearch/hermes-agent#28849."
        )


def test_explanatory_sentinel_comment_present() -> None:
    """Our explanatory comment is the positive marker for the patch.

    If a merge wipes the comment we treat it as a regression even when
    the offending loop happens to be gone for unrelated upstream reasons —
    a reviewer should re-confirm the patch is still effective.
    """
    src = _read_adapter()
    sentinel = "mcp_ prefix injection removed"
    assert sentinel in src, (
        f"OAuth Max patch sentinel comment missing from {ADAPTER}. "
        "Either the patch was lost during merge or it needs to be "
        "re-stated. See issue NousResearch/hermes-agent#28849."
    )


def test_oauth_branch_still_exists() -> None:
    """The is_oauth code path that we patch must still exist.

    If upstream refactors and renames ``is_oauth``, the patch needs to be
    re-pointed manually — this test will catch the refactor.
    """
    src = _read_adapter()
    assert "if is_oauth:" in src, (
        "Could not find `if is_oauth:` branch in anthropic_adapter.py. "
        "Upstream likely refactored the OAuth code path — the patch must "
        "be reviewed and re-applied to the new structure."
    )


def test_build_anthropic_kwargs_signature_unchanged() -> None:
    """The patched function should still exist with the expected name."""
    src = _read_adapter()
    assert re.search(r"def\s+build_anthropic_kwargs\s*\(", src), (
        "Function `build_anthropic_kwargs` not found. Upstream refactored "
        "the entry point — patch needs re-targeting."
    )


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-v"]))
