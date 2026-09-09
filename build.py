import PyInstaller.__main__
import customtkinter
import os

# Pega o caminho de instalação do customtkinter para adicionar os assets (temas, fontes)
ctk_path = os.path.dirname(customtkinter.__file__)

PyInstaller.__main__.run([
    'main.py',
    '--name=Automação BlueMonitor',
    '--onedir',          # Cria uma pasta com os arquivos ao invés de um único arquivo gigante (abre mais rápido)
    '--windowed',        # Não mostra o console preto do terminal no fundo
    '--noconfirm',       # Sobrescreve a pasta dist/ se já existir
    f'--add-data={ctk_path};customtkinter/', # Adiciona os assets do CustomTkinter
])

print("\n--- BUILD CONCLUÍDO ---")
print("O executável está na pasta 'dist/Automação BlueMonitor/'")
