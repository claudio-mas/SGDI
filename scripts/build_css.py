#!/usr/bin/env python
"""
Script para compilar arquivos SCSS para CSS
Uso: python scripts/build_css.py [--watch]
"""
import subprocess
import sys
import os
from pathlib import Path


def main():
    """Compila os arquivos SCSS para CSS"""
    # Mudar para o diretório raiz do projeto
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Verificar se o argumento --watch foi passado
    watch_mode = '--watch' in sys.argv or '-w' in sys.argv
    
    if watch_mode:
        print("🔄 Iniciando compilação SCSS em modo watch...")
        print("   Pressione Ctrl+C para parar\n")
        try:
            subprocess.run('npm run watch:css', check=True, shell=True)
        except KeyboardInterrupt:
            print("\n✅ Watch mode interrompido")
            sys.exit(0)
    else:
        print("🔨 Compilando SCSS para CSS...")
        try:
            result = subprocess.run(
                'npm run build:css',
                capture_output=True,
                text=True,
                shell=True
            )
            
            # Verificar se houve erro real (não apenas warnings)
            if result.returncode != 0:
                # Filtrar apenas erros críticos, não warnings de deprecação
                if result.stderr:
                    lines = result.stderr.split('\n')
                    error_lines = [
                        line for line in lines
                        if 'Error:' in line or (
                            'error' in line.lower() and
                            'deprecation' not in line.lower()
                        )
                    ]
                    if error_lines:
                        print("❌ Erros encontrados:")
                        print('\n'.join(error_lines))
                        sys.exit(1)
            
            print("✅ CSS compilado com sucesso!")
            print("   Arquivo gerado: static/css/base.css")
            
            # Verificar se o arquivo foi criado
            css_file = project_root / 'static' / 'css' / 'base.css'
            if css_file.exists():
                size_kb = css_file.stat().st_size / 1024
                print(f"   Tamanho: {size_kb:.1f} KB")
            else:
                print("   ⚠️  Atenção: Arquivo CSS não foi encontrado!")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Erro ao compilar CSS: {e}")
            sys.exit(1)


if __name__ == '__main__':
    main()
