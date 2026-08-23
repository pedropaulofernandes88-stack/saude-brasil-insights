# Metodologia e limites

## Pergunta do MVP

Como varia, entre os municípios brasileiros, a disponibilidade cadastrada de atenção básica e
estabelecimentos hospitalares ativos em relação à população estimada?

O projeto responde a uma pergunta descritiva. Ele não identifica causalidade e não classifica a
qualidade clínica de serviços.

## Unidade de análise

Município. A população vem da estimativa municipal mais recente disponibilizada na tabela 6579 do
SIDRA. UBS e hospitais ativos vêm da API de Dados Abertos do Ministério da Saúde.

## Integração

- O código municipal utilizado na relação de UBS possui seis dígitos; ele é associado aos seis
  primeiros dígitos do código IBGE de sete dígitos.
- O código legado `530040`, usado por uma UBS de Ceilândia, é remapeado para Brasília (`530010`),
  pois Ceilândia é uma região administrativa do Distrito Federal e não um município.
- Hospitais são selecionados no CNES por situação ativa e tipos hospital geral, especializado,
  unidade mista e hospital-dia isolado.
- O relatório em `data/processed/metadata.json` registra grupos que não puderam ser associados.

## Índice exploratório

Cada taxa é transformada em percentil nacional. A disponibilidade relativa combina:

- 65% UBS por 10 mil habitantes;
- 35% estabelecimentos hospitalares ativos por 100 mil habitantes.

O índice de lacuna é o complemento dessa disponibilidade, em uma escala de 0 a 100. Os pesos são
uma decisão explícita do MVP, não um consenso clínico ou regulatório.

## Riscos de interpretação

1. Um município sem hospital pode fazer parte de uma rede regional adequada.
2. Cadastro não garante operação, equipe, vaga, qualidade ou acesso real.
3. Taxas em populações pequenas são instáveis.
4. A integração nominal de hospitais pode gerar falsos zeros quando os nomes divergem.
5. O índice relativo sempre produz melhores e piores posições, mesmo que a oferta absoluta seja
   suficiente ou insuficiente para todos.
6. Leitos não entram no MVP: o endpoint agregado encontrado não expõe competência temporal e
   poderia somar snapshots históricos como se fossem observações atuais.
7. Boa Esperança do Norte (MT) integra os indicadores de 2025, mas ainda não está na malha
   simplificada devolvida pelo serviço do IBGE e, portanto, não aparece no mapa.

## Uso responsável

O painel serve para exploração, transparência e geração de hipóteses. Uma decisão pública exigiria
validação por especialistas, indicadores de demanda e desfecho, análise de deslocamento e revisão
da atualização cadastral.
