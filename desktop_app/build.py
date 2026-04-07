#!/usr/bin/env python3
"""
Build script for creating the executable.
"""

import PyInstaller.__main__
import os
import sys
import shutil

def build():
    """Build the executable."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Clean previous builds
    for folder in ['build', 'dist']:
        path = os.path.join(base_dir, folder)
        if os.path.exists(path):
            shutil.rmtree(path)
    
    spec_path = os.path.join(base_dir, 'WS1AppIntelligence.spec')
    if os.path.exists(spec_path):
        os.remove(spec_path)
    
    # PyInstaller arguments
    args = [
        os.path.join(base_dir, 'main.py'),
        '--name=WS1AppIntelligence',
        '--onefile',
        '--windowed',
        f'--add-data={os.path.join(base_dir, "index.html")}{os.pathsep}.',
        '--noconfirm',
        '--clean',
    ]
    
    # Add icon if it exists
    icon_path = os.path.join(base_dir, 'icon.ico')
    if os.path.exists(icon_path):
        args.append(f'--icon={icon_path}')
    
    # Run PyInstaller
    PyInstaller.__main__.run(args)
    
    print('\n' + '='*50)
    print('Build complete!')
    print(f'Executable location: {os.path.join(base_dir, "dist", "WS1AppIntelligence.exe")}')
    print('='*50)


if __name__ == '__main__':
    build()
