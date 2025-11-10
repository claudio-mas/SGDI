# Guia de Compilação SCSS

## Visão Geral

Este projeto utiliza arquivos SCSS (Sass) para estilização, compilados para CSS otimizado. O arquivo principal `static/assets/base.scss` importa todos os componentes necessários do tema ArchitectUI.

## Estrutura de Arquivos SCSS

```
static/assets/
├── base.scss                    # Arquivo principal (ponto de entrada)
├── components/
│   ├── bootstrap5/              # Bootstrap 5 completo
│   ├── calendar/                # Componentes de calendário
│   ├── hamburgers/              # Menu hamburger
│   ├── icons/                   # FontAwesome e outros ícones
│   ├── maps/                    # Mapas vetoriais
│   ├── notifications/           # Toastr e notificações
│   ├── perfect-scrollbar/       # Scrollbar customizado
│   ├── popovers-tooltips/       # Popovers e tooltips
│   └── tables/                  # Tabelas DataTables
├── demo-ui/                     # Elementos de demonstração
├── elements/                    # Elementos UI (botões, cards, etc.)
├── layout/                      # Layout e estrutura
├── themes/                      # Variáveis de tema
├── utils/                       # Utilitários e helpers
└── widgets/                     # Widgets e caixas de conteúdo
```

## Compilação

### Método 1: Script Python (Recomendado)

```bash
# Compilação única
python scripts/build_css.py

# Modo watch (recompila automaticamente ao salvar)
python scripts/build_css.py --watch
```

### Método 2: NPM Direto

```bash
# Compilação única
npm run build:css

# Modo watch
npm run watch:css

# Modo desenvolvimento (sem compressão)
npm run dev
```

## Arquivo Gerado

- **Entrada**: `static/assets/base.scss`
- **Saída**: `static/css/base.css`
- **Tamanho**: ~492 KB (comprimido)

O arquivo `base.css` inclui:
- ✅ Bootstrap 5 completo
- ✅ FontAwesome icons
- ✅ Layout responsivo
- ✅ Componentes UI (cards, modals, forms, etc.)
- ✅ Animações e transições
- ✅ Utilities e helpers
- ✅ Tema ArchitectUI

## Integração nos Templates

### Template Base

O arquivo `app/templates/base.html` já está configurado para usar o CSS compilado:

```html
<!-- Compiled CSS - Includes Bootstrap 5, FontAwesome, Layout, and Components -->
<link rel="stylesheet" href="{{ url_for('static', filename='css/base.css') }}">

<!-- Bootstrap Icons -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css">

<!-- Custom CSS -->
<link rel="stylesheet" href="{{ url_for('static', filename='css/custom.css') }}">
<link rel="stylesheet" href="{{ url_for('static', filename='css/ui_overrides.css') }}">
<link rel="stylesheet" href="{{ url_for('static', filename='css/animations.css') }}">
```

### Ordem de Carregamento

1. **base.css** - Estilos principais do tema
2. **Bootstrap Icons** - Ícones do Bootstrap
3. **custom.css** - Customizações específicas do projeto
4. **ui_overrides.css** - Sobrescritas de acessibilidade
5. **animations.css** - Animações adicionais
6. **extra_css** (block) - CSS específico de página

## Customização

### Modificar Variáveis de Tema

Edite `static/assets/themes/_layout-variables.scss`:

```scss
// Cores primárias
$primary: #007bff;
$secondary: #6c757d;

// Espaçamentos
$spacer: 1rem;

// Breakpoints
$grid-breakpoints: (
  xs: 0,
  sm: 576px,
  md: 768px,
  lg: 992px,
  xl: 1200px,
  xxl: 1400px
);
```

### Adicionar Novos Estilos

1. Crie arquivo SCSS em `static/assets/`
2. Importe no `base.scss`:
   ```scss
   @import "meu-componente";
   ```
3. Recompile o CSS

## Solução de Problemas

### Warnings de Deprecação

É normal ver avisos de deprecação do Sass/Bootstrap 5. Eles não afetam a funcionalidade e serão resolvidos em futuras versões do Bootstrap.

### CSS Não Atualiza

1. Limpe o cache do navegador (Ctrl+Shift+R)
2. Recompile o CSS: `python scripts/build_css.py`
3. Reinicie o servidor Flask

### Erros de Compilação

```bash
# Verifique se as dependências estão instaladas
npm install

# Verifique a sintaxe SCSS
npm run build:css
```

## Desenvolvimento

### Modo Watch Recomendado

Durante o desenvolvimento, use o modo watch para recompilar automaticamente:

```bash
# Terminal 1: Watch CSS
python scripts/build_css.py --watch

# Terminal 2: Servidor Flask
python run.py
```

### Performance

- **Produção**: Use `build:css` (comprimido, ~492 KB)
- **Desenvolvimento**: Use `dev` (não comprimido, mais fácil debug)

## Dependências NPM

```json
{
  "@fortawesome/fontawesome-free": "^7.1.0",
  "animate-sass": "^0.8.2",
  "sass": "^1.70.0"
}
```

Instale com: `npm install`

## Arquivos CSS Adicionais

Além do `base.css`, o projeto inclui:

- **custom.css** - Estilos customizados do projeto GED
- **ui_overrides.css** - Melhorias de acessibilidade e UX
- **animations.css** - Animações específicas

Estes arquivos **não** precisam ser compilados, são CSS direto.

## Comandos Úteis

```bash
# Ver tamanho do CSS compilado
Get-Item static/css/base.css | Select-Object Name, Length, LastWriteTime

# Verificar se SCSS tem erros de sintaxe
npm run build:css

# Limpar e recompilar
Remove-Item static/css/base.css -ErrorAction SilentlyContinue
npm run build:css
```

## Manutenção

### Atualizar Bootstrap

1. Atualize no package.json (se necessário)
2. Execute `npm install`
3. Recompile: `npm run build:css`
4. Teste todos os componentes

### Atualizar FontAwesome

1. Atualize no package.json
2. Execute `npm install`
3. Recompile: `npm run build:css`

## Conclusão

O sistema de compilação SCSS está totalmente integrado e funcional. O arquivo `base.css` inclui todos os estilos necessários do tema ArchitectUI e Bootstrap 5, otimizado para produção.

**Status**: ✅ Integração Completa
**Última Compilação**: 09/11/2025 22:33:50
**Tamanho**: 492 KB
