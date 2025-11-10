# Quick Reference - SCSS Compilation

## 🚀 Comandos Rápidos

```bash
# Compilar SCSS → CSS
python scripts/build_css.py

# Modo watch (auto-recompila)
python scripts/build_css.py --watch

# Via NPM
npm run build:css
npm run watch:css
```

## 📁 Estrutura

```
static/
├── assets/
│   ├── base.scss          ← Arquivo principal SCSS
│   ├── components/        ← Bootstrap 5, Icons, etc.
│   ├── layout/            ← Layout e estrutura
│   ├── themes/            ← Variáveis de tema
│   ├── elements/          ← Buttons, Cards, Forms, etc.
│   ├── utils/             ← Helpers e utilitários
│   └── widgets/           ← Widgets customizados
│
└── css/
    ├── base.css           ← CSS compilado (480 KB)
    ├── custom.css         ← Customizações do projeto
    ├── ui_overrides.css   ← Acessibilidade
    └── animations.css     ← Animações extras
```

## 🔗 Integração Templates

Todos os templates herdam de `app/templates/base.html`:

```html
<!-- CSS compilado com TUDO -->
<link rel="stylesheet" href="{{ url_for('static', filename='css/base.css') }}">

<!-- CSS adicional -->
<link rel="stylesheet" href="{{ url_for('static', filename='css/custom.css') }}">
<link rel="stylesheet" href="{{ url_for('static', filename='css/ui_overrides.css') }}">
<link rel="stylesheet" href="{{ url_for('static', filename='css/animations.css') }}">
```

## ✅ O que está incluído no base.css

- ✅ Bootstrap 5 completo
- ✅ FontAwesome 7.1.0
- ✅ Tema ArchitectUI
- ✅ Layout responsivo
- ✅ Todos os componentes UI
- ✅ Animações e transições
- ✅ Utilities e helpers

## 🎨 Customizar Estilos

1. **Variáveis**: Edite `static/assets/themes/_layout-variables.scss`
2. **Novos estilos**: Adicione em `static/css/custom.css` (não precisa compilar)
3. **Componentes**: Crie arquivo em `static/assets/` e importe no `base.scss`
4. **Recompile**: `python scripts/build_css.py`

## 🔍 Verificar Compilação

```bash
# Ver arquivo gerado
Get-Item static/css/base.css | Select-Object Name, Length, LastWriteTime

# Testar sintaxe SCSS
npm run build:css

# Ver tamanho
Get-ChildItem static/css/*.css | Select-Object Name, @{Name='KB';Expression={[math]::Round($_.Length/1KB,1)}}
```

## ⚠️ Solução de Problemas

### CSS não atualiza no navegador
```bash
# 1. Recompile
python scripts/build_css.py

# 2. Limpe cache (Ctrl+Shift+R)
# 3. Reinicie Flask
```

### Erro "sass command not found"
```bash
npm install
```

### Warnings de deprecação
**Normal!** São avisos do Bootstrap 5. Não afetam funcionalidade.

## 📊 Status Atual

- ✅ 480.7 KB CSS compilado
- ✅ 39 templates integrados
- ✅ Todas dependências instaladas
- ✅ Sistema funcionando

## 📚 Documentação Completa

- `docs/SCSS_COMPILATION_GUIDE.md` - Guia detalhado
- `docs/SCSS_INTEGRATION_REPORT.md` - Relatório completo
- `scripts/build_css.py` - Script de compilação

---

**Última compilação**: 09/11/2025 22:33:50  
**Status**: ✅ Operacional
