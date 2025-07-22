#!/bin/bash

# Verifica se o diretório input existe, se não, cria
mkdir -p input results

# Copia o arquivo de exemplo para o diretório input se ele não existir
if [ ! -f input/example_input.csv ]; then
    cp examples/example_input.csv input/
fi

# Executa o container
docker-compose up --build
