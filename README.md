# Middle Libs

Libs Middle

## Installation

Instalação HTTPS

```bash
pip install --upgrade --force-reinstall git+https://github.com/wx-middle/libs-middle.git
```

Instalação SSH

```bash
pip install --upgrade --force-reinstall git+ssh://git@github.com/wx-middle/libs-middle.git
```

Instalação branch especifica:

```bash
pip install git+https://github.com/wx-middle/libs-middle.gitt@main
```

## Exemplo de Uso: Atualização do DECOMP

O script `atualiza_decomp.py` permite realizar análises de sensibilidade e atualizar parâmetros do arquivo `dadger` do DECOMP.

### Exemplo de Execução

```python
from middle.decomp.atualiza_decomp import process_decomp

params = {
    'dadger_path': '/caminho/para/dadger.rv2',
    'output_path': '/caminho/para/saida/dadger.rv2',
    'id_estudo': '111',
    'case': 'ATUALIZANDO-CVU'
}

sensibilidade = {
    'ct': {
        'cvu': {
            "24": {"1": 341.04, "2": 341.04, "3": 341.04, "4": 341.04}
        }
    }
}

process_decomp(params, sensibilidade)
```

### Exemplo Completo de Sensibilidades

```python
exemplos_sensibilidades = {
    "TESTE-FULL": {
        "hq": {
            'lim_sup':    {"215": {"1": 4700, "2": 4700, "3": 4700, "4": 4700}},
            'lim_inf':    {"215": {"1": 200, "2": 200, "3": 200, "4": 200}},
            'lim_sup_p1': {"215": {"1": 300, "2": 300, "3": 300, "4": 300}}
        },
        'ct': {
            'inflex': {'absoluto': True,  24: {1: 100}, 25: {1: 200}, 27: {1: 50}},
            'cvu':    {24: {1: 0}, 25: {1: 0}, 27: {1: 0}},
            'disp':   {'absoluto': False, 24: {1: -250}, 25: {1: 0}, 27: {1: 0}}
        },
        "pq": {
            "valor_p1": {
                "NE_EOL": {"1": 6.0, "2": 2000, "3": 3000},
                "SUL_EOL": {"1": 1000},
            },
            "valor_p2": {
                "NE_EOL": {"1": 6.0, "2": 2000, "3": 3000},
                "SUL_EOL": {"1": 1000}
            },
        },
        "dp": {
            "valor_p1": {"1": {"1": 44936, "2": 46479}, "2": {"1": 1000}},
            "valor_p2": {"1": {"1": 39527}, "2": {"1": 1000}},
            "valor_p3": {"1": {"1": 1000}, "2": {"1": 1000}}
        },
        "re": {
            'vmax_p1': {"409": {"1": 4700, "2": 4700, "3": 4700, "4": 4700}},
            'vmax_p2': {"409": {"1": 4700, "2": 4700, "3": 4700, "4": 4700}},
            'vmax_p3': {"409": {"1": 4700, "2": 4700, "3": 4700, "4": 4700}}
        }
    }
}
```

Para rodar múltiplos cenários de sensibilidade:

```python
for sensitivity, sensitivity_df in exemplos_sensibilidades.items():
    params['case'] = sensitivity
    process_decomp(params, sensitivity_df)
```

### Parâmetros

- `dadger_path`: Caminho para o arquivo dadger.rvX de entrada.
- `output_path`: Caminho para o arquivo dadger.rvX de saída.
- `id_estudo`: Identificador do estudo.
- `case`: Nome do caso/sensibilidade.

### Estrutura dos Dados de Sensibilidade

Os dados de sensibilidade devem ser organizados por bloco (`ct`, `hq`, `pq`, `dp`, `re`), tipo de parâmetro, id da usina/fonte/submercado e estágio.

Consulte os exemplos acima para referência.

### Observações

- Recomenda-se validar os caminhos dos arquivos antes da execução.
- O script pode ser adaptado para diferentes tipos de análises conforme a necessidade.
