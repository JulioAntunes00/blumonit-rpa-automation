from src.gui.app_window import AppWindow
from src.services.browser_service import BrowserService

def main():
    # 1. Cria a instância do serviço (Core da automação)
    # 2. Como o serviço precisa escrever logs na UI, vamos usar um truque de binding
    # instanciando a UI com o serviço sem o logger, e injetando o logger depois,
    # ou usando uma casca.
    
    # Vamos injetar uma função vazia primeiro, e depois atualizar
    browser = BrowserService(logger_callback=lambda msg: None)
    
    # Instancia a interface injetando o serviço
    app = AppWindow(browser_service=browser)
    
    # Atualiza o callback de log do serviço para usar a função da janela
    browser.log = app.escrever_log
    browser.relatorio_callback = app.mostrar_relatorio
    
    # Inicia o loop da interface gráfica
    app.mainloop()

if __name__ == "__main__":
    main()
