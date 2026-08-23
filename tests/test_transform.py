from __future__ import annotations

import pandas as pd

from saude_brasil_insights.transform import (
    add_geographic_access_proxy,
    add_indicators,
    aggregate_ubs,
    build_municipal_dataset,
    normalize_text,
    prepare_population,
)


def population_fixture() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"D1C": "3550308", "D1N": "São Paulo - SP", "D3N": "2025", "V": "12000000"},
            {"D1C": "3304557", "D1N": "Rio de Janeiro - RJ", "D3N": "2025", "V": "6000000"},
        ]
    )


def test_normalize_text_handles_accents_and_punctuation() -> None:
    assert normalize_text("  São João d'Oeste  ") == "SAO JOAO D OESTE"


def test_prepare_population_builds_datasus_code_and_region() -> None:
    result = prepare_population(population_fixture())

    assert result.loc[0, "ibge6"] == "355030"
    assert result.loc[0, "uf"] == "SP"
    assert result.loc[0, "regiao"] == "Sudeste"
    assert result["populacao"].sum() == 18_000_000


def test_ubs_remaps_ceilandia_to_brasilia_at_municipal_level() -> None:
    result, quality = aggregate_ubs(pd.DataFrame([{"ibge": "530040", "cnes": "0010979"}]))

    assert result.iloc[0]["ibge6"] == "530010"
    assert quality["ubs_rows_remapped"] == 1


def test_build_dataset_integrates_ubs_and_hospitals() -> None:
    ubs = pd.DataFrame(
        [
            {"ibge": "355030", "cnes": "0000001"},
            {"ibge": "355030", "cnes": "0000002"},
            {"ibge": "355030", "cnes": "0000002"},
            {"ibge": "330455", "cnes": "0000003"},
        ]
    )
    hospitals = pd.DataFrame(
        [
            {
                "codigo_cnes": "0000100",
                "codigo_municipio": "355030",
                "codigo_tipo_unidade": 5,
                "estabelecimento_possui_centro_cirurgico": 1,
                "estabelecimento_possui_centro_obstetrico": 0,
            },
            {
                "codigo_cnes": "0000200",
                "codigo_municipio": "330455",
                "codigo_tipo_unidade": 7,
                "estabelecimento_possui_centro_cirurgico": 0,
                "estabelecimento_possui_centro_obstetrico": 1,
            },
        ]
    )

    result, quality = build_municipal_dataset(population_fixture(), ubs, hospitals)
    sao_paulo = result.loc[result["municipio"].eq("São Paulo")].iloc[0]

    assert sao_paulo["ubs"] == 2
    assert sao_paulo["hospitais"] == 1
    assert sao_paulo["centros_cirurgicos"] == 1
    assert quality["ubs_unique"] == 3
    assert quality["unmatched_hospital_groups"] == 0


def test_gap_index_is_higher_when_availability_is_lower() -> None:
    frame = pd.DataFrame(
        {
            "populacao": [100_000, 100_000, 100_000],
            "ubs": [1, 5, 10],
            "hospitais": [0, 1, 2],
            "centros_cirurgicos": [0, 1, 2],
            "centros_obstetricos": [0, 1, 2],
        }
    )

    result = add_indicators(frame)

    assert result.loc[0, "indice_lacuna"] > result.loc[1, "indice_lacuna"]
    assert result.loc[1, "indice_lacuna"] > result.loc[2, "indice_lacuna"]
    assert result["indice_lacuna"].equals(result["indice_lacuna_peso_ubs_065"])
    assert result["estabilidade_ranking"].between(0, 100).all()


def test_geographic_proxy_finds_nearest_hospital_municipality() -> None:
    frame = pd.DataFrame(
        {
            "ibge7": ["1000001", "1000002", "1000003"],
            "hospitais": [1, 0, 1],
        }
    )
    geojson = {
        "features": [
            {
                "properties": {"codarea": code},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[lon, 0], [lon + 0.1, 0], [lon + 0.1, 0.1], [lon, 0]]],
                },
            }
            for code, lon in [("1000001", 0.0), ("1000002", 1.0), ("1000003", 10.0)]
        ]
    }

    result = add_geographic_access_proxy(frame, geojson)

    assert result.loc[0, "distancia_hospital_proxy_km"] == 0
    assert result.loc[1, "ibge7_hospital_proxy_mais_proximo"] == "1000001"
    assert result.loc[1, "distancia_hospital_proxy_km"] > 100


def test_population_rejects_duplicate_codes() -> None:
    duplicated = pd.concat(
        [population_fixture(), population_fixture().iloc[[0]]], ignore_index=True
    )

    try:
        prepare_population(duplicated)
    except ValueError as error:
        assert "duplicados" in str(error)
    else:
        raise AssertionError("Duplicated municipal codes should be rejected")
