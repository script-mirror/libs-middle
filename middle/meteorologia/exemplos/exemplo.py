import time

# Contando o tempo de execução
start_time = time.time()

# Datas e parâmetros
modelo = 'ecmwf'
membros = True
inicializacao = 0
data = '2025-07-21'
modelo_fmt = modelo.lower()

# Importando funções específicas do modelo
from ..processamento.produtos import ProdutosPrevisaoCurtoPrazo

produto_config = ProdutosPrevisaoCurtoPrazo(
    modelo=modelo_fmt,
    inicializacao=inicializacao,
    data=data
)

# Fim da execução do código
end_time = time.time()
execution_time = end_time - start_time

# Colocando em minutos
execution_time = execution_time / 60  # Convertendo para minutos
print(f'Tempo de execução: {execution_time:.2f} minutos')
