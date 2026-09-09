# ⚡ BlueMonitor Automation RPA

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Playwright](https://img.shields.io/badge/Playwright-Automation-green.svg)](https://playwright.dev/python/)
[![CustomTkinter](https://img.shields.io/badge/GUI-CustomTkinter-orange.svg)](https://github.com/TomSchimansky/CustomTkinter)
[![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)](LICENSE)

Aplicação Desktop RPA (Robotic Process Automation) desenvolvida em **Python**, **CustomTkinter** e **Playwright** para automação de consulta, conferência e atualização de status de inventário de equipamentos em lote a partir de planilhas Excel.

---

## 🎯 Funcionalidades

- 📁 **Importação de Planilha Excel**: Leitura automática de colunas de Número de Série e Status desejado (com suporte a seleção dinâmica de abas).
- 🔍 **Filtro Inteligente de Registros**: Ignora automaticamente códigos inválidos ou placeholders (ex: `S/N`, `N/A`, códigos com menos de 5 caracteres).
- 🌐 **Automação Web Resiliente**:
  - Integração com Playwright em modo persistente (mantém login e sessão do navegador salvos localmente).
  - Pesquisa ágil e precisa pelo Serial/Hostname.
  - Seleção exata e verificação de opções em listas de seleção (dropdowns), prevenindo falsos positivos de status (ex: diferenciação exata entre *Ativo* e *Inativo*).
  - Extração automatizada de Unidade e Hostname de cada equipamento.
- 📊 **Relatório Final Interativo**:
  - Grade visual detalhada ao concluir ou interromper o processo.
  - Exibição de: **Serial**, **Hostname**, **Encontrado (Sim/Não)**, **Novo Status**, **Unidade** e **Observação**.
  - Células com texto totalmente selecionável e copiável individualmente.
- 🛑 **Controle Total**: Opções para Iniciar, Parar e acompanhar os logs em tempo real na interface gráfica moderna e intuitiva (Dark Mode).

---

## 🛠️ Tecnologias Utilizadas

- **[Python](https://www.python.org/)**: Linguagem base.
- **[CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)**: Interface gráfica moderna com suporte a temas.
- **[Playwright for Python](https://playwright.dev/python/)**: Automação web de alta performance e persistência de sessão.
- **[Pandas](https://pandas.pydata.org/) & [OpenPyXL](https://openpyxl.readthedocs.io/)**: Processamento e manipulação de arquivos `.xlsx`.
- **[PyInstaller](https://pyinstaller.org/)**: Compilação para executável portátil (`.exe`).

---

## 📂 Estrutura do Projeto

```text
├── src/
│   ├── gui/
│   │   ├── app_window.py      # Interface gráfica principal
│   │   └── report_window.py   # Janela do relatório final interativo
│   ├── services/
│   │   ├── browser_service.py # Automação e integração web (Playwright)
│   │   └── excel_service.py   # Leitura e parsing de planilhas
│   └── utils/
├── build.py                   # Script para compilação do executável (.exe)
├── main.py                    # Ponto de entrada da aplicação
├── requirements.txt           # Dependências do projeto
└── README.md
```

---

## 🚀 Como Executar o Projeto

### Pré-requisitos
- Python 3.10 ou superior instalado.
- Navegador Chromium (instalado via Playwright).

### 1. Clonar o repositório
```bash
git clone <URL_DO_REPOSITORIO>
cd <NOME_DA_PASTA>
```

### 2. Criar e ativar o ambiente virtual (opcional, mas recomendado)
```bash
# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Instalar as dependências
```bash
pip install -r requirements.txt
playwright install chromium
```

### 4. Executar a aplicação
```bash
python main.py
```

---

## 📦 Gerando o Executável (.exe)

Para compilar a aplicação em um único arquivo `.exe`:
```bash
python build.py
```
O executável gerado estará disponível na pasta `dist/`.

---

## 🔒 Segurança e Privacidade

- Nenhum dado confidencial, credencial de acesso ou cookie de sessão é versionado no repositório.
- A pasta de dados de navegação (`browser_data/`) e arquivos de planilhas locais estão incluídos no `.gitignore`.

---

## 📄 Licença

Distribuído sob a licença MIT. Veja `LICENSE` para mais informações.
