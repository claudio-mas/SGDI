# Assets - SCSS Source Files

Esta pasta contém todos os arquivos fonte SCSS do tema ArchitectUI que são compilados para CSS.

## 📁 Estrutura

```
assets/
├── base.scss                # 🎯 ARQUIVO PRINCIPAL - Ponto de entrada
│
├── components/              # Componentes de terceiros
│   ├── bootstrap5/          # Bootstrap 5 completo
│   ├── calendar/            # Componentes de calendário
│   ├── hamburgers/          # Animações menu hamburger
│   ├── icons/               # FontAwesome e outros ícones
│   ├── maps/                # Mapas vetoriais
│   ├── notifications/       # Toastr e notificações
│   ├── perfect-scrollbar/   # Scrollbar customizado
│   ├── popovers-tooltips/   # Popovers e tooltips
│   └── tables/              # Estilos para tabelas
│
├── demo-ui/                 # Elementos de demonstração
│   ├── elements/
│   ├── images/
│   └── _demo.scss
│
├── elements/                # Elementos UI customizados
│   ├── _accordions.scss
│   ├── _badges.scss
│   ├── _buttons.scss
│   ├── _cards.scss
│   ├── _dropdown.scss
│   ├── _forms.scss
│   ├── _listgroup.scss
│   ├── _modals.scss
│   ├── _navs.scss
│   ├── _pagination.scss
│   └── _tabs.scss
│
├── layout/                  # Layout e estrutura
│   ├── _layout.scss         # Layout principal
│   ├── _layout-variables.scss
│   └── responsive/          # Estilos responsivos
│
├── themes/                  # Temas e variáveis
│   ├── default/             # Tema padrão
│   │   └── _variables.scss
│   └── _layout-variables.scss
│
├── utils/                   # Utilitários e helpers
│   ├── _animate.scss
│   ├── _animate-override.scss
│   ├── _backgrounds.scss
│   ├── _comps-animations.scss
│   ├── _helpers.scss
│   └── helpers/
│       ├── _grayscale.scss
│       └── _opacity.scss
│
└── widgets/                 # Widgets customizados
    └── content-boxes/
        └── _content-boxes.scss
```

## 🔨 Compilação

### Arquivo de Entrada
**`base.scss`** - Este é o arquivo principal que importa todos os outros arquivos SCSS.

### Arquivo de Saída
**`../css/base.css`** - CSS compilado e otimizado (480 KB).

### Como Compilar

```bash
# Compilação única
python scripts/build_css.py

# Modo watch (recompila automaticamente)
python scripts/build_css.py --watch

# Usando NPM
npm run build:css
npm run watch:css
```

## 🎨 Customização

### Modificar Variáveis de Tema

Edite `themes/_layout-variables.scss` ou `themes/default/_variables.scss`:

```scss
// Exemplo: Alterar cor primária
$primary: #007bff;
$secondary: #6c757d;

// Exemplo: Ajustar espaçamentos
$spacer: 1rem;

// Exemplo: Customizar breakpoints
$grid-breakpoints: (
  xs: 0,
  sm: 576px,
  md: 768px,
  lg: 992px,
  xl: 1200px,
  xxl: 1400px
);
```

Após modificar, recompile: `python scripts/build_css.py`

### Adicionar Novos Componentes

1. Crie arquivo SCSS (ex: `elements/_meu-componente.scss`)
2. Adicione import no `base.scss`:
   ```scss
   @import "elements/meu-componente";
   ```
3. Recompile o CSS

### Sobrescrever Estilos Bootstrap

Edite `themes/default/_variables.scss` **antes** do import do Bootstrap no `base.scss`.

## 📦 O que está incluído

### Bootstrap 5
- Grid System completo
- Todos os componentes (buttons, forms, cards, modals, etc.)
- Utilities API
- Responsive breakpoints

### FontAwesome 7.1.0
- Ícones completos
- Estilos solid, regular, brands

### ArchitectUI Theme
- Layout moderno
- Sidebar customizado
- Dashboard components
- Animações suaves

### Utilitários
- Helpers de background
- Animações (via animate-sass)
- Opacity & grayscale helpers
- Component animations

## ⚠️ Importante

### NÃO EDITE DIRETAMENTE
- ❌ `static/css/base.css` - Este arquivo é GERADO automaticamente
- ❌ `components/bootstrap5/*` - Arquivos do Bootstrap (use variáveis para customizar)

### EDITE AQUI
- ✅ `themes/_layout-variables.scss` - Variáveis principais
- ✅ `themes/default/_variables.scss` - Variáveis do Bootstrap
- ✅ `elements/*` - Componentes customizados
- ✅ `static/css/custom.css` - CSS adicional que não precisa compilar

## 🔍 Debugging

### Ver estrutura compilada

O arquivo `base.scss` importa componentes nesta ordem:

1. **Functions** - Funções Sass
2. **Variables** - Variáveis de tema
3. **Bootstrap Core** - Base do Bootstrap 5
4. **Layout** - Estrutura de layout
5. **Utils** - Utilitários
6. **Elements** - Componentes customizados
7. **Widgets** - Widgets específicos
8. **Components** - Bibliotecas externas
9. **Responsive** - Media queries

### Verificar warnings

Warnings de deprecação do Sass são normais e não afetam funcionalidade.

## 📚 Documentação

- `/docs/SCSS_COMPILATION_GUIDE.md` - Guia completo
- `/docs/SCSS_INTEGRATION_REPORT.md` - Relatório de integração
- `/SCSS_QUICK_REFERENCE.md` - Referência rápida

## 🔗 Links Úteis

- [Bootstrap 5 Docs](https://getbootstrap.com/docs/5.3/)
- [Sass Documentation](https://sass-lang.com/documentation/)
- [FontAwesome Icons](https://fontawesome.com/icons)

---

**Última atualização**: 09/11/2025  
**Versão Tema**: ArchitectUI v4.1.0  
**Bootstrap**: 5.x  
**Sass**: 1.70.0
