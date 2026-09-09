import pandas as pd
from typing import List, Dict

class ExcelService:
    @staticmethod
    def ler_planilha(caminho_arquivo: str) -> List[Dict[str, str]]:
        """
        Lê a planilha Excel, procura as colunas adequadas e retorna uma lista de dicionários
        com as chaves 'serial', 'status' e 'obs'.
        Levanta ValueError se as colunas essenciais não forem encontradas.
        """
        if caminho_arquivo.lower().endswith(".csv"):
            try:
                df = pd.read_csv(caminho_arquivo, sep=None, engine='python', encoding='utf-8')
            except UnicodeDecodeError:
                df = pd.read_csv(caminho_arquivo, sep=None, engine='python', encoding='latin1')
        else:
            df = pd.read_excel(caminho_arquivo)
        colunas_encontradas = df.columns.tolist()
        
        # Busca heurística por colunas
        col_serial = [c for c in colunas_encontradas if "série" in str(c).lower() or "serial" in str(c).lower()]
        col_status = [c for c in colunas_encontradas if "status" in str(c).lower()]
        col_obs = [c for c in colunas_encontradas if "descrição" in str(c).lower() or "descriçao" in str(c).lower() or "obs" in str(c).lower()]
        col_host = [c for c in colunas_encontradas if "host" in str(c).lower() or "nome" in str(c).lower() or "equipamento" in str(c).lower()]

        if not col_serial or not col_status or not col_obs:
            raise ValueError(f"Colunas não identificadas na planilha. Colunas disponíveis: {colunas_encontradas}")

        c_ser = col_serial[0]
        c_sta = col_status[0]
        c_obs = col_obs[0]
        c_host = col_host[0] if col_host else None
        
        registros = []
        for _, row in df.iterrows():
            serial = str(row[c_ser]).strip()
            status = str(row[c_sta]).strip()
            obs = str(row[c_obs]).strip()
            hostname = str(row[c_host]).strip() if c_host else ""
            
            if not serial or serial.lower() == 'nan':
                continue
                
            # Ignora seriais muito curtos como S/N, N/A, etc (tamanho <= 4)
            if len(serial) <= 4:
                continue
                
            if obs.lower() == 'nan':
                obs = ""
            if hostname.lower() == 'nan':
                hostname = ""
                
            registros.append({
                "serial": serial,
                "status": status,
                "obs": obs,
                "hostname": hostname
            })
            
        return registros
