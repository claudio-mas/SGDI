# Guia de Ícones - Sistema GED

## Padronização: Bootstrap Icons

Todos os ícones do sistema agora utilizam **Bootstrap Icons** para consistência visual.

### Ícones por Categoria

#### 📄 **Documentos**
- `bi-file-earmark` - Arquivo genérico
- `bi-file-earmark-text` - Documento de texto
- `bi-file-earmark-pdf` - PDF
- `bi-file-earmark-word` - Word
- `bi-file-earmark-excel` - Excel
- `bi-file-earmark-ppt` - PowerPoint
- `bi-file-earmark-image` - Imagem
- `bi-file-earmark-zip` - Arquivo compactado

#### 📁 **Navegação**
- `bi-folder` - Pasta
- `bi-folder-open` - Pasta aberta
- `bi-folder-plus` - Nova pasta
- `bi-house-door` - Início
- `bi-arrow-left` - Voltar
- `bi-arrow-right` - Avançar

#### ⚙️ **Ações**
- `bi-cloud-upload` - Upload
- `bi-download` - Download
- `bi-eye` - Visualizar
- `bi-pencil` - Editar
- `bi-trash` - Excluir
- `bi-arrow-counterclockwise` - Restaurar/Desfazer
- `bi-share` - Compartilhar
- `bi-printer` - Imprimir

#### 🔍 **Busca e Filtros**
- `bi-search` - Buscar
- `bi-funnel` - Filtros
- `bi-filter` - Filtrar
- `bi-x` - Limpar/Fechar

#### 👤 **Usuário**
- `bi-person` - Usuário
- `bi-person-circle` - Avatar
- `bi-people` - Usuários (plural)
- `bi-key` - Senha
- `bi-shield-lock` - Segurança/Permissões

#### 📊 **Administração**
- `bi-speedometer2` - Dashboard
- `bi-gear` - Configurações
- `bi-graph-up` - Relatórios
- `bi-clipboard-data` - Estatísticas

#### 🔔 **Notificações e Status**
- `bi-bell` - Notificações
- `bi-bell-slash` - Sem notificações
- `bi-check-circle` - Sucesso
- `bi-exclamation-triangle` - Alerta/Erro
- `bi-info-circle` - Informação
- `bi-hourglass-split` - Aguardando

#### 🔄 **Workflows**
- `bi-diagram-3` - Workflow
- `bi-clock-history` - Histórico/Recentes
- `bi-check2-circle` - Aprovado
- `bi-x-circle` - Rejeitado

#### 📱 **Interface**
- `bi-list` - Visualização em lista
- `bi-grid` - Visualização em grade
- `bi-plus-circle` - Adicionar
- `bi-three-dots-vertical` - Menu de opções
- `bi-star` - Favorito
- `bi-star-fill` - Favorito marcado

### Exemplos de Uso

```html
<!-- Botão com ícone -->
<button class="btn btn-primary">
    <i class="bi bi-cloud-upload me-2"></i>
    Enviar Documento
</button>

<!-- Link com ícone -->
<a href="#" class="nav-link">
    <i class="bi bi-folder me-2"></i>
    Categorias
</a>

<!-- Ícone grande (empty state) -->
<div class="empty-state-icon">
    <i class="bi bi-inbox"></i>
</div>
```

### Tamanhos Personalizados

```html
<!-- Usando classes do Bootstrap -->
<i class="bi bi-search fs-1"></i> <!-- Extra grande -->
<i class="bi bi-search fs-3"></i> <!-- Grande -->
<i class="bi bi-search fs-5"></i> <!-- Normal -->
<i class="bi bi-search fs-6"></i> <!-- Pequeno -->

<!-- Usando CSS personalizado -->
<i class="bi bi-search" style="font-size: 2rem;"></i>
```

### Cores

```html
<!-- Usando classes de texto do Bootstrap -->
<i class="bi bi-check-circle text-success"></i>
<i class="bi bi-exclamation-triangle text-warning"></i>
<i class="bi bi-x-circle text-danger"></i>
<i class="bi bi-info-circle text-info"></i>
<i class="bi bi-star text-primary"></i>
```

### Migração de Font Awesome para Bootstrap Icons

| Font Awesome | Bootstrap Icons |
|-------------|-----------------|
| `fa-upload` | `bi-cloud-upload` |
| `fa-download` | `bi-download` |
| `fa-edit` | `bi-pencil` |
| `fa-trash` | `bi-trash` |
| `fa-eye` | `bi-eye` |
| `fa-user` | `bi-person` |
| `fa-folder` | `bi-folder` |
| `fa-search` | `bi-search` |
| `fa-cog` | `bi-gear` |
| `fa-times` | `bi-x` |
| `fa-check` | `bi-check` |
| `fa-plus` | `bi-plus` |

## Referência Completa

Para ver todos os ícones disponíveis:
https://icons.getbootstrap.com/
