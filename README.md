# Sistema SGDI - Gestão Eletrônica de Documentos

Sistema de Gestão Eletrônica de Documentos desenvolvido com Flask, SQL Server e Bootstrap. Uma solução corporativa completa para digitalização, armazenamento centralizado, organização hierárquica e controle de acesso a documentos.

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![Flask Version](https://img.shields.io/badge/flask-3.0%2B-green)
![SQL Server](https://img.shields.io/badge/sql%20server-2019%2B-red)
![License](https://img.shields.io/badge/license-Proprietary-orange)

## 📋 Índice

- [Características](#-características)
- [Capturas de Tela](#-capturas-de-tela)
- [Requisitos](#-requisitos)
- [Instalação](#-instalação)
- [Configuração](#-configuração)
- [Uso](#-uso)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Documentação](#-documentação)
- [Manutenção](#-manutenção)
- [Segurança](#-segurança)
- [Licença](#-licença)

## ✨ Características

### Gestão de Documentos
- 📤 **Upload de Documentos** - Suporte para múltiplos formatos (PDF, DOC, DOCX, XLS, XLSX, JPG, PNG, TIF)
- 📁 **Organização Hierárquica** - Categorias e pastas com até 5 níveis de profundidade
- 🏷️ **Tags e Metadados** - Classificação flexível com tags e metadados personalizados
- 🔍 **Busca Avançada** - Busca por nome, conteúdo (full-text), categoria, tags, data e mais
- 📊 **Versionamento** - Controle de versões com histórico completo (até 10 versões)
- 🗑️ **Lixeira** - Recuperação de documentos excluídos (30 dias de retenção)

### Segurança e Controle
- 🔐 **Autenticação Segura** - Login com proteção contra força bruta e bloqueio de conta
- 👥 **Controle de Acesso** - 5 perfis de usuário (Administrador, Gerente, Usuário, Auditor, Visitante)
- 🔒 **Permissões Granulares** - Controle de visualização, edição, exclusão e compartilhamento
- 🔑 **Criptografia** - Senhas com bcrypt, opção de criptografia AES-256 para documentos
- 📝 **Auditoria Completa** - Log de todas as operações com usuário, data, hora e IP

### Colaboração e Workflow
- 🤝 **Compartilhamento** - Compartilhe documentos com permissões específicas e datas de expiração
- ✅ **Workflows de Aprovação** - Processos de aprovação configuráveis com múltiplos estágios
- 📧 **Notificações por Email** - Alertas automáticos para uploads, compartilhamentos e aprovações
- 💬 **Comentários** - Histórico de comentários em aprovações e rejeições

### Administração
- 📊 **Dashboard Administrativo** - Estatísticas de uso, armazenamento e atividades
- 👤 **Gestão de Usuários** - Criação, edição, ativação/desativação de contas
- ⚙️ **Configurações do Sistema** - Parâmetros configuráveis (tamanho máximo, formatos permitidos)
- 📈 **Relatórios** - Relatórios de uso, acesso e armazenamento com exportação
- 💾 **Backup Automatizado** - Scripts para backup de banco de dados e arquivos

### Interface e Usabilidade
- 📱 **Design Responsivo** - Interface adaptável para desktop, tablet e mobile
- 🎨 **Interface Moderna** - Bootstrap 5 com design limpo e intuitivo
- ⚡ **Performance** - Suporte para 1000 usuários simultâneos e 500.000 documentos
- 🌐 **Compatibilidade** - Chrome 90+, Firefox 88+, Edge 90+, Safari 14+

## 📸 Capturas de Tela

> **Nota**: Adicione capturas de tela da aplicação nas seguintes seções:
> - Dashboard principal
> - Lista de documentos
> - Upload de documentos
> - Busca avançada
> - Visualização de documento
> - Painel administrativo

## 🔧 Requisitos

### Software Necessário

- **Python** 3.8 ou superior
- **SQL Server** 2019 ou superior
- **ODBC Driver 17** for SQL Server
- **Navegador Web** moderno (Chrome, Firefox, Edge, Safari)

### Requisitos de Hardware (Produção)

- **CPU**: 4 cores mínimo
- **RAM**: 8GB mínimo
- **Disco**: 100GB para aplicação + 2TB para armazenamento de documentos
- **Rede**: 100 Mbps mínimo

## 🚀 Instalação

### 1. Clone o Repositório

```bash
git clone <repository-url>
cd sistema-ged
```

### 2. Crie o Ambiente Virtual

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instale as Dependências

```bash
pip install -r requirements.txt
```

### 4. Configure o Banco de Dados

Crie o banco de dados no SQL Server:

```sql
CREATE DATABASE sistema_ged;
```

### 5. Configure as Variáveis de Ambiente

Copie o arquivo de exemplo e edite com suas configurações:

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

Edite o arquivo `.env` com suas configurações:

```env
# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-secret-key-here

# Database Configuration
DATABASE_SERVER=localhost
DATABASE_NAME=sistema_ged
DATABASE_USER=sa
DATABASE_PASSWORD=your-password-here
DATABASE_DRIVER=ODBC Driver 17 for SQL Server

# Admin User
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=admin123
ADMIN_NAME=System Administrator

# Upload Configuration
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=52428800

# Email Configuration (opcional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

### 6. Inicialize o Banco de Dados

Execute o script de inicialização que cria as tabelas e dados iniciais:

```bash
python init_db.py
```

Este script cria:
- Todas as tabelas do banco de dados
- 5 perfis de usuário (Administrador, Gerente, Usuário, Auditor, Visitante)
- 6 categorias padrão (Contratos, Faturas, RH, Jurídico, Técnico, Administrativo)
- Usuário administrador inicial

Para mais detalhes, consulte [DATABASE_SETUP.md](DATABASE_SETUP.md).

### 7. Execute a Aplicação

**Modo Desenvolvimento:**
```bash
python run.py
```

A aplicação estará disponível em: `http://localhost:5000`

**Modo Produção:**

Consulte a documentação de deployment em [deployment/DEPLOYMENT_GUIDE.md](deployment/DEPLOYMENT_GUIDE.md).

## ⚙️ Configuração

### Variáveis de Ambiente Principais

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `FLASK_ENV` | Ambiente (development/production) | development |
| `SECRET_KEY` | Chave secreta para sessões | (obrigatório) |
| `DATABASE_SERVER` | Servidor SQL Server | localhost |
| `DATABASE_NAME` | Nome do banco de dados | sistema_ged |
| `DATABASE_USER` | Usuário do banco | sa |
| `DATABASE_PASSWORD` | Senha do banco | (obrigatório) |
| `UPLOAD_FOLDER` | Pasta para uploads | uploads |
| `MAX_CONTENT_LENGTH` | Tamanho máximo de arquivo (bytes) | 52428800 (50MB) |

Para lista completa, consulte `.env.example`.

### Primeiro Acesso

1. Acesse `http://localhost:5000`
2. Faça login com as credenciais do administrador:
   - Email: `admin@example.com` (ou o configurado em `ADMIN_EMAIL`)
   - Senha: `admin123` (ou o configurado em `ADMIN_PASSWORD`)
3. **IMPORTANTE**: Altere a senha do administrador imediatamente!

## 📖 Uso

### Upload de Documentos

1. Acesse **Documentos** > **Upload**
2. Arraste arquivos ou clique para selecionar (até 10 arquivos simultâneos)
3. Preencha os metadados:
   - Nome do documento
   - Descrição
   - Categoria
   - Tags (separadas por vírgula)
4. Clique em **Enviar**

### Busca de Documentos

**Busca Simples:**
- Use a barra de busca no topo da página
- Digite palavras-chave do nome ou descrição

**Busca Avançada:**
1. Acesse **Buscar** > **Busca Avançada**
2. Aplique filtros:
   - Intervalo de datas
   - Categoria
   - Autor
   - Tipo de arquivo
   - Tamanho
   - Tags
3. Clique em **Buscar**

**Busca Full-Text:**
- Busca no conteúdo de arquivos PDF
- Acesse **Buscar** > **Busca Full-Text**

### Compartilhamento

1. Abra o documento
2. Clique em **Compartilhar**
3. Selecione o usuário
4. Escolha as permissões (Visualizar/Editar)
5. Defina data de expiração (opcional)
6. Clique em **Compartilhar**

### Workflows de Aprovação

**Criar Workflow:**
1. Acesse **Workflows** > **Novo Workflow**
2. Defina nome e descrição
3. Configure os estágios de aprovação
4. Adicione aprovadores para cada estágio
5. Salve o workflow

**Submeter Documento:**
1. Abra o documento
2. Clique em **Submeter para Aprovação**
3. Selecione o workflow
4. Adicione comentários
5. Clique em **Submeter**

**Aprovar/Rejeitar:**
1. Acesse **Workflows** > **Aprovações Pendentes**
2. Abra a aprovação
3. Revise o documento
4. Clique em **Aprovar** ou **Rejeitar**
5. Adicione comentários obrigatórios

### Administração

**Gerenciar Usuários:**
1. Acesse **Admin** > **Usuários**
2. Clique em **Novo Usuário** para criar
3. Edite usuários existentes clicando no ícone de edição
4. Ative/desative contas com o botão de status

**Visualizar Relatórios:**
1. Acesse **Admin** > **Relatórios**
2. Escolha o tipo de relatório:
   - Uso do sistema
   - Acessos
   - Armazenamento
3. Aplique filtros de data
4. Exporte em PDF ou Excel

**Auditoria:**
1. Acesse **Admin** > **Auditoria**
2. Filtre logs por:
   - Data
   - Usuário
   - Ação
   - Documento
3. Visualize detalhes de cada operação

## 📁 Estrutura do Projeto

```
sistema-ged/
├── app/                          # Aplicação principal
│   ├── __init__.py              # Factory da aplicação
│   ├── models/                  # Modelos de dados (SQLAlchemy)
│   │   ├── user.py             # Usuários e perfis
│   │   ├── document.py         # Documentos e versões
│   │   ├── category.py         # Categorias e pastas
│   │   ├── workflow.py         # Workflows e aprovações
│   │   └── audit.py            # Logs de auditoria
│   ├── repositories/            # Camada de acesso a dados
│   │   ├── base.py             # Repositório base
│   │   ├── user_repository.py
│   │   ├── document_repository.py
│   │   └── ...
│   ├── services/                # Lógica de negócio
│   │   ├── auth_service.py     # Autenticação
│   │   ├── document_service.py # Gestão de documentos
│   │   ├── search_service.py   # Busca
│   │   ├── workflow_service.py # Workflows
│   │   └── ...
│   ├── auth/                    # Blueprint de autenticação
│   │   ├── routes.py           # Rotas de login/logout
│   │   └── forms.py            # Formulários
│   ├── documents/               # Blueprint de documentos
│   │   ├── routes.py
│   │   └── forms.py
│   ├── categories/              # Blueprint de categorias
│   ├── search/                  # Blueprint de busca
│   ├── workflows/               # Blueprint de workflows
│   ├── admin/                   # Blueprint administrativo
│   ├── errors/                  # Tratamento de erros
│   │   ├── __init__.py
│   │   └── handlers.py
│   ├── utils/                   # Utilitários
│   │   ├── decorators.py       # Decoradores customizados
│   │   ├── file_handler.py     # Manipulação de arquivos
│   │   └── logging_config.py   # Configuração de logs
│   └── templates/               # Templates Jinja2
│       ├── base.html           # Template base
│       ├── auth/               # Templates de autenticação
│       ├── documents/          # Templates de documentos
│       └── ...
├── static/                      # Arquivos estáticos
│   ├── css/                    # Estilos CSS
│   │   └── custom.css
│   ├── js/                     # JavaScript
│   │   └── main.js
│   └── assets/                 # Imagens, ícones, etc.
├── migrations/                  # Migrações Alembic
│   └── versions/
├── scripts/                     # Scripts de manutenção
│   ├── backup_database.py      # Backup do banco
│   ├── backup_files.py         # Backup de arquivos
│   ├── cleanup_trash.py        # Limpeza de lixeira
│   └── ...
├── deployment/                  # Arquivos de deployment
│   ├── DEPLOYMENT_GUIDE.md     # Guia de deployment
│   ├── nginx_sistema_ged.conf  # Config NGINX
│   └── ...
├── docs/                        # Documentação adicional
│   ├── API_DOCUMENTATION.md    # Documentação da API
│   ├── LOGGING_AND_ERROR_HANDLING.md
│   └── ...
├── logs/                        # Logs da aplicação
├── uploads/                     # Arquivos enviados
├── backups/                     # Backups
├── config.py                    # Configurações
├── run.py                       # Ponto de entrada (dev)
├── wsgi.py                      # Ponto de entrada (prod)
├── init_db.py                   # Inicialização do banco
├── seed_data.py                 # Dados iniciais
├── requirements.txt             # Dependências Python
├── .env.example                 # Exemplo de variáveis
├── .gitignore                   # Arquivos ignorados
└── README.md                    # Este arquivo
```

## 📚 Documentação

### Documentação Técnica

- **[API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md)** - Documentação completa da API REST
- **[DATABASE_SETUP.md](DATABASE_SETUP.md)** - Guia de configuração do banco de dados
- **[LOGGING_AND_ERROR_HANDLING.md](docs/LOGGING_AND_ERROR_HANDLING.md)** - Sistema de logs e erros
- **[PERMISSION_SYSTEM_GUIDE.md](docs/PERMISSION_SYSTEM_GUIDE.md)** - Sistema de permissões
- **[SEARCH_FUNCTIONALITY.md](docs/SEARCH_FUNCTIONALITY.md)** - Funcionalidade de busca

### Deployment e Manutenção

- **[deployment/DEPLOYMENT_GUIDE.md](deployment/DEPLOYMENT_GUIDE.md)** - Guia completo de deployment
- **[deployment/QUICK_START.md](deployment/QUICK_START.md)** - Início rápido para deployment
- **[deployment/WINDOWS_DEPLOYMENT.md](deployment/WINDOWS_DEPLOYMENT.md)** - Deployment no Windows
- **[deployment/TROUBLESHOOTING.md](deployment/TROUBLESHOOTING.md)** - Solução de problemas
- **[scripts/README.md](scripts/README.md)** - Scripts de backup e manutenção
- **[scripts/BACKUP_SCHEDULING.md](scripts/BACKUP_SCHEDULING.md)** - Agendamento de backups

## 🔧 Manutenção

### Backup

**Backup Manual:**

```bash
# Backup do banco de dados
python scripts/backup_database.py

# Backup de arquivos
python scripts/backup_files.py

# Backup completo
python scripts/backup_all.py
```

**Backup Automatizado:**

Configure tarefas agendadas (cron/Task Scheduler). Consulte [scripts/BACKUP_SCHEDULING.md](scripts/BACKUP_SCHEDULING.md).

### Limpeza

```bash
# Limpar lixeira (documentos > 30 dias)
python scripts/cleanup_trash.py

# Limpar tokens expirados
python scripts/cleanup_tokens.py

# Limpar logs antigos
python scripts/cleanup_audit_logs.py

# Limpeza completa
python scripts/cleanup_all.py
```

### Monitoramento

**Logs da Aplicação:**
```bash
# Linux
tail -f logs/ged_system.log

# Windows
Get-Content logs\ged_system.log -Tail 50 -Wait
```

**Verificar Status:**
```bash
# Espaço em disco
df -h  # Linux
Get-PSDrive  # Windows

# Processos
ps aux | grep gunicorn  # Linux
Get-Process | Where-Object {$_.Name -like "*python*"}  # Windows
```

## 🔒 Segurança

### Práticas de Segurança Implementadas

- ✅ **Senhas**: Hash bcrypt com fator de custo 12
- ✅ **Proteção contra Força Bruta**: Bloqueio após 5 tentativas (15 minutos)
- ✅ **HTTPS**: TLS 1.2+ obrigatório em produção
- ✅ **CSRF**: Tokens de proteção em todas as operações
- ✅ **XSS**: Sanitização de entradas e encoding de saídas
- ✅ **SQL Injection**: Queries parametrizadas via ORM
- ✅ **Rate Limiting**: 100 requisições/minuto por IP
- ✅ **Headers de Segurança**: X-Frame-Options, CSP, HSTS
- ✅ **Auditoria**: Log completo de todas as operações
- ✅ **Criptografia**: Opção de AES-256 para documentos sensíveis

### Checklist de Segurança para Produção

Antes de colocar em produção:

- [ ] Gerar `SECRET_KEY` forte e único
- [ ] Usar senha forte para banco de dados
- [ ] Instalar certificado SSL/TLS válido
- [ ] Configurar firewall (portas 80, 443)
- [ ] Definir permissões corretas de arquivos
- [ ] Proteger arquivo `.env` (chmod 600)
- [ ] Alterar senha padrão do administrador
- [ ] Atualizar todas as dependências
- [ ] Configurar backups automatizados
- [ ] Testar restauração de backup
- [ ] Realizar auditoria de segurança

### Conformidade

- **LGPD**: Suporte para anonimização, exportação e exclusão de dados
- **Auditoria**: Logs imutáveis retidos por 1 ano
- **Retenção**: Backups retidos por 90 dias

## 🛠️ Tecnologias Utilizadas

### Backend
- **Flask 3.0+** - Framework web Python
- **SQLAlchemy** - ORM para banco de dados
- **Flask-Login** - Gestão de sessões
- **Flask-WTF** - Formulários e CSRF
- **PyODBC** - Driver SQL Server
- **Werkzeug** - Utilitários de segurança
- **PyPDF2** - Processamento de PDFs
- **python-magic** - Validação de tipos de arquivo

### Frontend
- **Bootstrap 5.3** - Framework CSS
- **jQuery 3.7** - Biblioteca JavaScript
- **DataTables** - Tabelas interativas
- **Select2** - Campos de seleção avançados
- **Dropzone.js** - Upload de arquivos
- **Chart.js** - Gráficos e visualizações

### Banco de Dados
- **SQL Server 2019+** - RDBMS
- **Full-Text Search** - Busca em conteúdo

### Infraestrutura
- **Gunicorn** - Servidor WSGI
- **NGINX** - Proxy reverso
- **Supervisor** - Gerenciador de processos

## 🤝 Contribuindo

Este é um projeto proprietário. Para contribuições, entre em contato com a equipe de desenvolvimento.

## 📄 Licença

Proprietary - Todos os direitos reservados

Copyright © 2024 [Sua Empresa]

## 📞 Suporte

Para suporte técnico ou dúvidas:

- **Email**: suporte@example.com
- **Documentação**: Consulte a pasta `docs/`
- **Issues**: Entre em contato com o administrador do sistema

## 🗺️ Roadmap

Funcionalidades planejadas para versões futuras:

- [ ] Integração com Active Directory/LDAP
- [ ] Assinatura digital de documentos
- [ ] OCR para documentos escaneados
- [ ] Aplicativo mobile (iOS/Android)
- [ ] Integração com Microsoft Office Online
- [ ] Suporte para armazenamento em nuvem (S3, Azure Blob)
- [ ] API REST completa para integrações
- [ ] Webhooks para eventos do sistema
- [ ] Dashboard de analytics avançado
- [ ] Suporte multilíngue

---

**Desenvolvido com ❤️ usando Flask e Python**
