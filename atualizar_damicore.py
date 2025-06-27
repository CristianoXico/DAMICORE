#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para atualizar o código-fonte do DAMICORE para Python 3.
"""

import os
import re
import shutil
from pathlib import Path

def atualizar_arquivo(caminho_entrada, caminho_saida):
    """Atualiza um único arquivo para Python 3."""
    with open(caminho_entrada, 'r', encoding='utf-8', errors='replace') as f:
        conteudo = f.read()
    
    # Adiciona imports do __future__ se não existirem
    if 'from __future__ import' not in conteudo:
        imports_futuros = 'from __future__ import print_function, division, absolute_import\n\n'
        conteudo = imports_futuros + conteudo
    
    # Atualiza prints
    conteudo = re.sub(r'print\s+([^\(].*?)(?=\n|$)', r'print(\1)', conteudo, flags=re.MULTILINE)
    
    # Atualiza imports comuns
    substituicoes = [
        (r'import StringIO', 'import io'),
        (r'StringIO\.StringIO', 'io.StringIO'),
        (r'import cPickle', 'import _pickle as cPickle'),
        (r'import urlparse', 'import urllib.parse as urlparse'),
        (r'import urllib\s*$', 'import urllib.request, urllib.parse, urllib.error'),
        (r'urllib\.urlopen', 'urllib.request.urlopen'),
        (r'urllib\.quote', 'urllib.parse.quote'),
        (r'urllib\.unquote', 'urllib.parse.unquote'),
        (r'xrange\(', 'range('),
        (r'iteritems\(', 'items('),
        (r'itervalues\(', 'values('),
        (r'iterkeys\(', 'keys('),
        (r'\.has_key\(', ' in '),
        (r'<\?', '<'),  # Remove tags PHP se houver
    ]
    
    for antigo, novo in substituicoes:
        conteudo = re.sub(antigo, novo, conteudo)
    
    # Corrige abertura de arquivos binários
    conteudo = re.sub(r'open\(([^,)]+)(, *["\']r["\'])?\)', 
                     r'open(\1, "rb")', 
                     conteudo)
    
    # Cria diretório de saída se não existir
    os.makedirs(os.path.dirname(caminho_saida), exist_ok=True)
    
    # Salva o arquivo atualizado
    with open(caminho_saida, 'w', encoding='utf-8') as f:
        f.write(conteudo)

def copiar_arquivo(caminho_entrada, caminho_saida):
    """Copia um arquivo mantendo os metadados."""
    os.makedirs(os.path.dirname(caminho_saida), exist_ok=True)
    shutil.copy2(caminho_entrada, caminho_saida)

def processar_diretorio(diretorio_entrada, diretorio_saida):
    """Processa todos os arquivos Python no diretório de entrada."""
    for raiz, _, arquivos in os.walk(diretorio_entrada):
        for arquivo in arquivos:
            if arquivo.endswith('.py'):
                caminho_entrada = os.path.join(raiz, arquivo)
                # Mantém a estrutura de diretórios relativa
                rel_path = os.path.relpath(caminho_entrada, diretorio_entrada)
                caminho_saida = os.path.join(diretorio_saida, rel_path)
                
                print(f'Atualizando {rel_path}...')
                try:
                    atualizar_arquivo(caminho_entrada, caminho_saida)
                except Exception as e:
                    print(f'Erro ao processar {caminho_entrada}: {e}')
            else:
                # Copia arquivos não-PY sem modificação
                caminho_entrada = os.path.join(raiz, arquivo)
                rel_path = os.path.relpath(caminho_entrada, diretorio_entrada)
                caminho_saida = os.path.join(diretorio_saida, rel_path)
                copiar_arquivo(caminho_entrada, caminho_saida)

if __name__ == '__main__':
    # Caminhos
    dir_entrada = os.path.join('damicore-python', 'damicore-python', 'src')
    dir_saida = 'damicore_py3'
    
    print(f'Iniciando conversão de {dir_entrada} para Python 3...')
    print(f'Diretório de saída: {dir_saida}')
    
    # Processa os arquivos
    processar_diretorio(dir_entrada, dir_saida)
    
    print('\nConversão concluída!')
    print('\nAtenção: Esta é uma conversão automática. Verifique manualmente os seguintes itens:')
    print('- Tratamento de bytes vs strings')
    print('- Métodos de ordenação (cmp vs key)')
    print('- Divisão de inteiros (usa // para divisão inteira)')
    print('- Chamadas de API que podem ter mudado entre Python 2 e 3')
