import bs4, re

class MetadataObject(object):
    def __init__(self, recte_list=[], adv_list=[], recdo_list=[]):
        self.recte_list = recte_list
        self.adv_list = adv_list
        self.recdo_list = recdo_list

def parse_file(path_to_file):
    filename = open(path_to_file, 'rb')
    soup = bs4.BeautifulSoup(filename, 'lxml')
    text = soup.text
    adv = re.compile('ADV.: .*')
    adv_list = adv.findall(text)
    recte = re.compile('RECTE.: .*')
    recte_list = recte.findall(text)
    recdo = re.compile('RECDO.: .*')
    recdo_list = re.findall(text)


    meta = MetadataObject(recte_list, adv_list, recdo_list)

    return meta

def find_category(name):
    jurisp_keys = ['AgR', 'Acórdão', 'Súmula', 'Orientação Jurisprudencial', 'Relação'
                   'RE', 'HC', 'AI', 'SS', 'CR', 'MI', 'RMS', 'MDI', 'Rcl', 'AO', 'AC',
                   'ADI', 'Ext', 'MS']

    leis_keys = ['Portaria', 'ATO', 'Ato', 'Constituição', 'Decreto', 'Lei', 'LEI',
                 'Deliberação', 'Emenda', 'Enunciado', 'Instrução', 'INSTRUÇÃO',
                 'Medida Provisória', 'Ordem de Serviço', 'Orientação Normativa',
                 'PORTARIA', 'Provimento', 'Recomendação', 'Regimento Interno',
                 'Resolução', 'RESOLUÇÃO']

    prop_keys = ['PL', 'PROJETO DE LEI', 'PROJETO DE DECRETO', 'MPV', 'PLV', 'PRC'
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
