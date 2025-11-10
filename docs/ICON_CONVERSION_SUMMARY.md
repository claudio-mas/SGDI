# Conversão de Font Awesome para Bootstrap Icons

## Resumo da Conversão

### Data da Conversão
10 de novembro de 2025

### Objetivo
Substituir todos os ícones Font Awesome por Bootstrap Icons em todos os templates do sistema GED.

### Motivo
Os ícones Font Awesome não estavam sendo exibidos corretamente no sistema. Bootstrap Icons já estava carregado no `base.html` e é uma solução mais leve e integrada com o Bootstrap 5.

## Arquivos Processados

### Total de Templates
- **55 arquivos HTML** processados
- **26 arquivos** convertidos na primeira passagem
- **7 arquivos** corrigidos na segunda passagem (conversões parciais)
- **4 arquivos** ajustados manualmente (templates com expressões Jinja dinâmicas)

### Scripts Criados

1. **convert_icons.py**
   - Script principal de conversão automática
   - Converte classes `fas`, `far`, `fab` para `bi`
   - Mapeia ícones Font Awesome para equivalentes Bootstrap Icons
   - Converte modificadores de tamanho (`fa-2x` → `fs-2`)
   - Converte animações (`fa-spin` → `spinner-border`)

2. **fix_partial_icon_conversions.py**
   - Corrige conversões parciais (ex: `class="bi fa-icon"`)
   - Trata ícones específicos que não foram capturados na primeira passagem

## Mapeamento de Ícones

### Principais Conversões

| Font Awesome | Bootstrap Icons | Uso |
|--------------|-----------------|-----|
| `fa-tachometer-alt` | `bi-speedometer2` | Dashboard |
| `fa-users` | `bi-people-fill` | Usuários |
| `fa-file-alt` | `bi-file-earmark-text` | Documentos |
| `fa-hdd` | `bi-hdd` | Armazenamento |
| `fa-chart-line` | `bi-graph-up` | Gráficos |
| `fa-chart-pie` | `bi-pie-chart` | Gráficos de pizza |
| `fa-history` | `bi-clock-history` | Histórico |
| `fa-download` | `bi-download` | Download |
| `fa-upload` | `bi-upload` | Upload |
| `fa-edit` | `bi-pencil` | Editar |
| `fa-trash` | `bi-trash` | Excluir |
| `fa-save` | `bi-save` | Salvar |
| `fa-search` | `bi-search` | Busca |
| `fa-folder` | `bi-folder` | Pastas |
| `fa-eye` | `bi-eye` | Visualizar |
| `fa-lock` | `bi-lock-fill` | Bloqueio/Segurança |
| `fa-check` | `bi-check-lg` | Confirmação |
| `fa-times` | `bi-x-lg` | Cancelar/Fechar |

### Modificadores de Tamanho

| Font Awesome | Bootstrap | Tamanho |
|--------------|-----------|---------|
| `fa-lg` | `fs-5` | Grande |
| `fa-2x` | `fs-2` | 2x |
| `fa-3x` | `fs-3` | 3x |
| `fa-4x` | `fs-4` | 4x |
| `fa-5x` | `fs-5` | 5x |

### Animações

| Font Awesome | Bootstrap |
|--------------|-----------|
| `fa-spin` | `spinner-border spinner-border-sm` |

## Arquivos Modificados

### Admin
- `dashboard.html` - Dashboard administrativo
- `reports.html` - Relatórios
- `report_access.html` - Relatório de acesso
- `report_storage.html` - Relatório de armazenamento
- `report_usage.html` - Relatório de uso
- `settings.html` - Configurações
- `users.html` - Gerenciamento de usuários
- `user_form.html` - Formulário de usuário
- `user_reset_password.html` - Redefinição de senha

### Categories
- `folders.html` - Lista de pastas
- `folder_form.html` - Formulário de pasta
- `folder_view.html` - Visualização de pasta
- `form.html` - Formulário de categoria
- `view.html` - Visualização de categoria
- `_folder_tree_sidebar.html` - Sidebar de árvore de pastas

### Documents
- `edit.html` - Edição de documento
- `upload.html` - Upload de documento
- `view.html` - Visualização de documento

### Errors
- `403.html` - Erro de acesso negado
- `404.html` - Página não encontrada
- `429.html` - Muitas requisições
- `500.html` - Erro interno

### Workflows
- `approvals.html` - Lista de aprovações
- `approval_detail.html` - Detalhes de aprovação
- `form.html` - Formulário de workflow
- `list.html` - Lista de workflows

## Ajustes Manuais Necessários

### Templates com Expressões Jinja Dinâmicas

1. **workflows/list.html**
   - Linha 70: Ícone de pausa/play dinâmico
   - Linha 116: JavaScript para alternar ícone

2. **workflows/approval_detail.html**
   - Linha 10: Ícone de status dinâmico
   - Linha 135: Ícone de ação (aprovado/rejeitado)

3. **admin/users.html**
   - Linha 132: Ícone de ativar/desativar usuário

## Verificação de Qualidade

### Comandos Executados

```bash
# Conversão inicial
python scripts/convert_icons.py

# Correção de conversões parciais
python scripts/fix_partial_icon_conversions.py

# Verificação de ícones Font Awesome remanescentes
grep -r "fa-" app/templates/**/*.html  # Resultado: nenhuma correspondência
grep -r "fas\|far\|fab" app/templates/**/*.html  # Resultado: nenhuma correspondência
```

## Benefícios da Conversão

1. **Consistência Visual**: Todos os ícones agora usam a mesma biblioteca
2. **Performance**: Bootstrap Icons é mais leve que Font Awesome
3. **Manutenibilidade**: Menos dependências externas
4. **Integração**: Melhor integração com Bootstrap 5
5. **Licença**: MIT License (mais permissiva)

## Observações

- O arquivo `base.css` ainda contém código Font Awesome compilado, mas não está mais sendo utilizado
- Pode ser removido em uma futura atualização de limpeza de código
- Bootstrap Icons já estava carregado via CDN no `base.html`
- Não foram necessárias alterações no código Python (backend)

## Próximos Passos

1. ✅ Testar visualmente todas as páginas do sistema
2. ⚠️ Considerar remover Font Awesome do `base.css` (futura otimização)
3. ⚠️ Atualizar documentação de desenvolvimento
4. ⚠️ Criar changelog da versão
