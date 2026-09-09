import customtkinter as ctk
from tkinter import filedialog, ttk
import threading
from src.services.excel_service import ExcelService
from src.services.browser_service import BrowserService

class AppWindow(ctk.CTk):
    def __init__(self, browser_service: BrowserService):
        super().__init__()
        self.browser_service = browser_service
        self.caminho_planilha = None

        self.title("Automação BlueMonitor Pro")
        self.geometry("600x700")
        self.minsize(550, 650)
        self.resizable(True, True)
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self._construir_interface()

    def escrever_log(self, mensagem: str):
        self.after(0, self._atualizar_log_gui, mensagem)

    def _atualizar_log_gui(self, mensagem: str):
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", mensagem + "\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")

    def _construir_interface(self):
        # Título
        self.titulo_label = ctk.CTkLabel(self, text="BlueMonitor Automator", font=ctk.CTkFont(size=24, weight="bold"))
        self.titulo_label.pack(pady=(20, 10))

        # Botão Navegador
        self.btn_navegador = ctk.CTkButton(
            self, text="1. Abrir Navegador p/ Automação", command=self._abrir_navegador_thread,
            font=ctk.CTkFont(size=14, weight="bold"), height=40
        )
        self.btn_navegador.pack(pady=10, padx=20, fill="x")

        # Tabs
        self.tabview = ctk.CTkTabview(self, width=560, height=250)
        self.tabview.pack(pady=10, padx=20, fill="x")
        self.tabview.add("Carregar de Planilha")
        self.tabview.add("Modo Manual")

        # Aba: Planilha
        self.btn_procurar = ctk.CTkButton(
            self.tabview.tab("Carregar de Planilha"), text="Procurar Planilha Excel", command=self._procurar_planilha
        )
        self.btn_procurar.pack(pady=40)
        self.lbl_planilha = ctk.CTkLabel(self.tabview.tab("Carregar de Planilha"), text="Nenhum arquivo selecionado")
        self.lbl_planilha.pack()

        # Aba: Manual
        self.entry_serial = ctk.CTkEntry(self.tabview.tab("Modo Manual"), placeholder_text="Número de Série", width=300)
        self.entry_serial.pack(pady=(20, 10))
        self.entry_status = ctk.CTkEntry(self.tabview.tab("Modo Manual"), placeholder_text="Status", width=300)
        self.entry_status.pack(pady=10)
        self.entry_obs = ctk.CTkEntry(self.tabview.tab("Modo Manual"), placeholder_text="Observação", width=300)
        self.entry_obs.pack(pady=10)

        # Controles (Iniciar, Pausar, Finalizar)
        self.frame_botoes = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_botoes.pack(pady=20, padx=20, fill="x")

        self.btn_iniciar = ctk.CTkButton(
            self.frame_botoes, text="▶ INICIAR", command=self._iniciar_thread,
            font=ctk.CTkFont(size=14, weight="bold"), height=40, fg_color="#28a745", hover_color="#218838"
        )
        self.btn_iniciar.pack(side="left", fill="x", expand=True, padx=5)

        self.btn_pausar = ctk.CTkButton(
            self.frame_botoes, text="⏸ PAUSAR", command=self._pausar,
            font=ctk.CTkFont(size=14, weight="bold"), height=40, fg_color="#ffc107", hover_color="#e0a800", text_color="black"
        )
        self.btn_pausar.pack(side="left", fill="x", expand=True, padx=5)

        self.btn_parar = ctk.CTkButton(
            self.frame_botoes, text="⏹ FINALIZAR", command=self._parar,
            font=ctk.CTkFont(size=14, weight="bold"), height=40, fg_color="#dc3545", hover_color="#c82333"
        )
        self.btn_parar.pack(side="left", fill="x", expand=True, padx=5)

        # Log
        self.lbl_status = ctk.CTkLabel(self, text="STATUS:", anchor="w")
        self.lbl_status.pack(padx=20, fill="x")
        self.log_textbox = ctk.CTkTextbox(self, height=250, activate_scrollbars=True)
        self.log_textbox.pack(padx=20, pady=(0, 20), fill="both", expand=True)
        self.log_textbox.configure(state="disabled")

        self.escrever_log("Sistema modular carregado. Aguardando inicialização.")

    def _abrir_navegador_thread(self):
        self.browser_service.iniciar_navegador()

    def _procurar_planilha(self):
        arquivo = filedialog.askopenfilename(title="Selecione a Planilha", filetypes=[("Planilhas", "*.xlsx *.xls *.csv")])
        if arquivo:
            self.caminho_planilha = arquivo
            self.lbl_planilha.configure(text=f"Selecionado: {arquivo.split('/')[-1]}", text_color="#28a745")
            self.escrever_log("Planilha carregada.")

    def _iniciar_thread(self):
        aba_atual = self.tabview.get()
        if not self.browser_service.is_aberto():
            self.escrever_log("ERRO: Abra o navegador primeiro.")
            return

        if aba_atual == "Carregar de Planilha":
            if not self.caminho_planilha:
                self.escrever_log("ERRO: Selecione a planilha.")
                return
            threading.Thread(target=self._ler_e_enviar_planilha, daemon=True).start()
        else:
            serial, status, obs = self.entry_serial.get(), self.entry_status.get(), self.entry_obs.get()
            if not serial:
                self.escrever_log("ERRO: O serial é obrigatório.")
                return
            self.browser_service.processar_manual(serial, status, obs)

    def _ler_e_enviar_planilha(self):
        try:
            self.escrever_log("Lendo e validando Excel...")
            registros = ExcelService.ler_planilha(self.caminho_planilha)
            self.browser_service.processar_planilha(registros)
        except Exception as e:
            self.escrever_log(f"Erro na planilha: {str(e)}")

    def _pausar(self):
        self.browser_service.pausar()

    def _parar(self):
        self.browser_service.parar()

    def mostrar_relatorio(self, resultados):
        # Esta função é chamada pela thread do browser, precisamos agendar na thread principal da GUI
        self.after(0, self._abrir_janela_relatorio, resultados)

    def _abrir_janela_relatorio(self, resultados):
        top = ctk.CTkToplevel(self)
        top.title("Relatório de Processamento")
        top.geometry("800x400")
        top.transient(self) # Fica na frente da janela principal
        top.grab_set() # Foca eventos apenas nela
        
        lbl = ctk.CTkLabel(top, text=f"Foram processados {len(resultados)} equipamentos.", font=("Arial", 16, "bold"))
        lbl.pack(pady=10)
        
        lbl_instrucao = ctk.CTkLabel(top, text="Você pode selecionar e copiar o texto de qualquer célula individualmente.", font=("Arial", 12), text_color="gray")
        lbl_instrucao.pack(pady=(0, 10))

        # Usando CTkScrollableFrame para criar uma tabela com células selecionáveis
        frame_scroll = ctk.CTkScrollableFrame(top, fg_color="#2b2b2b")
        frame_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Configuração das colunas (Título, Largura)
        headers = [
            ("Nº de Série", 120), 
            ("Hostname", 130), 
            ("Unidade", 200), 
            ("Foi Encontrado?", 120), 
            ("Status Final", 150), 
            ("Observação Final", 250)
        ]
        
        # Desenha o cabeçalho
        for col, (h, w) in enumerate(headers):
            lbl = ctk.CTkLabel(frame_scroll, text=h, font=("Arial", 12, "bold"), width=w, anchor="w")
            lbl.grid(row=0, column=col, padx=2, pady=5, sticky="w")
            
        # Desenha as linhas com CTkEntry para permitir seleção de texto
        for row, res in enumerate(resultados, start=1):
            encontrado_str = "Sim" if res["resultado"] == "sucesso" else ("Não (Erro)" if res["resultado"] == "erro" else "Não (Não Enc.)")
            
            valores = [
                res.get("serial", ""),
                res.get("hostname", ""),
                res.get("unidade_site", "-"),
                encontrado_str,
                res.get("status_site", "-"),
                res.get("obs_site", "-")
            ]
            
            for col, (val, (h, w)) in enumerate(zip(valores, headers)):
                entry = ctk.CTkEntry(frame_scroll, width=w, height=28, fg_color="#333333", border_width=1, text_color="white")
                entry.insert(0, str(val) if val else "")
                entry.configure(state="readonly")
                entry.grid(row=row, column=col, padx=2, pady=2, sticky="w")
