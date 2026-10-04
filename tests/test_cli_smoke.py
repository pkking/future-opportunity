import re

from typer.testing import CliRunner

from future_opportunity.cli import app


runner = CliRunner()
ANSI_ESCAPE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


def plain_output(value: str) -> str:
    return ANSI_ESCAPE.sub("", value)


def test_cli_exposes_v0_business_workflow_commands() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    for command in (
        "discover",
        "simulate",
        "positions",
        "position-show",
        "position-refresh",
        "position-close",
        "opportunity-show",
        "opportunity-history",
        "db-migrate",
    ):
        assert command in result.stdout


def test_quickstart_remains_zero_configuration_and_paper_only() -> None:
    result = runner.invoke(app, ["quickstart", "funding-carry"])

    assert result.exit_code == 0
    assert "arb discover funding-carry" in result.stdout
    assert "arb simulate funding-carry" in result.stdout
    assert "paper" in result.stdout.lower()
    assert "live orders are disabled" in result.stdout.lower()


def test_discover_and_simulate_expose_explicit_liquidity_controls() -> None:
    for command in ("discover", "simulate"):
        result = runner.invoke(app, [command, "--help"])
        assert result.exit_code == 0
        output = plain_output(result.stdout)
        assert "--liquidity-policy" in output
        assert "--max-impact-bps" in output
        assert "strict" in output
