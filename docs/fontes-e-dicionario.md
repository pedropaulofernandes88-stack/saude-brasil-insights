# Fontes e dicionário de dados

## Linhagem das fontes

| Identificador | Instituição | Conteúdo usado | Endpoint |
|---|---|---|---|
| `population` | IBGE/SIDRA | População municipal estimada, tabela 6579, variável 9324 | [consulta JSON](https://apisidra.ibge.gov.br/values/t/6579/n6/all/v/9324/p/last%201?formato=json) |
| `municipal_boundaries` | IBGE | Malha municipal mínima em GeoJSON | [consulta GeoJSON](https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR?formato=application/vnd.geo+json&qualidade=minima&intrarregiao=municipio) |
| `ubs` | Ministério da Saúde | Relação de Unidades Básicas de Saúde | [endpoint UBS](https://apidadosabertos.saude.gov.br/assistencia-a-saude/unidade-basicas-de-saude) |
| `active_hospitals` | Ministério da Saúde/CNES | Estabelecimentos ativos filtrados por tipo | [endpoint CNES](https://apidadosabertos.saude.gov.br/cnes/estabelecimentos) |

Os endereços efetivamente usados em cada atualização também são gravados em
`data/processed/metadata.json`.

## Artefatos processados

### `data/processed/municipios.csv`

Uma linha por registro municipal devolvido pela estimativa populacional.

| Coluna | Tipo lógico | Unidade/origem | Definição |
|---|---|---|---|
| `ibge7` | texto | IBGE | Código municipal completo com sete dígitos |
| `ibge6` | texto | derivada | Seis primeiros dígitos do código IBGE, usados na integração DATASUS |
| `municipio` | texto | IBGE | Nome oficial do município |
| `uf` | categoria | IBGE | Sigla da Unidade da Federação |
| `regiao` | categoria | derivada | Norte, Nordeste, Centro-Oeste, Sudeste ou Sul |
| `ano_populacao` | inteiro | IBGE | Ano de referência da estimativa |
| `populacao` | inteiro | pessoas | População residente estimada |
| `ubs` | inteiro | Ministério da Saúde | UBS únicas associadas ao município |
| `hospitais` | inteiro | CNES | Estabelecimentos hospitalares ativos incluídos no escopo |
| `centros_cirurgicos` | inteiro | CNES | Hospitais cadastrados com centro cirúrgico |
| `centros_obstetricos` | inteiro | CNES | Hospitais cadastrados com centro obstétrico |
| `ubs_por_10k` | decimal | por 10 mil pessoas | Taxa municipal de UBS |
| `hospitais_por_100k` | decimal | por 100 mil pessoas | Taxa municipal de hospitais |
| `centros_cirurgicos_por_100k` | decimal | por 100 mil pessoas | Taxa municipal de centros cirúrgicos |
| `centros_obstetricos_por_100k` | decimal | por 100 mil pessoas | Taxa municipal de centros obstétricos |
| `indice_lacuna` | decimal | escala 0–100 | Complemento da disponibilidade relativa ponderada |
| `prioridade_exploratoria` | categoria | derivada | Baixa, Moderada, Alta ou Muito alta |

Os identificadores devem ser lidos como texto para preservar zeros à esquerda.

### `data/processed/municipios.geojson`

`FeatureCollection` com a malha simplificada do IBGE. Cada feição possui o identificador municipal
em `properties.codarea`, usado para ligar o mapa ao campo `ibge7` do CSV.

### `data/processed/metadata.json`

Registra horário da geração, ano da população, URLs das fontes, contagens de qualidade e descrição
resumida das fórmulas. É o primeiro artefato a consultar para auditar um snapshot.

## Dados não armazenados

As respostas brutas nacionais não são versionadas. O repositório guarda somente o conjunto
municipal agregado, a malha necessária ao mapa e os metadados. Isso reduz o tamanho do projeto e
evita tratar cadastros de contato de estabelecimentos sem necessidade analítica.
