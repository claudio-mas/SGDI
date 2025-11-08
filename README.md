# Sistema GED - Gestão Eletrônica de Documentos

Sistema de Gestão Eletrônica de Documentos desenvolvido com Flask, SQL Server e Bootstrap.

## Características

- Autenticação e autorização de usuários
- Upload e armazenamento de documentos
- Organização hierárquica com categorias e pastas
- Busca avançada e full-text
- Controle de acesso e permissões
- Versionamento de documentos
- Workflows de aprovação
- Auditoria completa
- Interface responsiva

## Requisitos

- Python 3.8+
- SQL Server 2019+
- ODBC Driver 17 for SQL Server

## Instalação

1. Clone o repositório:
```bash
git clone <repository-url>
cd sistema-ged
```

2. Crie e ative o ambiente virtual:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente:
```bash
copy .env.example .env
# Edite o arquivo .env com suas configurações
```

5. Inicialize o banco de dados:
```bash
flask db upgrade
```

6. Execute a aplicação:
```bash
python run.py
```

## Estrutura do Projeto

```
sistema-ged/
├── app/
│   ├── __init__.py
│   ├── models/
│   ├── repositories/
│   ├── services/
│   ├── auth/
│   ├── documents/
│   ├── categories/
│   ├── search/
│   ├── workflows/
│   ├── admin/
│   ├── errors/
│   ├── utils/
│   └── templates/
├── static/
│   ├── css/
│   ├── js/
│   └── assets/
├── migrations/
├── tests/
├── config.py
├── run.py
└── requirements.txt
```

## Licença

Proprietary - Todos os direitos reservados
