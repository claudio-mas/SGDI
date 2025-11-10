#!/usr/bin/env python3
"""
Script para converter ícones Font Awesome para Bootstrap Icons em todos os templates HTML
"""
import os
import re
from pathlib import Path

# Mapeamento de ícones Font Awesome para Bootstrap Icons
ICON_MAP = {
    # Admin / Dashboard
    'fa-tachometer-alt': 'bi-speedometer2',
    'fa-users': 'bi-people-fill',
    'fa-file-alt': 'bi-file-earmark-text',
    'fa-hdd': 'bi-hdd',
    'fa-sign-in-alt': 'bi-box-arrow-in-right',
    'fa-chart-line': 'bi-graph-up',
    'fa-chart-pie': 'bi-pie-chart',
    'fa-history': 'bi-clock-history',
    'fa-user-shield': 'bi-shield-check',
    'fa-lock': 'bi-lock-fill',
    'fa-users-cog': 'bi-people',
    'fa-database': 'bi-database',
    
    # Workflows
    'fa-project-diagram': 'bi-diagram-3',
    'fa-plus': 'bi-plus-lg',
    'fa-edit': 'bi-pencil',
    'fa-pause': 'bi-pause-fill',
    'fa-play': 'bi-play-fill',
    'fa-info-circle': 'bi-info-circle',
    'fa-times': 'bi-x-lg',
    'fa-save': 'bi-save',
    'fa-trash': 'bi-trash',
    'fa-clock': 'bi-clock',
    'fa-check-circle': 'bi-check-circle-fill',
    'fa-times-circle': 'bi-x-circle-fill',
    'fa-layer-group': 'bi-layers',
    'fa-user': 'bi-person',
    'fa-calendar': 'bi-calendar',
    'fa-calendar-check': 'bi-calendar-check',
    'fa-download': 'bi-download',
    'fa-eye': 'bi-eye',
    'fa-check': 'bi-check-lg',
    'fa-exclamation-triangle': 'bi-exclamation-triangle',
    'fa-circle': 'bi-circle',
    
    # Errors
    'fa-home': 'bi-house-door',
    'fa-redo': 'bi-arrow-clockwise',
    'fa-search': 'bi-search',
    'fa-envelope': 'bi-envelope',
    
    # Documents
    'fa-file-pdf': 'bi-file-earmark-pdf',
    'fa-file-word': 'bi-file-earmark-word',
    'fa-file-excel': 'bi-file-earmark-excel',
    'fa-file-image': 'bi-file-earmark-image',
    'fa-file': 'bi-file-earmark',
    'fa-arrow-left': 'bi-arrow-left',
    'fa-align-left': 'bi-align-start',
    'fa-comment': 'bi-chat-left-text',
    'fa-undo': 'bi-arrow-counterclockwise',
    'fa-folder': 'bi-folder',
    'fa-tags': 'bi-tags',
    'fa-tag': 'bi-tag',
    'fa-share': 'bi-share',
    'fa-cog': 'bi-gear',
    'fa-upload': 'bi-upload',
    'fa-file-upload': 'bi-cloud-upload',
    'fa-spinner': 'bi-arrow-repeat',
    
    # Categories
    'fa-folder-tree': 'bi-folder2-open',
    'fa-folder-open': 'bi-folder2-open',
    'fa-sitemap': 'bi-diagram-2',
    
    # Tasks
    'fa-tasks': 'bi-list-check',
    
    # Search
    'fa-filter': 'bi-funnel',
    'fa-sort': 'bi-sort-down',
    
    # Common
    'fa-list': 'bi-list',
    'fa-bars': 'bi-list',
    'fa-ellipsis-v': 'bi-three-dots-vertical',
    'fa-bell': 'bi-bell',
    'fa-power-off': 'bi-power',
    'fa-cogs': 'bi-gear-fill',
}

def convert_icon_classes(content):
    """Converte as classes de ícones Font Awesome para Bootstrap Icons"""
    
    # Padrões de substituição
    replacements = []
    
    # 1. Substituir fas/far/fab por bi
    for fa_icon, bi_icon in ICON_MAP.items():
        # Padrão: class="fas fa-icon"
        pattern1 = rf'class="(fas|far|fab)\s+{re.escape(fa_icon)}'
        replacement1 = f'class="bi {bi_icon}'
        replacements.append((pattern1, replacement1))
        
        # Padrão: class="fas fa-icon fa-2x" (com modificadores de tamanho)
        pattern2 = rf'class="(fas|far|fab)\s+{re.escape(fa_icon)}\s+fa-(\w+)x'
        replacement2 = lambda m: f'class="bi {bi_icon} fs-{m.group(2)}'
        replacements.append((pattern2, replacement2))
        
        # Padrão dentro de templates Jinja: fa-icon
        pattern3 = rf'{re.escape(fa_icon)}(?=["\'\s])'
        replacement3 = bi_icon
        replacements.append((pattern3, replacement3))
    
    # Aplicar substituições
    for pattern, replacement in replacements:
        if callable(replacement):
            content = re.sub(pattern, replacement, content)
        else:
            content = re.sub(pattern, replacement, content)
    
    # Substituições adicionais para classes específicas
    content = re.sub(r'\bfas\s+', 'bi ', content)
    content = re.sub(r'\bfar\s+', 'bi ', content)
    content = re.sub(r'\bfab\s+', 'bi ', content)
    
    # Converter fa-2x, fa-3x, etc para fs-2, fs-3, etc
    content = re.sub(r'\bfa-2x\b', 'fs-2', content)
    content = re.sub(r'\bfa-3x\b', 'fs-3', content)
    content = re.sub(r'\bfa-4x\b', 'fs-4', content)
    content = re.sub(r'\bfa-5x\b', 'fs-5', content)
    content = re.sub(r'\bfa-lg\b', 'fs-5', content)
    
    # Converter fa-spin para spinner-border ou similar
    content = re.sub(r'\bfa-spin\b', 'spinner-border spinner-border-sm', content)
    
    return content

def process_file(file_path):
    """Processa um arquivo HTML e converte os ícones"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        content = convert_icon_classes(content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ Convertido: {file_path}")
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
    converted_count = 0
    
    for file_path in html_files:
        if process_file(file_path):
            converted_count += 1
    
    print(f"\n{'='*60}")
    print(f"Total de arquivos processados: {len(html_files)}")
    print(f"Arquivos convertidos: {converted_count}")
    print(f"Arquivos sem alterações: {len(html_files) - converted_count}")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
