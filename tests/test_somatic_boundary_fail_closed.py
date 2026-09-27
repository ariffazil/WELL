"""Somatic boundary must fail closed (F13 order 2026-09-28).

Why this file exists: the somatic/autonomic split was OPT-IN, gated on
`_os.environ.get("WELL_SOMATIC_BOUNDARY", "0") == "1"`. A process booted without that
variable therefore published the entire autonomic surface. Measured the same night: an
instance started without the flag advertised 81 tools instead of 40, adding names such as
well_seal_vault and well_999_vault that had never been public. Production looked safe
only because the systemd unit happened to set the variable -- the default underneath was
fail-open, so a dropped `Environment=` line, a new host, or any ad-hoc run silently
widened the privacy boundary.

The decision is tested as a pure function (`server._somatic_boundary_armed`) rather than
by re-importing a 21k-line module, so it cannot silently stop being exercised.
"""

from __future__ import annotations

import pytest

import server

ARMED = "must be armed: absence of configuration is not consent to publish the autonomic surface"


def test_no_configuration_arms_the_boundary():
    assert server._somatic_boundary_armed({}) is True, ARMED


def test_none_argument_uses_process_env_and_arms_by_default(monkeypatch):
    monkeypatch.delenv("WELL_SOMATIC_BOUNDARY", raising=False)
    monkeypatch.delenv("FEDERATION_SOMATIC_BOUNDARY", raising=False)
    assert server._somatic_boundary_armed() is True, ARMED


@pytest.mark.parametrize("token", ["0", "false", "FALSE", "off", "OFF", "no", " off "])
def test_explicit_opt_out_is_still_possible_for_development(token):
    assert server._somatic_boundary_armed({"WELL_SOMATIC_BOUNDARY": token}) is False


@pytest.mark.parametrize(
    "typo", ["", "1", "yes", "OFFx", "None", "none", "disabled", "01", "true", "falseh"]
)
def test_everything_else_arms_it_including_typos(typo):
    """A misspelled opt-out must not silently open the surface."""
    assert server._somatic_boundary_armed({"WELL_SOMATIC_BOUNDARY": typo}) is True, (
        f"{typo!r} disabled the privacy boundary -- only the explicit falsy tokens may"
    )


def test_federation_flag_forces_it_on():
    assert (
        server._somatic_boundary_armed(
            {"FEDERATION_SOMATIC_BOUNDARY": "1", "WELL_SOMATIC_BOUNDARY": "0"}
        )
        is True
    ), "the federation-wide flag must win over a local opt-out"


@pytest.mark.parametrize(
    "name",
    [
        "well_seal_vault",
        "well_999_vault",
        "well_measure_gradient",
        "well_compute_metabolic_flux",
        "well_log_state",
        "well_fatigue_accumulator",
        "well_readiness",
        "well_state",
        "well_get_health",
    ],
)
def test_sensitive_names_are_not_somatic(name):
    """Independent of the filter: these are not in the allowlist at all."""
    assert name not in server.SOMATIC_TOOLS, f"{name} must never be publicly advertised"


def test_filter_actually_subtracts_from_a_listing():
    """The filter must subtract, not relabel.

    Uses a stand-in provider instead of FastMCP internals: poking private attributes
    here would break on the next fastmcp upgrade (WP-7), and a test that fails for the
    wrong reason trains agents to ignore it.
    """
    import asyncio
    import types

    class _FakeTool:
        def __init__(self, name):
            self.name = name

    async def _listed():
        return [_FakeTool(n) for n in ("well_registry_status", "well_seal_vault", "well_state")]

    provider = types.SimpleNamespace(list_tools=_listed)
    app = types.SimpleNamespace(_local_provider=provider)

    server._enforce_somatic_boundary(app)
    names = [t.name for t in asyncio.run(provider.list_tools())]

    assert "well_registry_status" in names, "a somatic tool was wrongly hidden"
    assert "well_seal_vault" not in names, "an autonomic verb leaked into the public listing"
    assert "well_state" not in names, "a deprecated name leaked into the public listing"
