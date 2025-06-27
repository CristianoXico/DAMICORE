import pandas as pd
import os

def main():
    dados = []
    diretorio = 'test_data/portugues'
    
    # Lista todos os arquivos .txt no diretório
    for arquivo in os.listdir(diretorio):
        if arquivo.endswith('.txt'):
            try:
                # Lê as primeiras 10 linhas de cada arquivo
                caminho_arquivo = os.path.join(diretorio, arquivo)
                with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                    linhas = [linha.strip() for linha in f.readlines() if linha.strip()]
                    # Pega no máximo as primeiras 10 linhas não vazias
                    texto = ' '.join(linhas[:10])
                    # Adiciona à lista de dados
                    dados.append({
                        'documento': os.path.splitext(arquivo)[0],
                        'texto': texto
                    })
            except Exception as e:
                print(f"Erro ao processar o arquivo {arquivo}: {e}")
    
    # Cria o DataFrame e salva como CSV
    if dados:
        df = pd.DataFrame(dados)
        caminho_saida = os.path.join(diretorio, 'dados_portugues.csv')
        df.to_csv(caminho_saida, index=False, encoding='utf-8')
        print(f"Arquivo criado com sucesso: {caminho_saida}")
        print(f"Total de documentos processados: {len(dados)}")
    else:
        print("Nenhum dado foi processado.")

if __name__ == "__main__":
    main()
