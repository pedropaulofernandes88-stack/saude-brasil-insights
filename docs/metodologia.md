# Metodologia

## 1. Objetivo analítico

O Saúde Brasil Insights descreve como a disponibilidade **local e cadastrada** de UBS e
estabelecimentos hospitalares ativos varia entre os municípios brasileiros em relação à população.

A unidade de análise é o município. O projeto não estima causalidade, eficiência, qualidade clínica
ou suficiência da rede regional.

## 2. Escopo do MVP

O MVP combina quatro conjuntos:

1. população municipal estimada pelo IBGE;
2. relação de UBS publicada pelo Ministério da Saúde;
3. estabelecimentos hospitalares ativos do CNES;
4. malha municipal simplificada do IBGE.

Não entram no índice: leitos, profissionais, produção assistencial, ocupação, deslocamento,
especialidades, demanda reprimida ou desfechos de saúde.

## 3. Extração

O pipeline consulta as APIs oficiais no momento da atualização. As respostas do Ministério da Saúde
são paginadas e possuem retentativas para falhas HTTP transitórias.

Embora a documentação pública descreva `offset` como número de página, o comportamento observado
no serviço é de deslocamento de registros. Por isso o cliente avança `offset` pelo tamanho efetivo da
página, evitando janelas sobrepostas e duplicação.

O snapshot atual foi gerado em `2026-08-23T19:01:32Z` e utiliza população de referência de 2025.
Uma nova execução pode produzir números diferentes conforme os cadastros oficiais forem atualizados.

## 4. Regras de transformação

### 4.1 População

- O código IBGE é preservado com sete dígitos em `ibge7`.
- Os seis primeiros dígitos formam `ibge6`, chave usada para integrar os dados do DATASUS.
- Município e UF são separados do rótulo devolvido pelo SIDRA.
- Populações ausentes, não numéricas ou não positivas interrompem o pipeline.
- Códigos municipais duplicados também interrompem o pipeline.

### 4.2 UBS

- UBS são deduplicadas pela combinação de código municipal e código CNES.
- O código legado `530040`, associado a uma UBS de Ceilândia, é remapeado para `530010`
  (Brasília), pois a análise é municipal e Ceilândia é uma região administrativa do Distrito
  Federal.
- Códigos municipais inválidos são contabilizados nos metadados.

### 4.3 Estabelecimentos hospitalares

- A extração solicita apenas registros com `status=1` no CNES.
- São incluídos os tipos CNES: hospital geral (`5`), hospital especializado (`7`), unidade mista
  (`15`) e hospital-dia isolado (`62`).
- Estabelecimentos são deduplicados por código CNES.
- A integração é feita por `codigo_municipio`, sem associação aproximada por nome.
- Os campos cadastrais de centro cirúrgico e centro obstétrico são agregados por município.

### 4.4 Valores ausentes

Depois de integrar a dimensão completa de municípios com as bases cadastrais, ausência de UBS ou
hospital associado é representada por zero. Os grupos não associados são reportados em
`metadata.json`, permitindo distinguir zero analítico de falha de integração.

## 5. Indicadores per capita

Para um município `m`:

```text
UBS por 10 mil(m) = UBS(m) / população(m) × 10.000

Hospitais por 100 mil(m) = hospitais(m) / população(m) × 100.000

Centros cirúrgicos por 100 mil(m) = centros cirúrgicos(m) / população(m) × 100.000

Centros obstétricos por 100 mil(m) = centros obstétricos(m) / população(m) × 100.000
```

As taxas são arredondadas para duas casas no arquivo processado. Os cálculos são feitos antes do
arredondamento.

## 6. Índice exploratório de lacuna

UBS por 10 mil e hospitais por 100 mil são transformados em percentis nacionais. Empates recebem a
menor posição compartilhada (`rank(method="min", pct=True)`).

```text
disponibilidade(m) = 0,65 × percentil_UBS(m)
                   + 0,35 × percentil_hospitais(m)

índice_lacuna(m) = 100 × [1 - disponibilidade(m)]
```

Faixas usadas apenas para navegação no painel:

| Índice | Faixa exploratória |
|---:|---|
| 0 a <25 | Baixa |
| 25 a <50 | Moderada |
| 50 a <75 | Alta |
| 75 a 100 | Muito alta |

Os pesos são uma decisão transparente do MVP, não um consenso clínico, epidemiológico ou
regulatório. O índice mede posição relativa: mesmo em um cenário de oferta suficiente para todos,
ele continuaria ordenando municípios.

### 6.1 Análise de sensibilidade

O pipeline repete o cálculo com pesos de UBS de 0%, 25%, 50%, 65%, 75% e 100%, mantendo o
complemento para hospitais. Para cada município são publicados a amplitude e o desvio-padrão do
índice, além de uma estabilidade de ranking de 0 a 100. Quanto mais próximo de 100, menor a
variação da posição entre os cenários testados. Essa análise revela dependência dos pesos, mas não
valida qual combinação é substantivamente correta.

## 7. Proxy geográfico de acesso hospitalar

Para cada geometria municipal, calcula-se o centro da caixa envolvente. Em seguida, a fórmula de
haversine identifica a menor distância geodésica até o centro de um município que possua ao menos
um hospital ativo no cadastro.

O campo `distancia_hospital_proxy_km` é uma medida exploratória de separação espacial. Ele **não é
distância por rodovia, tempo de viagem ou acesso efetivo**. O centro geométrico pode estar longe da
população e a unidade hospitalar pode estar longe desse centro. O indicador serve para priorizar
onde uma análise de rede viária e fluxos regionais seria mais útil.

## 8. Limitações

1. Município sem hospital pode estar adequadamente atendido por uma rede regional próxima.
2. Cadastro ativo não comprova funcionamento, equipe, agenda, vaga ou qualidade.
3. Taxas de municípios pequenos podem ser instáveis e sensíveis a uma única unidade.
4. O índice não incorpora necessidades distintas por idade, morbidade ou vulnerabilidade social.
5. Centros cirúrgicos e obstétricos são atributos cadastrais, não medidas de produção.
6. Leitos foram excluídos porque o endpoint agregado examinado não expõe competência temporal; sua
   soma poderia misturar snapshots históricos como se fossem oferta atual.
7. Boa Esperança do Norte (MT) integra a população de 2025, mas ainda não aparece na malha
   simplificada devolvida pelo serviço utilizado. O município permanece na tabela e nos cálculos,
   ficando ausente apenas do mapa.

8. O proxy territorial não incorpora estradas, rios, relevo, transporte ou localização exata das
   unidades.

## 9. Interpretação responsável

Um valor alto no índice é um **sinal para investigação**, não confirmação de desassistência. Uma
avaliação aplicada deveria incluir redes de referência, tempo de viagem, capacidade operacional,
demanda, utilização, resultados e validação por profissionais de saúde pública.

## 10. Reprodutibilidade

```powershell
python -m pip install -e ".[dev]"
saude-brasil-update --output-dir data/processed
pytest
ruff check .
```

Consulte também [fontes-e-dicionario.md](fontes-e-dicionario.md) e
[validacao-e-qualidade.md](validacao-e-qualidade.md).
