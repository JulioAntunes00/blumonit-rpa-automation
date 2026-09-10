import queue
import threading
import time
from playwright.sync_api import sync_playwright
from src.core.status_mapper import mapear_status


class BrowserService:
    def __init__(self, logger_callback):
        self.log = logger_callback
        self.fila_comandos = queue.Queue()
        self._navegador_aberto = False
        self._thread_worker = None
        self.pausado = False
        self.parar_atual = False
        self.relatorio_callback = None

    def is_aberto(self) -> bool:
        return self._navegador_aberto

    def iniciar_navegador(self):
        if self._thread_worker and self._thread_worker.is_alive():
            self.log("Navegador já está aberto ou iniciando.")
            return

        self._thread_worker = threading.Thread(target=self._worker, daemon=True)
        self._thread_worker.start()

    def _worker(self):
        import asyncio
        import os
        asyncio.set_event_loop(asyncio.new_event_loop())

        # Cria pasta para dados do usuário para salvar senhas e cookies
        user_data_dir = os.path.join(os.getcwd(), "browser_data")
        os.makedirs(user_data_dir, exist_ok=True)

        try:
            with sync_playwright() as p:
                self.log("Iniciando motor do navegador (Chrome c/ Perfil Salvo)...")

                try:
                    context = p.chromium.launch_persistent_context(
                        user_data_dir=user_data_dir,
                        channel="chrome",
                        headless=False,
                        args=['--start-maximized'],
                        no_viewport=True
                    )
                except Exception:
                    self.log("Aviso: Chrome não encontrado, usando o Edge...")
                    context = p.chromium.launch_persistent_context(
                        user_data_dir=user_data_dir,
                        channel="msedge",
                        headless=False,
                        args=['--start-maximized'],
                        no_viewport=True
                    )

                page = context.pages[0] if context.pages else context.new_page()

                self.log("Acessando página de login...")
                page.goto("https://seducsp.bluemonitor.com.br/login/bm")
                self.log("Navegador aberto! Faça login, minimize e clique INICIAR.")
                self._navegador_aberto = True

                # Loop para manter a thread viva e processar comandos
                while self._navegador_aberto:
                    try:
                        comando = self.fila_comandos.get(timeout=1.0)
                        tipo = comando.get("tipo")

                        if tipo == "planilha":
                            registros = comando.get("registros")
                            self._processar_planilha_loop(page, registros)
                        elif tipo == "manual":
                            serial = comando.get("serial")
                            status = comando.get("status")
                            obs = comando.get("obs")
                            self._processar_equipamento_interno(page, serial, status, obs)
                        elif tipo == "encerrar":
                            self._navegador_aberto = False

                        self.fila_comandos.task_done()
                    except queue.Empty:
                        continue
                    except Exception as e:
                        self.log(f"Erro no processamento: {str(e)}")

                context.close()
        except Exception as e:
            self.log(f"Erro fatal no navegador: {str(e)}")
            self._navegador_aberto = False

    def processar_planilha(self, registros):
        self.fila_comandos.put({"tipo": "planilha", "registros": registros})

    def processar_manual(self, serial, status, obs):
        self.fila_comandos.put({"tipo": "manual", "serial": serial, "status": status, "obs": obs})

    def encerrar(self):
        self.fila_comandos.put({"tipo": "encerrar"})

    def pausar(self):
        self.pausado = not self.pausado
        estado = "PAUSADA" if self.pausado else "RETOMADA"
        self.log(f"--- Automação {estado} ---")

    def parar(self):
        self.parar_atual = True
        self.pausado = False
        self.log("--- Cancelando processamento atual... ---")

    def _processar_planilha_loop(self, page, registros):
        self.parar_atual = False
        total = len(registros)
        self.log(f"{total} registros encontrados. Iniciando...")
        
        resultados_finais = []

        for i, reg in enumerate(registros):
            if self.parar_atual:
                self.log("Processamento interrompido pelo usuário.")
                break

            while self.pausado and not self.parar_atual:
                time.sleep(0.5)

            if self.parar_atual:
                self.log("Processamento interrompido pelo usuário.")
                break

            self.log(f"[{i+1}/{total}] Processando {reg['serial']}...")
            res_dict = self._processar_equipamento_interno(
                page, reg['serial'], reg['status'], reg['obs']
            )
            
            resultados_finais.append({
                "serial": reg['serial'],
                "hostname": res_dict.get("hostname_site") or reg.get('hostname', ''),
                "unidade_site": res_dict.get("unidade_site", "-"),
                "resultado": res_dict.get("resultado", "erro"),
                "status_site": res_dict.get("status_site", "-"),
                "obs_site": res_dict.get("obs_site", "-")
            })

        if not self.parar_atual:
            self.log("Fim do processamento da planilha.")
            
        if self.relatorio_callback:
            self.relatorio_callback(resultados_finais)

    def _processar_equipamento_interno(self, page, serial: str, status_planilha: str, obs: str) -> dict:
        nome_equipamento_site = ""
        unidade_site = ""
        try:
            status_site = mapear_status(status_planilha)

            # ============================================================
            # 1. NAVEGAR PARA A LISTA DE DISPOSITIVOS
            # ============================================================
            page.goto("https://seducsp.bluemonitor.com.br/device/list", wait_until="domcontentloaded")
            page.wait_for_timeout(2000)

            # ============================================================
            # 2. PESQUISAR O SERIAL
            # ============================================================
            self.log(f"Pesquisando: {serial}...")

            # Encontra campos de texto visíveis
            todos_inputs = page.locator('input[type="text"]:visible, input[type="search"]:visible, input:not([type]):visible')
            qtd_inputs = todos_inputs.count()

            if qtd_inputs == 0:
                page.wait_for_timeout(3000)
                todos_inputs = page.locator('input[type="text"]:visible, input[type="search"]:visible, input:not([type]):visible')
                qtd_inputs = todos_inputs.count()

            if qtd_inputs == 0:
                self.log(f"Erro: Nenhum campo de busca na página para {serial}.")
                return {"resultado": "erro", "status_site": "-", "obs_site": "-", "hostname_site": nome_equipamento_site}

            campo_busca = todos_inputs.first
            campo_busca.click()
            page.wait_for_timeout(200)
            campo_busca.fill("")
            page.wait_for_timeout(200)
            campo_busca.fill(serial)
            page.wait_for_timeout(300)
            page.keyboard.press("Enter")
            page.wait_for_timeout(500)

            # Clica em botão de pesquisa se existir
            btn_pesquisa = page.locator('button:has-text("Pesquis"), button:has-text("Buscar"), button:has-text("Filtrar"), button[type="submit"]').first
            if btn_pesquisa.count() > 0 and btn_pesquisa.is_visible():
                btn_pesquisa.click()

            # Espera resultados
            page.wait_for_timeout(3000)

            # ============================================================
            # 3. VERIFICAR SE ENCONTROU O SERIAL
            # ============================================================
            encontrado = False
            linha_idx = 0
            for tentativa in range(4):
                linhas = page.locator('table tbody tr')
                qtd_linhas = linhas.count()

                if qtd_linhas > 0:
                    for li in range(min(qtd_linhas, 10)):
                        texto = linhas.nth(li).inner_text()
                        if serial.upper() in texto.upper():
                            encontrado = True
                            linha_idx = li
                            break

                    if encontrado:
                        break

                # Checa mensagem de não encontrado
                nao_enc = page.locator('text="Nenhum equipamento encontrado"')
                if nao_enc.count() > 0 and nao_enc.first.is_visible():
                    break

                page.wait_for_timeout(2000)

            if not encontrado:
                self.log(f"  Não encontrado no site. Pulando...")
                return {"resultado": "nao_encontrado", "status_site": "-", "obs_site": "-", "hostname_site": nome_equipamento_site}

            self.log(f"  Encontrado! Abrindo detalhes...")

            # ============================================================
            # 4. CLICAR NO EQUIPAMENTO (link azul na tabela)
            # ============================================================
            linha_alvo = page.locator('table tbody tr').nth(linha_idx)
            celula = linha_alvo.locator('td').first
            celula_unidade = linha_alvo.locator('td').nth(1)
            
            if celula.count() > 0:
                nome_equipamento_site = celula.inner_text().strip()
                
            if celula_unidade.count() > 0:
                unidade_site = celula_unidade.inner_text().strip()
                
            link = celula.locator('a')
            if link.count() > 0:
                link.first.click()
            else:
                celula.click()

            page.wait_for_timeout(2000)

            # ============================================================
            # 5. CLICAR EM "Alterar status" (O BOTÃOZINHO NA PÁGINA)
            # ============================================================
            # Pela screenshot: é um botão/link escrito "Alterar" ao lado do status
            btn_alterar = None
            for seletor in [
                'button:has-text("Alterar")',
                'a:has-text("Alterar")',
                'text="Alterar status"',
                'text="Alterar Status"',
                'text="Alterar"',
            ]:
                loc = page.locator(seletor).first
                if loc.count() > 0:
                    try:
                        loc.wait_for(state="visible", timeout=3000)
                        btn_alterar = loc
                        break
                    except:
                        continue

            if btn_alterar is None:
                page.wait_for_timeout(3000)
                btn_alterar = page.get_by_text("Alterar", exact=False).first
                try:
                    btn_alterar.wait_for(state="visible", timeout=5000)
                except:
                    self.log(f"  Erro: Botão 'Alterar' não encontrado.")
                    return {"resultado": "erro", "status_site": "-", "obs_site": "-", "hostname_site": nome_equipamento_site}

            btn_alterar.click()
            self.log(f"  Botão 'Alterar' clicado. Aguardando modal/janela...")

            # ============================================================
            # 6. DETECTAR O MODAL/DIALOG (flexível)
            # ============================================================
            # O modal pode ser:
            # - Um overlay na mesma página
            # - Um dialog HTML
            # - Pode ter texto diferente do esperado
            modal_encontrado = False

            # Estratégia A: Procura pelo texto do título (case-insensitive, parcial)
            for texto_modal in [
                "ALTERAR STATUS DO DISPOSITIVO",
                "Alterar Status do Dispositivo",
                "Alterar status do dispositivo",
                "ALTERAR STATUS",
                "Alterar Status",
                "Status do Dispositivo",
            ]:
                try:
                    page.get_by_text(texto_modal, exact=False).first.wait_for(state="visible", timeout=2000)
                    modal_encontrado = True
                    self.log(f"  Modal detectado: '{texto_modal}'")
                    break
                except:
                    continue

            # Estratégia B: Procura por qualquer dialog/modal genérico
            if not modal_encontrado:
                for seletor_modal in [
                    'div[role="dialog"]',
                    '.modal',
                    '.dialog',
                    '[class*="modal"]',
                    '[class*="dialog"]',
                    '[class*="overlay"]',
                    'form:has(select):has(textarea)',
                    'form:has(textarea)',
                ]:
                    try:
                        page.locator(seletor_modal).first.wait_for(state="visible", timeout=2000)
                        modal_encontrado = True
                        self.log(f"  Modal detectado via seletor: '{seletor_modal}'")
                        break
                    except:
                        continue

            if not modal_encontrado:
                # Última chance: espera mais e tira um screenshot do HTML
                page.wait_for_timeout(3000)
                html_visivel = page.evaluate('() => document.body.innerText.substring(0, 500)')
                self.log(f"  [DEBUG] Texto visível na página: {html_visivel[:200]}")
                self.log(f"  Erro: Modal não detectado para {serial}.")
                return {"resultado": "erro", "status_site": "-", "obs_site": "-", "hostname_site": nome_equipamento_site}

            page.wait_for_timeout(2000)  # Espera extra para o modal renderizar 100%

            # ============================================================
            # DEBUG: Captura o HTML REAL do modal
            # ============================================================
            modal_html = page.evaluate('''() => {
                // Procura o modal pela classe ou pelo conteúdo
                const modais = document.querySelectorAll('div[role="dialog"], .modal, [class*="modal"], [class*="dialog"]');
                if (modais.length > 0) {
                    return modais[modais.length - 1].innerHTML.substring(0, 1000);
                }
                // Fallback: captura tudo que contém o texto do título
                const all = document.querySelectorAll('*');
                for (let el of all) {
                    if (el.innerText && el.innerText.includes('ALTERAR STATUS') && el.querySelector('select, textarea, input')) {
                        return el.innerHTML.substring(0, 1000);
                    }
                }
                return 'MODAL_NAO_ENCONTRADO';
            }''')
            self.log(f"  [DEBUG] HTML do modal: {modal_html[:300]}")

            # ============================================================
            # 7+8. STATUS + OBSERVAÇÃO (VIA PLAYWRIGHT NATIVO)
            # ============================================================
            try:
                # ----- STATUS (via Tab + Home + Setas, igual o usuário faz manualmente) -----
                status_sucesso = False
                
                # Mapa de índices: quantas setas pra BAIXO a partir do topo ("Aguardando Garantia")
                MAPA_INDICES = {
                    "Aguardando Garantia": 0,
                    "Ativo": 1,
                    "Roubado/Furtado": 2,
                    "Inservivel": 3,
                    "Desativado": 4,
                    "Desconhecido": 5,
                    "Aguardando Manutencao": 6,
                    "Não localizado": 7,
                }
                
                setas_para_baixo = MAPA_INDICES.get(status_site)
                
                if setas_para_baixo is not None:
                    # 1. Tab para focar no select do status
                    page.keyboard.press("Tab")
                    page.wait_for_timeout(500)
                    
                    # 2. Tecla Home para voltar ao topo ("Aguardando Garantia")
                    page.keyboard.press("Home")
                    page.wait_for_timeout(300)
                    
                    # 3. Apertar ArrowDown a quantidade de vezes necessária
                    if setas_para_baixo > 0:
                        self.log(f"  Navegando: {setas_para_baixo}x ArrowDown para '{status_site}'")
                        for _ in range(setas_para_baixo):
                            page.keyboard.press("ArrowDown")
                            page.wait_for_timeout(100)
                    else:
                        self.log(f"  Status é 'Aguardando Garantia', já selecionado via tecla Home.")
                    
                    # 4. Tab para confirmar e ir para o campo de observação
                    page.wait_for_timeout(300)
                    page.keyboard.press("Tab")
                    
                    self.log(f"  ✔ Status selecionado via teclado: {status_site}")
                    status_sucesso = True
                else:
                    self.log(f"  AVISO: Status '{status_site}' não está no mapa de opções conhecidas.")

                # ----- OBSERVAÇÃO -----
                obs_limpa = str(obs).strip()
                if obs_limpa.lower() in ["nan", "none"]:
                    obs_limpa = ""

                textarea_elem = page.locator('textarea').first
                if textarea_elem.count() > 0:
                    # Limpa e preenche garantindo que o React detecte
                    textarea_elem.click(force=True)
                    textarea_elem.fill("")
                    page.wait_for_timeout(100)
                    textarea_elem.fill(obs_limpa)
                    self.log(f"  Observação preenchida: {obs_limpa[:30]}...")
                else:
                    self.log("  AVISO: Campo de Observação (textarea) não encontrado.")

            except Exception as e:
                self.log(f"  Erro ao preencher status/obs: {str(e)[:120]}")

            page.wait_for_timeout(500)

            # ============================================================
            # SALVAR
            # ============================================================
            try:
                # Tenta clicar no botão Salvar via Playwright
                btn_salvar = page.locator('button:has-text("Salvar")').first
                if btn_salvar.count() > 0:
                    btn_salvar.click()
                    self.log(f"  Salvar clicado via Playwright!")
                else:
                    # Fallback: clica via JavaScript
                    page.evaluate('''() => {
                        const botoes = document.querySelectorAll('button');
                        for (let btn of botoes) {
                            if (btn.innerText.trim().toLowerCase().includes('salvar')) {
                                btn.click();
                                return true;
                            }
                        }
                        return false;
                    }''')
                    self.log(f"  Salvar clicado via JavaScript!")

                page.wait_for_timeout(3000)
            except Exception as e:
                self.log(f"  Aviso: Erro ao salvar: {str(e)[:80]}")

            self.log(f"OK: {serial} -> {status_site}")
            return {"resultado": "sucesso", "status_site": status_site, "obs_site": obs, "hostname_site": nome_equipamento_site, "unidade_site": unidade_site}

        except Exception as e:
            self.log(f"ERRO em {serial}: {str(e)[:120]}")
            return {"resultado": "erro", "status_site": "-", "obs_site": "-", "hostname_site": nome_equipamento_site, "unidade_site": unidade_site}
