# Validação e qualidade

## Resultado do snapshot versionado

Snapshot gerado em `2026-08-23T19:01:32Z`, com população de referência de 2025.

| Verificação | Resultado |
|---|---:|
| Registros municipais | 5.571 |
| População consolidada | 213.421.037 |
| UBS únicas na fonte | 46.848 |
| UBS remapeadas de Ceilândia para Brasília | 1 |
| Grupos de UBS não associados | 0 |
| Hospitais ativos únicos | 6.457 |
| Grupos hospitalares não associados | 0 |
| Códigos hospitalares inválidos | 0 |
| Feições municipais no GeoJSON | 5.570 |
| Municípios sem geometria | 1 |
| Municípios com proxy territorial | 5.570 |

Os valores acima correspondem a `data/processed/metadata.json`. Este documento descreve o snapshot
versionado; após uma atualização, ele deve ser revisado junto com os metadados.

## Validações implementadas

### População

- presença das colunas esperadas do SIDRA;
- separação válida de município e UF;
- código IBGE municipal único;
- população numérica e positiva;
- UF associada a uma das cinco regiões.

### UBS

- código municipal com seis dígitos;
- código CNES normalizado com sete dígitos;
- deduplicação por município e CNES;
- remapeamento explícito e contado do código legado de Ceilândia;
- contagem de grupos sem correspondência populacional.

### Hospitais

- seleção de registros ativos na chamada à API;
- seleção explícita dos quatro tipos de unidade incluídos;
- deduplicação nacional pelo código CNES;
- normalização do código municipal;
- contagem de códigos inválidos e grupos não associados.

### Geometria

- resposta obrigatoriamente do tipo `FeatureCollection`;
- retenção apenas das feições presentes na dimensão municipal;
- contagem de municípios do CSV sem geometria correspondente.

## Testes automatizados

A suíte cobre:

- normalização de texto;
- transformação da população e mapeamento regional;
- remapeamento Ceilândia → Brasília;
- deduplicação e integração de UBS e hospitais;
- ordenação esperada do índice de lacuna;
- rejeição de códigos municipais duplicados;
- paginação por deslocamento real de registros.

O workflow `.github/workflows/ci.yml` executa lint e testes em todo `push` e `pull_request`.

## Critérios para considerar uma atualização válida

1. `pytest` e `ruff check .` devem terminar sem falhas.
2. Códigos populacionais devem continuar únicos e com população positiva.
3. Grupos não associados devem ser zero ou possuir justificativa documentada.
4. Variações grandes nas contagens de UBS ou hospitais devem ser investigadas antes do commit.
5. A diferença entre municípios e feições geográficas deve ser explicada.
6. README, metodologia e este relatório devem refletir o novo snapshot.

## Limite da validação

Esses controles verificam estrutura, consistência e integração. Eles não confirmam presencialmente
se uma unidade está aberta, equipada ou com capacidade disponível. Essa distinção deve permanecer
visível em qualquer análise baseada no projeto.
