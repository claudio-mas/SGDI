#!/usr/bin/env bash
# exit on error
set -o errexit

# Define que a instalação será não-interativa (para aceitar EULAs)
export DEBIAN_FRONTEND=noninteractive

# 1. Instalação das dependências APT básicas
# (O que tínhamos antes, mais 'curl' e 'gpg' para adicionar o repo da MS)
apt-get update
apt-get install -y libmagic1 build-essential unixodbc-dev curl gpg

# 2. Adiciona o Repositório da Microsoft para o Driver SQL Server
# (Este exemplo usa Ubuntu 22.04, que é comum no Render)
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/ubuntu/22.04/prod.list > /etc/apt/sources.list.d/mssql-release.list

# 3. Atualiza o APT (depois de adicionar o novo repo) e Instala o Driver
apt-get update
ACCEPT_EULA=Y apt-get install -y msodbcsql18

# (Opcional, mas recomendado) Instala as ferramentas de linha de comando
# Podem ser úteis para testar a conexão via 'sqlcmd'
# ACCEPT_EULA=Y apt-get install -y mssql-tools18
# echo 'export PATH="$PATH:/opt/mssql-tools18/bin"' >> ~/.bashrc
# source ~/.bashrc

# 4. Finalmente, instala as dependências Python
pip install -r requirements.txt

# (Se tiveres um 'collectstatic' ou 'migrate' do Django, adiciona aqui)
# python manage.py collectstatic --no-input
# python manage.py migrate