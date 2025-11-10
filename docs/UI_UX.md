# UI/UX - Sistema SGDI

## Arquivos SCSS

O projeto utiliza SCSS (Sass) para gerenciar os estilos CSS de forma modular e organizada.

### Estrutura de Arquivos

```
static/assets/
├── base.scss                    # Arquivo principal que importa todos os outros
├── components/                  # Componentes de terceiros
│   ├── bootstrap5/             # Bootstrap 5 customizado
│   ├── icons/                  # Ícones (FontAwesome)
│   ├── hamburgers/             # Botões hamburger animados
│   ├── notifications/          # Toasts e notificações
│   ├── perfect-scrollbar/      # Scrollbar customizada
│   └── ...
├── layout/                      # Layout da aplicação
│   ├── header/                 # Cabeçalho e navbar
│   ├── sidebar/                # Barra lateral de navegação
│   ├── footer/                 # Rodapé
│   └── main/                   # Área de conteúdo principal
├── elements/                    # Elementos da UI (botões, cards, forms, etc.)
├── utils/                       # Utilitários (animações, helpers, backgrounds)
├── themes/                      # Temas e variáveis de cores
└── widgets/                     # Widgets e componentes especiais

```

### Compilação do SCSS

#### Requisitos

- Node.js e npm instalados
- Dependências instaladas: `npm install`

#### Comandos Disponíveis

**1. Compilar uma vez (produção):**
```bash
npm run build:css
```

**2. Modo watch (desenvolvimento):**
```bash
npm run watch:css
```
Este comando monitora alterações nos arquivos SCSS e recompila automaticamente.

**3. Modo dev (com source maps):**
```bash
npm run dev
```

#### Script Python

Você também pode usar o script Python:

```bash
# Compilar uma vez
python scripts/build_css.py

# Modo watch
python scripts/build_css.py --watch
```

### Arquivo Compilado

O arquivo compilado é salvo em:
- `static/css/base.css` (versão comprimida para produção)

Este arquivo é automaticamente referenciado no template `base.html`.

### Customização

#### Variáveis de Tema

As variáveis principais estão em:
- `static/assets/themes/layout-variables.scss` - Layout e cores
- `static/assets/components/bootstrap5/_variables.scss` - Bootstrap customizado

#### Cores Principais

Edite `static/assets/themes/layout-variables.scss` para alterar:
- Cores do tema (primária, secundária, etc.)
- Espaçamentos
- Tipografia
- Breakpoints responsivos

#### Layout

Para customizar header, sidebar e footer, edite os arquivos em:
- `static/assets/layout/header/`
- `static/assets/layout/sidebar/`
- `static/assets/layout/footer/`

### Integração com Templates

O CSS compilado é incluído no template base:

```html
<!-- app/templates/base.html -->
<link rel="stylesheet" href="{{ url_for('static', filename='css/base.css') }}">
```

Todos os outros templates herdam de `base.html` e automaticamente incluem os estilos.

### Bibliotecas Incluídas

O arquivo `base.css` compilado inclui:

✅ **Bootstrap 5** - Framework CSS completo
✅ **FontAwesome** - Ícones
✅ **Animações CSS** - animate-sass
✅ **Layout responsivo** - Header, Sidebar, Footer
✅ **Componentes UI** - Botões, cards, forms, modals, etc.
✅ **Utilitários** - Helpers, backgrounds, animações

### Desenvolvimento

#### Workflow Recomendado

1. Inicie o modo watch:
   ```bash
   npm run watch:css
   ```

2. Edite os arquivos SCSS em `static/assets/`

3. O CSS será recompilado automaticamente

4. Atualize o navegador para ver as alterações

#### Evitar Conflitos

- Não edite diretamente o arquivo `static/css/base.css` - ele será sobrescrito
- Sempre edite os arquivos `.scss` na pasta `static/assets/`
- Para estilos específicos do projeto, adicione em `static/css/custom.css`

### Troubleshooting

**Erro ao compilar:**
```bash
npm install  # Reinstalar dependências
npm run build:css  # Tentar compilar novamente
```

**CSS não aparece no navegador:**
1. Limpe o cache do navegador (Ctrl+F5)
2. Verifique se o arquivo `static/css/base.css` existe
3. Verifique o console do navegador por erros 404

**Mudanças não aparecem:**
1. Certifique-se de que o modo watch está rodando
2. Verifique se editou o arquivo SCSS correto
3. Limpe o cache do navegador

### Performance

O arquivo CSS é compilado em modo **compressed** para produção, resultando em:
- Tamanho reduzido (~492KB)
- Carregamento mais rápido
- Sem source maps (em produção)

Para desenvolvimento com source maps, use:
```bash
npm run dev
```

---

**Nota:** Os arquivos SCSS usam a sintaxe moderna do Sass com `@use` e `@import`. Avisos de deprecação sobre `@import` não afetam o funcionamento atual.
