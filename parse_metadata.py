def find_category(name):
    jurisp_keys = ['AgR', 'Acórdão', 'Súmula', 'Orientação Jurisprudencial', 'Relação',
                   'RE', 'HC', 'AI', 'SS', 'CR', 'MI', 'RMS', 'MDI', 'Rcl', 'AO', 'AC',
                   'ADI', 'Ext', 'MS', 'PET', 'CC']

    leis_keys = ['Portaria', 'ATO', 'Ato', 'Constituição', 'Decreto', 'Lei', 'LEI',
                 'Deliberação', 'Emenda', 'Enunciado', 'Instrução', 'INSTRUÇÃO',
                 'Medida Provisória', 'Ordem de Serviço', 'Orientação Normativa',
                 'PORTARIA', 'Provimento', 'Recomendação', 'Regimento Interno',
                 'Resolução', 'RESOLUÇÃO']

    prop_keys = ['PL', 'PROJETO DE LEI', 'PROJETO DE DECRETO', 'MPV', 'PLV', 'PRC',
                 'PROPOSTA DE EMENDA', 'PEC']

    other_keys = []

    tipo = 'Outros'

    for key in jurisp_keys:
        if key in name:
            tipo = 'Jurisprudências'
            return tipo
    for key in leis_keys:
        if key in name:
            tipo = 'Leis'
            return tipo
    for key in prop_keys:
        if key in name:
            tipo = 'Proposições Legislativas'
            return tipo

    return tipo
