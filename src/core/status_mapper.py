def mapear_status(status_planilha: str) -> str:
    """
    Recebe o status da planilha Excel e retorna o status exato esperado pelo site.
    """
    if not status_planilha or str(status_planilha).lower() == 'nan':
        return "Ativo"
        
    status = str(status_planilha).strip().lower()
    mapa = {
        "ativo": "Ativo",
        "chamado aberto": "Aguardando Garantia",
        "danificado": "Inservivel",
        "inservivel": "Inservivel",
        "em manutenção": "Aguardando Manutencao",
        "aguardando peça": "Aguardando Manutencao",
        "não localizado": "Não localizado"
    }
    return mapa.get(status, "Ativo") # Default para Ativo se não mapeado
