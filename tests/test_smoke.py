from src.oescl.config import load_config
from src.oescl.experiments import run_experiment
from src.oescl.validation import validate_results


def test_smoke_pipeline_runs():
    cfg = load_config("config/conference_config.yaml")
    result = run_experiment(cfg, mode="smoke")
    validation = validate_results(result, cfg)
    assert "channel_metrics" in result
    assert "scenario_summary" in result
    assert validation["passed"]
