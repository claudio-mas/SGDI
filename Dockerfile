# -----------------------------------------------------------------
# Fase 1: Configuração do Sistema Operativo
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

# -----------------------------------------------------------------
# Etapa 2: Instalação do Driver SQL Server (AQUI ESTÁ A CORREÇÃO)
# -----------------------------------------------------------------

# 2.1. Adiciona a chave GPG da Microsoft ao keyring
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg

# 2.2. Cria a lista de sources MANUALMENTE, apontando para a chave
# (Esta é a linha que foi corrigida)
RUN echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/11/prod bullseye main" > /etc/apt/sources.list.d/mssql-release.list

# 3. Instala o Driver (agora o 'apt-get update' vai funcionar)
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
RUN pip install -r requirements.txt

# Copia o resto do código da tua aplicação
COPY . .