#!/usr/bin/env python3
"""
Script para corrigir conversões incompletas de ícones Font Awesome para Bootstrap Icons
"""
import re
from pathlib import Path

# Mapeamento adicional de ícones que foram parcialmente convertidos
ADDITIONAL_ICON_MAP = {
    'fa-pause': 'bi-pause-fill',
    'fa-play': 'bi-play-fill',
    'fa-clock': 'bi-clock',
    'fa-check-circle': 'bi-check-circle-fill',
    'fa-times-circle': 'bi-x-circle-fill',
    'fa-check': 'bi-check-lg',
    'fa-times': 'bi-x-lg',
    'fa-chart-bar': 'bi-bar-chart',
    'fa-bolt': 'bi-lightning-fill',
    'fa-shield-alt': 'bi-shield-check',
    'fa-palette': 'bi-palette',
    'fa-broom': 'bi-trash',
    'fa-key': 'bi-key',
    'fa-ban': 'bi-ban',
    'fa-chart-area': 'bi-graph-up',
    'fa-trophy': 'bi-trophy',
}


def fix_partial_conversions(content):
    """Corrige conversões parciais de ícones"""
    
    # 1. Corrigir padrão class="bi fa-icon" para class="bi bi-icon"
    for fa_icon, bi_icon in ADDITIONAL_ICON_MAP.items():
        # Padrão: class="bi fa-icon"
        pattern = rf'class="bi\s+{re.escape(fa_icon)}"'
        replacement = f'class="bi {bi_icon}"'
        content = re.sub(pattern, replacement, content)
        
        # Padrão em template strings JavaScript: class="bi fa-icon"
        pattern_js = rf'class="bi\s+{re.escape(fa_icon)}'
        replacement_js = f'class="bi {bi_icon}'
        content = re.sub(pattern_js, replacement_js, content)
        
        # Padrão em Jinja templates dinâmicos
        pattern_jinja = rf"\{{\{{\s*'?{re.escape(fa_icon)}'?\s*"
        replacement_jinja = f"{{{{ '{bi_icon}' "
        content = re.sub(pattern_jinja, replacement_jinja, content)
    
    return content


def process_file(file_path):
    """Processa um arquivo HTML e corrige os ícones"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        content = fix_partial_conversions(content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ Corrigido: {file_path}")
            return True
        else:
            print(f"- Sem alterações: {file_path}")
            return False
    except Exception as e:
        print(f"✗ Erro ao processar {file_path}: {e}")
        return False


def main():
    """Processa todos os arquivos HTML no diretório de templates"""
    templates_dir = Path(__file__).parent.parent / 'app' / 'templates'
    
    if not templates_dir.exists():
        print(f"Diretório de templates não encontrado: {templates_dir}")
        return
    
    print(f"Procurando arquivos HTML em: {templates_dir}\n")
    
    html_files = list(templates_dir.rglob('*.html'))
    corrected_count = 0
    
    for file_path in html_files:
        if process_file(file_path):
            corrected_count += 1
    
    print(f"\n{'='*60}")
    print(f"Total de arquivos processados: {len(html_files)}")
    print(f"Arquivos corrigidos: {corrected_count}")
    print(f"Arquivos sem alterações: {len(html_files) - corrected_count}")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
