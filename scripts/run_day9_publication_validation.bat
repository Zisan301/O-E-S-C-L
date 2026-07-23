@echo off
setlocal
cd /d "%~dp0\.."
python scripts\run_day9_publication_validation.py --config config\day9_validation_config.yaml
pause
