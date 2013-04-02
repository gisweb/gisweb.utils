# - coding: utf-8 -
from datetime import datetime
from DateTime import DateTime

ADDITIONAL_VALUES = {
    'IRIDE_DOCID': 1,
    'IRIDE_PROGR': 1,
    'IRIDE_FONTE': 'GW',
    'IRIDE_DATINS': datetime.now().isoformat(),
    'IRIDE_UTEINS': 'what?',
    'IRIDE_DATAGG': 'what?',
    'IRIDE_UTEAGG': 'what?',
}


FIELDS_MAP = {
    'frm_gara_a': {
        '__tablename': 'POR_COMPSTRA',
        '__TipoDocumento': 'COMP',
        '__InCaricoA': 'COMPSTRANEW',
        '__Classifica': 'XVIII.02.03.',
        'gara_denominazione': 'COMP_DENGARA',
        'gara_data_gara': 'COMP_DATACOMP',
        'gara_comune_gara': 'COMP_LOCALITA',
        'gara_ora_ritrovo': 'COMP_ORE_RITROVO',
        'gara_luogo_ritrovo': 'COMP_LUO_RITROVO',
        'gara_luogo_partenza': 'COMP_LUO_PARTENZA',
        'gara_ora_partenza': 'COMP_ORE_PARTENZA',
        'gara_ora_arrivo': 'COMP_ORE_ARRIVO',
        'gara_luogo_arrivo': 'COMP_LUO_ARRIVO',
        'gara_itinerario': 'COMP_ITINERARIO',
        'gara_data_sopraluogo': 'COMP_DATA_SOPLUO',
        'gara_polizza_num': 'COMP_NUM_POLIZZA',
        'gara_polizza_data': 'COMP_DATA_POLIZZA',
        'gara_polizza_societa': 'COMP_SOC_ASSICURA',
    },

    'frm_occupazione_a': {
        '__tablename': 'POR_CONCSTRA_VOL',
        '__TipoDocumento': 'CONSC',
        '__InCaricoA': 'CONCESNEW',
        '__Classifica': '002.000.000',
        'ubicazione_localita': 'VOL_LOCALITA',
        'ubicazione_comune': 'VOL_COMUNE',
        'ubicazione_provincia': 'VOL_PROVINCIA',
        'ubicazione_indirizzo': 'VOL_INDIRIZZO',
        'ubicazione_civico': 'VOL_CIVICO',
        'ubicazione_interno': 'VOL_INTERNO',
        'ubicazione_cap': 'VOL_CAP',
        'ubicazione_foglio': 'VOL_FOGLIO',
        'ubicazione_mappale': 'VOL_MAPPALE',
        # '': 'VOL_POSLAT',
        # '': 'VOL_POSLONG',
        'autorizzazione_repertorio_numero': 'VOL_NUMREPERTORIO',
        'autorizzazione_repertorio_data': 'VOL_DATAREPERTORIO',
        'autorizzazione_intestazione_precedente': 'VOL_INTESTAZIONE',
        # '': 'VOL_LABDICHIARA',
        'voltura_motivazioni': 'VOL_MOTIVO',
        'voltura_modificazioni': 'VOL_MODIFICA',
        # '': 'VOL_NOTE',
    },

    'frm_occupazione_c': {
        '__tablename': 'POR_CONCSTRA_CPUB',
        '__TipoDocumento': 'CONSC',
        '__InCaricoA': 'CONCESNEW',
        '__Classifica': '002.000.000',
        'cartelli_comune': 'CPUB_COMUNE',
        'cartelli_tipo': 'CPUB_TIPO',
        'cartelli_illuminato': 'CPUB_ILLUMINA',
        'cartelli_pertinenza': 'CPUB_PERTINENZA',
        # '': 'CPUB_DALKM', # we mourn the loss of this field
        'cartelli_km': 'CPUB_ALKM',
        'cartelli_lato': 'CPUB_LATO',
        # '': 'CPUB_POSLAT',
        # '': 'CPUB_POSLONG', # I see dead fields
        'cartelli_base': 'CPUB_DIMBASE',
        'cartelli_altezza': 'CPUB_DIMALTEZZA',
        'cartelli_mq': 'CPUB_TOTMQ',
        'cartelli_testo': 'CPUB_DICITURA',
    },
}

FIELDS_MAP['frm_gara_b'] = FIELDS_MAP['frm_gara_a']
FIELDS_MAP['frm_gara_base'] = FIELDS_MAP['frm_gara_a']


def frm_gara_a_postprocessing(doc, data):
    data['COMP_CATEG'] = 'atletica o ciclistica'


def frm_gara_b_postprocessing(doc, data):
    data['COMP_CATEG'] = 'motoristica'


def get_tabledata_for(doc):
    """
    Returns a dictionary with IRIDE table names as keys
    and lists of dictionaries with key names from IRIDE definitions
    as values
    """
    plomino_table = doc.getForm().id
    data = dict(ADDITIONAL_VALUES)
    map = FIELDS_MAP[plomino_table]
    for key in doc.getItems():
        if key not in map:
            continue
        value = normalize_value(doc.getItem(key, None))
        data[map[key]] = value
    post_method = plomino_table + '_postprocessing'
    if post_method in globals():
        globals()[post_method](doc, data)
    iride_table = map['__tablename']
    return {
        iride_table: (data,)
    }


def normalize_value(value):
    if isinstance(value, DateTime):
        value = value.ISO8601()
    return value
