"""Clientes pequenos e testaveis para as fontes publicas do projeto."""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import (
    CNES_ESTABLISHMENTS_ENDPOINT,
    HOSPITAL_UNIT_TYPES,
    IBGE_GEOJSON_URL,
    IBGE_POPULATION_URL,
    OPEN_DATA_SUS_BASE_URL,
    UBS_ENDPOINT,
)


def build_session() -> requests.Session:
    """Cria uma sessao HTTP com retentativas apenas para falhas transitorias."""
    retry = Retry(
        total=4,
        backoff_factor=0.6,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
    )
    session = requests.Session()
    session.headers.update({"User-Agent": "saude-brasil-insights/0.1"})
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


def fetch_population(session: requests.Session | None = None) -> pd.DataFrame:
    """Baixa a estimativa municipal mais recente publicada no SIDRA/IBGE."""
    client = session or build_session()
    response = client.get(IBGE_POPULATION_URL, timeout=90)
    response.raise_for_status()
    records = response.json()
    if not records or len(records) < 2:
        raise ValueError("A resposta do SIDRA nao contem municipios.")
    return pd.DataFrame.from_records(records[1:])


def fetch_paginated(
    endpoint: str,
    response_key: str,
    *,
    limit: int = 1_000,
    session: requests.Session | None = None,
    on_page: Callable[[int, int], None] | None = None,
    query_params: dict[str, Any] | None = None,
) -> pd.DataFrame:
    """Percorre a API usando ``offset`` como deslocamento real de registros.

    A documentacao publica descreve ``offset`` como pagina, mas o servico em producao retorna
    janelas sobrepostas quando recebe 0, 1, 2. Por isso o cliente avanca pelo tamanho da pagina.
    """
    client = session or build_session()
    offset = 0
    records: list[dict[str, Any]] = []

    while True:
        params = dict(query_params or {})
        params.update({"limit": limit, "offset": offset})
        response = client.get(
            f"{OPEN_DATA_SUS_BASE_URL}{endpoint}",
            params=params,
            timeout=120,
        )
        response.raise_for_status()
        payload = response.json()
        batch = payload.get(response_key)
        if batch is None:
            raise ValueError(f"Chave '{response_key}' ausente na resposta de {endpoint}.")
        if not batch:
            break

        records.extend(batch)
        if on_page:
            on_page(offset // limit, len(records))
        if len(batch) < limit:
            break
        offset += limit

    return pd.DataFrame.from_records(records)


def fetch_ubs(session: requests.Session | None = None) -> pd.DataFrame:
    """Baixa a relacao nacional de Unidades Basicas de Saude."""
    return fetch_paginated(UBS_ENDPOINT, "ubs", session=session)


def fetch_hospitals(session: requests.Session | None = None) -> pd.DataFrame:
    """Baixa estabelecimentos hospitalares ativos diretamente do cadastro CNES."""
    del session  # Cada worker usa sua propria sessao; requests.Session nao garante thread safety.

    def fetch_unit_type(unit_type: int) -> pd.DataFrame:
        return fetch_paginated(
            CNES_ESTABLISHMENTS_ENDPOINT,
            "estabelecimentos",
            limit=20,
            session=build_session(),
            query_params={"codigo_tipo_unidade": unit_type, "status": 1},
        )

    with ThreadPoolExecutor(max_workers=len(HOSPITAL_UNIT_TYPES)) as executor:
        frames = list(executor.map(fetch_unit_type, HOSPITAL_UNIT_TYPES))
    return pd.concat(frames, ignore_index=True).drop_duplicates(subset=["codigo_cnes"])


def fetch_municipal_geojson(session: requests.Session | None = None) -> dict[str, Any]:
    """Baixa a malha municipal simplificada do IBGE em GeoJSON."""
    client = session or build_session()
    response = client.get(IBGE_GEOJSON_URL, timeout=180)
    response.raise_for_status()
    geojson = response.json()
    if geojson.get("type") != "FeatureCollection":
        raise ValueError("A malha do IBGE nao retornou um FeatureCollection.")
    return geojson
