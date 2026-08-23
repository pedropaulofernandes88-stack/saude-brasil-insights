# Mapeamento de transparência — GATHER

Esta é uma autoavaliação inspirada nas diretrizes GATHER para estimativas de saúde. Não é uma
auditoria oficial e o projeto produz indicadores descritivos, não estimativas de carga de doença.

| Tema | Evidência | Situação |
|---|---|---|
| Definição do indicador e unidade de análise | `docs/metodologia.md` | Coberto |
| Identificação das fontes | `docs/fontes-e-dicionario.md`, `metadata.json` | Coberto |
| Critérios de inclusão e transformação | pipeline e metodologia | Coberto |
| Acesso aos dados e código | URLs oficiais, código e snapshot | Coberto |
| Tratamento de ausência | metodologia e relatório de qualidade | Coberto |
| Incerteza | análise de sensibilidade dos pesos | Parcial |
| Validação | testes e reconciliação do snapshot | Coberto tecnicamente |
| Interpretação e limitações | README e metodologia | Coberto |
| Conflitos e financiamento | projeto independente, sem financiamento declarado | Declarado |

## Lacunas

- não há intervalos de incerteza das fontes cadastrais;
- a sensibilidade cobre pesos, mas não sub-registro, denominador populacional ou definição de
  estabelecimento;
- o proxy territorial precisa ser substituído por localização das unidades, rede viária e tempos
  de viagem para uma aplicação de planejamento;
- especialistas em saúde pública e gestores municipais ainda não revisaram os limiares e usos.
