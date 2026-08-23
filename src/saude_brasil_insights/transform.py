"""Limpeza, integracao e calculo dos indicadores municipais."""

from __future__ import annotations

import re
import unicodedata
from typing import Any

import pandas as pd

from .config import UF_TO_REGION

HOSPITAL_COLUMNS = {
    "codigo_cnes": "cnes",
    "codigo_municipio": "ibge6",
    "codigo_tipo_unidade": "tipo_unidade",
    "estabelecimento_possui_centro_cirurgico": "centro_cirurgico",
    "estabelecimento_possui_centro_obstetrico": "centro_obstetrico",
}

DATASUS_MUNICIPAL_CODE_ALIASES = {
    # Ceilandia e uma regiao administrativa do DF; no nivel municipal pertence a Brasilia.
    "530040": "530010",
}


def normalize_text(value: Any) -> str:
    """Normaliza nomes para integrar fontes que nao compartilham o mesmo identificador."""
    if value is None or pd.isna(value):
        return ""
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(character for character in text if not unicodedata.combining(character))
    text = re.sub(r"[^A-Za-z0-9]+", " ", text.upper())
    return " ".join(text.split())


def prepare_population(raw: pd.DataFrame) -> pd.DataFrame:
    """Converte o retorno compacto do SIDRA em uma dimensao municipal."""
    required = {"D1C", "D1N", "D3N", "V"}
    missing = required.difference(raw.columns)
    if missing:
        raise ValueError(f"Colunas ausentes na populacao: {sorted(missing)}")

    frame = raw.loc[:, ["D1C", "D1N", "D3N", "V"]].copy()
    extracted = frame["D1N"].str.extract(r"^(?P<municipio>.+) - (?P<uf>[A-Z]{2})$")
    if extracted.isna().any(axis=None):
        raise ValueError("Nao foi possivel separar municipio e UF em todos os registros do SIDRA.")

    frame["ibge7"] = frame["D1C"].astype("string").str.zfill(7)
    frame["ibge6"] = frame["ibge7"].str[:6]
    frame["municipio"] = extracted["municipio"].str.strip()
    frame["uf"] = extracted["uf"]
    frame["regiao"] = frame["uf"].map(UF_TO_REGION)
    frame["ano_populacao"] = pd.to_numeric(frame["D3N"], errors="raise").astype("int64")
    frame["populacao"] = pd.to_numeric(frame["V"], errors="raise").astype("int64")
    frame["municipio_chave"] = frame["uf"] + "|" + frame["municipio"].map(normalize_text)

    if frame["ibge7"].duplicated().any():
        raise ValueError("A fonte de populacao retornou codigos municipais duplicados.")
    if (frame["populacao"] <= 0).any():
        raise ValueError("A fonte de populacao retornou valor nao positivo.")
    if frame["regiao"].isna().any():
        raise ValueError("Existe UF sem regiao mapeada.")

    return frame[
        [
            "ibge7",
            "ibge6",
            "municipio",
            "uf",
            "regiao",
            "ano_populacao",
            "populacao",
            "municipio_chave",
        ]
    ]


def aggregate_ubs(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    """Conta UBS unicas por codigo municipal DATASUS de seis digitos."""
    required = {"ibge", "cnes"}
    missing = required.difference(raw.columns)
    if missing:
        raise ValueError(f"Colunas ausentes nas UBS: {sorted(missing)}")

    frame = raw.copy()
    frame["ibge6"] = frame["ibge"].astype("string").str.replace(r"\D", "", regex=True).str.zfill(6)
    remapped_rows = int(frame["ibge6"].isin(DATASUS_MUNICIPAL_CODE_ALIASES).sum())
    frame["ibge6"] = frame["ibge6"].replace(DATASUS_MUNICIPAL_CODE_ALIASES)
    frame["cnes"] = frame["cnes"].astype("string").str.replace(r"\D", "", regex=True).str.zfill(7)
    valid = frame["ibge6"].str.fullmatch(r"\d{6}", na=False)
    invalid_rows = int((~valid).sum())
    frame = frame.loc[valid].drop_duplicates(subset=["ibge6", "cnes"])
    result = frame.groupby("ibge6", as_index=False).agg(ubs=("cnes", "nunique"))
    return result, {
        "ubs_rows_invalid_code": invalid_rows,
        "ubs_rows_remapped": remapped_rows,
        "ubs_unique": int(len(frame)),
    }


def aggregate_hospitals(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    """Agrega estabelecimentos hospitalares ativos pelo codigo municipal CNES."""
    missing = set(HOSPITAL_COLUMNS).difference(raw.columns)
    if missing:
        raise ValueError(f"Colunas ausentes nos hospitais: {sorted(missing)}")

    frame = raw.rename(columns=HOSPITAL_COLUMNS).loc[:, list(HOSPITAL_COLUMNS.values())].copy()
    frame["ibge6"] = (
        frame["ibge6"].astype("string").str.replace(r"\D", "", regex=True).str.zfill(6)
    )
    frame["cnes"] = frame["cnes"].astype("string").str.replace(r"\D", "", regex=True).str.zfill(7)
    valid = frame["ibge6"].str.fullmatch(r"\d{6}", na=False)
    invalid_rows = int((~valid).sum())
    frame = frame.loc[valid].drop_duplicates(subset=["cnes"])
    for column in ["centro_cirurgico", "centro_obstetrico"]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce").fillna(0).clip(0, 1)

    result = frame.groupby("ibge6", as_index=False).agg(
        hospitais=("cnes", "nunique"),
        centros_cirurgicos=("centro_cirurgico", "sum"),
        centros_obstetricos=("centro_obstetrico", "sum"),
    )
    return result, {
        "hospital_rows_invalid_code": invalid_rows,
        "hospitals_unique_active": int(len(frame)),
    }


def _availability_percentile(series: pd.Series) -> pd.Series:
    """Percentil de disponibilidade; empates recebem a menor posicao compartilhada."""
    return series.rank(method="min", pct=True).fillna(0)


def add_indicators(frame: pd.DataFrame) -> pd.DataFrame:
    """Calcula taxas comparaveis e um indice exploratorio de lacuna assistencial."""
    result = frame.copy()
    result["ubs_por_10k"] = result["ubs"] / result["populacao"] * 10_000
    result["hospitais_por_100k"] = result["hospitais"] / result["populacao"] * 100_000
    result["centros_cirurgicos_por_100k"] = (
        result["centros_cirurgicos"] / result["populacao"] * 100_000
    )
    result["centros_obstetricos_por_100k"] = (
        result["centros_obstetricos"] / result["populacao"] * 100_000
    )

    availability = (
        0.65 * _availability_percentile(result["ubs_por_10k"])
        + 0.35 * _availability_percentile(result["hospitais_por_100k"])
    )
    result["indice_lacuna"] = ((1 - availability) * 100).clip(0, 100)
    result["prioridade_exploratoria"] = pd.cut(
        result["indice_lacuna"],
        bins=[-float("inf"), 25, 50, 75, float("inf")],
        labels=["Baixa", "Moderada", "Alta", "Muito alta"],
        right=False,
    ).astype("string")

    rate_columns = [
        "ubs_por_10k",
        "hospitais_por_100k",
        "centros_cirurgicos_por_100k",
        "centros_obstetricos_por_100k",
        "indice_lacuna",
    ]
    result[rate_columns] = result[rate_columns].round(2)
    return result


def build_municipal_dataset(
    population_raw: pd.DataFrame,
    ubs_raw: pd.DataFrame,
    hospitals_raw: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, int | float]]:
    """Integra as tres fontes e devolve os indicadores e um relatorio de qualidade."""
    population = prepare_population(population_raw)
    ubs, ubs_quality = aggregate_ubs(ubs_raw)
    hospitals, hospital_quality = aggregate_hospitals(hospitals_raw)

    population_codes = set(population["ibge6"])
    unmatched_ubs = int((~ubs["ibge6"].isin(population_codes)).sum())
    unmatched_hospitals = int((~hospitals["ibge6"].isin(population_codes)).sum())

    result = population.merge(ubs, on="ibge6", how="left", validate="one_to_one")
    result = result.merge(hospitals, on="ibge6", how="left", validate="one_to_one")
    count_columns = ["ubs", "hospitais", "centros_cirurgicos", "centros_obstetricos"]
    result[count_columns] = result[count_columns].fillna(0)
    result[count_columns] = result[count_columns].astype("int64")
    result = add_indicators(result)

    quality: dict[str, int | float] = {
        **ubs_quality,
        **hospital_quality,
        "municipalities": int(len(result)),
        "municipalities_with_ubs": int((result["ubs"] > 0).sum()),
        "municipalities_with_hospital": int((result["hospitais"] > 0).sum()),
        "unmatched_ubs_groups": unmatched_ubs,
        "unmatched_hospital_groups": unmatched_hospitals,
        "population_total": int(result["populacao"].sum()),
    }
    return result.drop(columns=["municipio_chave"]), quality
