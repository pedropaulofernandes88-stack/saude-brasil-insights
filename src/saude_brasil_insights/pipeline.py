"""Pipeline executavel que atualiza o snapshot usado pelo painel."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from .config import SOURCE_URLS
from .data_sources import (
    build_session,
    fetch_hospitals,
    fetch_municipal_geojson,
    fetch_population,
    fetch_ubs,
)
from .transform import add_geographic_access_proxy, build_municipal_dataset


def update_data(output_dir: Path) -> dict[str, object]:
    """Baixa, valida e grava o conjunto municipal pronto para consumo."""
    output_dir.mkdir(parents=True, exist_ok=True)
    session = build_session()

    print("[1/5] Baixando populacao municipal do IBGE...")
    population = fetch_population(session)
    print("[2/5] Baixando Unidades Basicas de Saude...")
    ubs = fetch_ubs(session)
    print("[3/5] Baixando estabelecimentos hospitalares ativos do CNES...")
    hospitals = fetch_hospitals(session)
    print("[4/5] Integrando fontes e calculando indicadores...")
    dataset, quality = build_municipal_dataset(population, ubs, hospitals)
    print("[5/5] Baixando malha municipal simplificada...")
    geojson = fetch_municipal_geojson(session)

    municipal_codes = set(dataset["ibge7"].astype(str))
    geojson["features"] = [
        feature
        for feature in geojson["features"]
        if str(feature.get("properties", {}).get("codarea")) in municipal_codes
    ]
    quality["geojson_features"] = len(geojson["features"])
    geojson_codes = {
        str(feature.get("properties", {}).get("codarea")) for feature in geojson["features"]
    }
    quality["municipalities_without_geometry"] = int(
        (~dataset["ibge7"].astype(str).isin(geojson_codes)).sum()
    )
    dataset = add_geographic_access_proxy(dataset, geojson)
    quality["municipalities_with_access_proxy"] = int(
        dataset["distancia_hospital_proxy_km"].notna().sum()
    )

    dataset_path = output_dir / "municipios.csv"
    geojson_path = output_dir / "municipios.geojson"
    metadata_path = output_dir / "metadata.json"

    dataset.sort_values(["uf", "municipio"]).to_csv(dataset_path, index=False, encoding="utf-8")
    geojson_path.write_text(
        json.dumps(geojson, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )

    metadata: dict[str, object] = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "population_year": int(dataset["ano_populacao"].max()),
        "sources": SOURCE_URLS,
        "quality": quality,
        "methodology": {
            "ubs_rate": "UBS unicas por 10 mil habitantes",
            "hospital_rate": "estabelecimentos hospitalares ativos por 100 mil habitantes",
            "gap_index": (
                "complemento do percentil ponderado de disponibilidade: "
                "65% UBS e 35% estabelecimentos hospitalares ativos"
            ),
            "sensitivity": "pesos UBS de 0%, 25%, 50%, 65%, 75% e 100%",
            "geographic_access_proxy": (
                "distancia geodesica entre centros das caixas envolventes municipais e o "
                "centro do municipio com hospital ativo mais proximo; nao representa viagem"
            ),
        },
    }
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Dados atualizados em {output_dir.resolve()}")
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/processed"),
        help="Diretorio para municipios.csv, municipios.geojson e metadata.json",
    )
    args = parser.parse_args()
    update_data(args.output_dir)


if __name__ == "__main__":
    main()
