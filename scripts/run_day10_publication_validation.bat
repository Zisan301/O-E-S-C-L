@echo off
cd /d "%~dp0\.."
python scripts\run_day10_publication_validation.py --config config\day10_validation_config.yaml
pause
