"""
Script para testar a função visualizar_arvore_consenso com dados de exemplo.
"""

# Árvores Newick de exemplo (simples para teste)
arvores_newick = [
    "(A:1,(B:1,(C:1,D:1):0.5):0.5);",
    "(A:1,(B:1,(D:1,C:1):0.5):0.5);",
    "(A:1,(B:1,(C:1,D:1):0.5):0.5);"
]

# Rótulos para as folhas (opcional, mas recomendado)
rotulos = ["Amostra A", "Amostra B", "Amostra C", "Amostra D"]

# Índice do outgroup (opcional, padrão é 0)
outgroup_idx = 0  # Usa a primeira amostra como outgroup

# Importa a função do pipeline
from pipeline_novo import visualizar_arvore_consenso

# Executa a visualização
print("🔍 Iniciando teste da visualização da árvore de consenso...")
resultado = visualizar_arvore_consenso(
    newick_strings=arvores_newick,
    labels=rotulos,
    outgroup_index=outgroup_idx
)

# Exibe os resultados
if resultado:
    print("\n🎉 Teste concluído com sucesso!")
    print("\n📝 Resumo dos arquivos gerados:")
    for tipo, caminho in resultado['arquivos_gerados'].items():
        print(f"   - {tipo.replace('_', ' ').title()}: {caminho}")
    
    # Exibe a visualização ASCII se disponível
    if 'ascii_tree' in resultado['visualizacoes']:
        print("\n🌳 Visualização ASCII gerada com sucesso!")
        print("   (Verifique o arquivo .txt para a visualização completa)")
else:
    print("\n❌ Ocorreu um erro ao gerar as visualizações.")
