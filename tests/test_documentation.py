from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "processed"


def format_pt_br(value: int) -> str:
    return f"{value:,}".replace(",", ".")


def test_versioned_snapshot_matches_metadata() -> None:
    data = pd.read_csv(DATA_DIR / "municipios.csv", dtype={"ibge7": "string", "ibge6": "string"})
    metadata = json.loads((DATA_DIR / "metadata.json").read_text(encoding="utf-8"))
    quality = metadata["quality"]
    geojson = json.loads((DATA_DIR / "municipios.geojson").read_text(encoding="utf-8"))

    assert len(data) == quality["municipalities"]
    assert int(data["populacao"].sum()) == quality["population_total"]
    assert int(data["ubs"].sum()) == quality["ubs_unique"]
    assert int(data["hospitais"].sum()) == quality["hospitals_unique_active"]
    assert int(data["ubs"].gt(0).sum()) == quality["municipalities_with_ubs"]
    assert int(data["hospitais"].gt(0).sum()) == quality["municipalities_with_hospital"]
    assert len(geojson["features"]) == quality["geojson_features"]


def test_readme_snapshot_numbers_match_metadata() -> None:
    metadata = json.loads((DATA_DIR / "metadata.json").read_text(encoding="utf-8"))
    quality = metadata["quality"]
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    documented_values = [
        quality["municipalities"],
        quality["ubs_unique"],
        quality["hospitals_unique_active"],
        quality["municipalities_with_ubs"],
        quality["municipalities_with_hospital"],
        quality["population_total"],
    ]
    for value in documented_values:
        assert format_pt_br(value) in readme


def test_quality_report_matches_metadata() -> None:
    metadata = json.loads((DATA_DIR / "metadata.json").read_text(encoding="utf-8"))
    quality = metadata["quality"]
    report = (ROOT / "docs" / "validacao-e-qualidade.md").read_text(encoding="utf-8")
    methodology = (ROOT / "docs" / "metodologia.md").read_text(encoding="utf-8")
    generated_at = datetime.fromisoformat(metadata["generated_at_utc"])
    documented_timestamp = generated_at.replace(microsecond=0).isoformat().replace("+00:00", "Z")

    expected_rows = {
        "Registros municipais": quality["municipalities"],
        "População consolidada": quality["population_total"],
        "UBS únicas na fonte": quality["ubs_unique"],
        "UBS remapeadas de Ceilândia para Brasília": quality["ubs_rows_remapped"],
        "Grupos de UBS não associados": quality["unmatched_ubs_groups"],
        "Hospitais ativos únicos": quality["hospitals_unique_active"],
        "Grupos hospitalares não associados": quality["unmatched_hospital_groups"],
        "Códigos hospitalares inválidos": quality["hospital_rows_invalid_code"],
        "Feições municipais no GeoJSON": quality["geojson_features"],
        "Municípios sem geometria": quality["municipalities_without_geometry"],
        "Municípios com proxy territorial": quality["municipalities_with_access_proxy"],
    }
    for label, value in expected_rows.items():
        assert f"| {label} | {format_pt_br(value)} |" in report

    assert documented_timestamp in report
    assert documented_timestamp in methodology
