# -----------------------------------------------------------------
# Fase 1: Configuração do Sistema Operativo (O que falhou antes)
# -----------------------------------------------------------------
# Ajuste "3.10" se estiveres a usar uma versão diferente do Python
FROM python:3.12-slim-bullseye

# Define variáveis de ambiente
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# 1. Instala pré-requisitos (como o 'curl' e ferramentas de build)
RUN apt-get update && apt-get install -y \
    curl \
    gpg \
    gnupg \
    build-essential \
    unixodbc-dev \
    libmagic1 \
    --no-install-recommends

# 2. Adiciona o repositório da Microsoft (para Debian 11 "Bullseye")
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg
RUN curl -fsSL https://packages.microsoft.com/config/debian/11/prod.list | tee /etc/apt/sources.list.d/mssql-release.list

# 3. Instala o Driver do SQL Server (e aceita a EULA)
RUN apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql18 --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# -----------------------------------------------------------------
# Fase 2: Instalação da Aplicação Python
# -----------------------------------------------------------------

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia o requirements.txt primeiro (para otimizar o cache)
COPY requirements.txt .

# Instala as dependências Python
# (Agora o 'pyodbc' e o 'python-magic' vão encontrar as libs)
RUN pip install -r requirements.txt

# Copia o resto do código da tua aplicação
COPY . .

# O Render vai executar o teu "Start Command" aqui
# Não é preciso 'EXPOSE' ou 'CMD', o Render trata disso.