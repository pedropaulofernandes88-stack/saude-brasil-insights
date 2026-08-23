"""Configuracoes e URLs das fontes oficiais."""

from __future__ import annotations

IBGE_POPULATION_URL = (
    "https://apisidra.ibge.gov.br/values/t/6579/n6/all/v/9324/p/last%201?formato=json"
)
IBGE_GEOJSON_URL = (
    "https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR"
    "?formato=application/vnd.geo+json&qualidade=minima&intrarregiao=municipio"
)
OPEN_DATA_SUS_BASE_URL = "https://apidadosabertos.saude.gov.br"
UBS_ENDPOINT = "/assistencia-a-saude/unidade-basicas-de-saude"
CNES_ESTABLISHMENTS_ENDPOINT = "/cnes/estabelecimentos"
HOSPITAL_UNIT_TYPES = {
    5: "Hospital geral",
    7: "Hospital especializado",
    15: "Unidade mista",
    62: "Hospital-dia isolado",
}

UF_TO_REGION = {
    "AC": "Norte",
    "AL": "Nordeste",
    "AM": "Norte",
    "AP": "Norte",
    "BA": "Nordeste",
    "CE": "Nordeste",
    "DF": "Centro-Oeste",
    "ES": "Sudeste",
    "GO": "Centro-Oeste",
    "MA": "Nordeste",
    "MG": "Sudeste",
    "MS": "Centro-Oeste",
    "MT": "Centro-Oeste",
    "PA": "Norte",
    "PB": "Nordeste",
    "PE": "Nordeste",
    "PI": "Nordeste",
    "PR": "Sul",
    "RJ": "Sudeste",
    "RN": "Nordeste",
    "RO": "Norte",
    "RR": "Norte",
    "RS": "Sul",
    "SC": "Sul",
    "SE": "Nordeste",
    "SP": "Sudeste",
    "TO": "Norte",
}

SOURCE_URLS = {
    "population": IBGE_POPULATION_URL,
    "municipal_boundaries": IBGE_GEOJSON_URL,
    "ubs": f"{OPEN_DATA_SUS_BASE_URL}{UBS_ENDPOINT}",
    "active_hospitals": f"{OPEN_DATA_SUS_BASE_URL}{CNES_ESTABLISHMENTS_ENDPOINT}",
}
