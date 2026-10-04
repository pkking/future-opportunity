from typer.testing import CliRunner

from future_opportunity.cli import app


runner = CliRunner()


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
