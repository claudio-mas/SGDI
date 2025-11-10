# Como Criar o Favicon

## 🎨 Opções para Criar o Favicon

### Opção 1: Online (Mais Fácil)

Use um gerador online gratuito:

1. **Favicon.io** (https://favicon.io/)
   - Text to favicon: Digite "GED"
   - Image to favicon: Upload logo
   - Emoji to favicon: Escolha 📁 ou 📄

2. **RealFaviconGenerator** (https://realfavicongenerator.net/)
   - Upload logo/imagem
   - Gera múltiplos tamanhos

3. **Favicon Generator** (https://www.favicon-generator.org/)
   - Simples e rápido

### Opção 2: Photoshop/GIMP

1. Crie imagem 32x32 px ou 16x16 px
2. Salve como PNG
3. Use conversor online para .ico

### Opção 3: PowerShell (Temporário)

Criar favicon simples com iniciais:

```powershell
# Usar um ícone do sistema temporariamente
Copy-Item "C:\Windows\System32\imageres.dll" "static\favicon.ico"
```

## 📥 Instalação

1. Salve o arquivo como `favicon.ico`
2. Coloque em `static/favicon.ico`
3. Reinicie o servidor Flask
4. Limpe cache do navegador (Ctrl+Shift+R)

## ✅ Verificação

```powershell
# Verificar se o arquivo existe
Test-Path "static\favicon.ico"

# Ver detalhes
Get-Item "static\favicon.ico" | Select-Object Name, Length
```

## 🎯 Recomendações

- **Tamanho**: 16x16, 32x32 ou 48x48 pixels
- **Formato**: .ico (suporta múltiplas resoluções)
- **Design**: Simples e reconhecível
- **Cores**: Use cores do logo/tema

## 💡 Sugestões de Design para GED

- 📁 Pasta/folder
- 📄 Documento
- 🗂️ Arquivo
- Iniciais "GED"
- Logo da empresa

## 🔄 Depois de Adicionar

O navegador exibirá o ícone:
- ✅ Na aba do navegador
- ✅ Nos favoritos/bookmarks
- ✅ No histórico
- ✅ Em atalhos da área de trabalho

---

**Nota**: O template já está configurado para usar `static/favicon.ico`. Basta criar o arquivo!
