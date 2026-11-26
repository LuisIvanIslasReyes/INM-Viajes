"""
Gentilicio para precargar la nacionalidad: "de nacionalidad china", no "de nacionalidad China".

En femenino y minúsculas, porque concuerda con "nacionalidad". Solo los países que más
llegan; si el código no está aquí, se precarga el nombre del país y el agente lo corrige.
"""

# (ISO-3, ISO-2, gentilicio)
_GENTILICIOS = [
    ('CHN', 'CN', 'china'), ('HKG', 'HK', 'china'), ('MAC', 'MO', 'china'), ('TWN', 'TW', 'taiwanesa'),
    ('RUS', 'RU', 'rusa'), ('UKR', 'UA', 'ucraniana'), ('BLR', 'BY', 'bielorrusa'),
    ('KAZ', 'KZ', 'kazaja'), ('KGZ', 'KG', 'kirguisa'), ('UZB', 'UZ', 'uzbeka'), ('TJK', 'TJ', 'tayika'),
    ('TKM', 'TM', 'turcomana'), ('GEO', 'GE', 'georgiana'), ('ARM', 'AM', 'armenia'), ('AZE', 'AZ', 'azerbaiyana'),
    ('MNG', 'MN', 'mongola'), ('IND', 'IN', 'india'), ('NPL', 'NP', 'nepalí'), ('PAK', 'PK', 'pakistaní'),
    ('BGD', 'BD', 'bangladesí'), ('LKA', 'LK', 'esrilanquesa'), ('AFG', 'AF', 'afgana'),
    ('IRN', 'IR', 'iraní'), ('IRQ', 'IQ', 'iraquí'), ('SYR', 'SY', 'siria'), ('TUR', 'TR', 'turca'),
    ('VNM', 'VN', 'vietnamita'), ('THA', 'TH', 'tailandesa'), ('PHL', 'PH', 'filipina'),
    ('IDN', 'ID', 'indonesia'), ('MYS', 'MY', 'malasia'), ('JPN', 'JP', 'japonesa'), ('KOR', 'KR', 'surcoreana'),
    ('EGY', 'EG', 'egipcia'), ('MAR', 'MA', 'marroquí'), ('NGA', 'NG', 'nigeriana'), ('GHA', 'GH', 'ghanesa'),
    ('CMR', 'CM', 'camerunesa'), ('SEN', 'SN', 'senegalesa'), ('ETH', 'ET', 'etíope'), ('ERI', 'ER', 'eritrea'),
    ('SOM', 'SO', 'somalí'), ('SDN', 'SD', 'sudanesa'), ('MRT', 'MR', 'mauritana'), ('AGO', 'AO', 'angoleña'),
    ('COG', 'CG', 'congoleña'), ('COD', 'CD', 'congoleña'), ('KEN', 'KE', 'keniana'),
    ('FRA', 'FR', 'francesa'), ('ESP', 'ES', 'española'), ('GBR', 'GB', 'británica'), ('DEU', 'DE', 'alemana'),
    ('ITA', 'IT', 'italiana'), ('USA', 'US', 'estadounidense'), ('CAN', 'CA', 'canadiense'),
    ('AUS', 'AU', 'australiana'), ('MEX', 'MX', 'mexicana'),
    ('GTM', 'GT', 'guatemalteca'), ('HND', 'HN', 'hondureña'), ('SLV', 'SV', 'salvadoreña'),
    ('NIC', 'NI', 'nicaragüense'), ('CRI', 'CR', 'costarricense'), ('PAN', 'PA', 'panameña'),
    ('CUB', 'CU', 'cubana'), ('HTI', 'HT', 'haitiana'), ('DOM', 'DO', 'dominicana'),
    ('COL', 'CO', 'colombiana'), ('VEN', 'VE', 'venezolana'), ('ECU', 'EC', 'ecuatoriana'), ('PER', 'PE', 'peruana'),
    ('BOL', 'BO', 'boliviana'), ('CHL', 'CL', 'chilena'), ('ARG', 'AR', 'argentina'), ('URY', 'UY', 'uruguaya'),
    ('PRY', 'PY', 'paraguaya'), ('BRA', 'BR', 'brasileña'),
]

GENTILICIO_POR_CODIGO = {}
for _iso3, _iso2, _gentilicio in _GENTILICIOS:
    GENTILICIO_POR_CODIGO[_iso3] = _gentilicio
    GENTILICIO_POR_CODIGO[_iso2] = _gentilicio


def gentilicio(codigo_pais):
    """'CHN' o 'CN' → 'china'; '' si el código no está en el catálogo."""
    return GENTILICIO_POR_CODIGO.get((codigo_pais or '').strip().upper(), '')
