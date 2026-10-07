import importlib.util
import sqlite3
from pathlib import Path

import pytest

from app.settings import Settings, validate_production_settings


def test_light_profile_keeps_production_secret_gate():
    with pytest.raises(RuntimeError):
        validate_production_settings(Settings(environment="production",deployment_profile="light"))
    validate_production_settings(Settings(environment="production",deployment_profile="light",auth_secret="x"*40))
    with pytest.raises(RuntimeError):
        validate_production_settings(Settings(environment="production",deployment_profile="standard",auth_secret="x"*40))
    with pytest.raises(RuntimeError):
        validate_production_settings(Settings(deployment_profile="unknown"))


def test_light_backup_and_restored_sqlite_integrity(tmp_path):
    path=Path(__file__).parents[3] / "infra/backup_light.py"
    spec=importlib.util.spec_from_file_location("backup_light",path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    source=tmp_path / "metadata"
    source.mkdir()
    with sqlite3.connect(source / "fixture.sqlite3") as connection:
        connection.execute("CREATE TABLE evidence(text TEXT)")
        connection.execute("INSERT INTO evidence VALUES('Synthetic source record')")
    module.backup(source,tmp_path / "backup")
    with sqlite3.connect(tmp_path / "backup/fixture.sqlite3") as restored:
        assert restored.execute("SELECT text FROM evidence").fetchone()[0]=="Synthetic source record"
    with pytest.raises(ValueError):
        module.backup(source,tmp_path / "backup")
