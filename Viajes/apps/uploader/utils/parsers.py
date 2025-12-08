"""
Utilidades para parsear y convertir datos
"""
import pandas as pd

# ============================================
# DICCIONARIO DE CÓDIGOS ISO DE PAÍSES
# ============================================
PAISES_ISO = {
    'AFG': 'Afganistán', 'ALB': 'Albania', 'DEU': 'Alemania', 'AND': 'Andorra', 'AGO': 'Angola',
    'ATG': 'Antigua y Barbuda', 'SAU': 'Arabia Saudita', 'DZA': 'Argelia', 'ARG': 'Argentina', 
    'ARM': 'Armenia', 'AUS': 'Australia', 'AUT': 'Austria', 'AZE': 'Azerbaiyán', 'BHS': 'Bahamas',
    'BGD': 'Bangladés', 'BRB': 'Barbados', 'BHR': 'Baréin', 'BEL': 'Bélgica', 'BLZ': 'Belice',
    'BEN': 'Benín', 'BLR': 'Bielorrusia', 'MMR': 'Birmania', 'BOL': 'Bolivia', 'BIH': 'Bosnia y Herzegovina',
    'BWA': 'Botsuana', 'BRA': 'Brasil', 'BRN': 'Brunéi', 'BGR': 'Bulgaria', 'BFA': 'Burkina Faso',
    'BDI': 'Burundi', 'BTN': 'Bután', 'CPV': 'Cabo Verde', 'KHM': 'Camboya', 'CMR': 'Camerún',
    'CAN': 'Canadá', 'QAT': 'Catar', 'TCD': 'Chad', 'CHL': 'Chile', 'CHN': 'China',
    'CYP': 'Chipre', 'VAT': 'Ciudad del Vaticano', 'COL': 'Colombia', 'COM': 'Comoras', 
    'PRK': 'Corea del Norte', 'KOR': 'Corea del Sur', 'CIV': 'Costa de Marfil', 'CRI': 'Costa Rica',
    'HRV': 'Croacia', 'CUB': 'Cuba', 'DNK': 'Dinamarca', 'DMA': 'Dominica', 'ECU': 'Ecuador',
    'EGY': 'Egipto', 'SLV': 'El Salvador', 'ARE': 'Emiratos Árabes Unidos', 'ERI': 'Eritrea',
    'SVK': 'Eslovaquia', 'SVN': 'Eslovenia', 'ESP': 'España', 'USA': 'Estados Unidos',
    'EST': 'Estonia', 'ETH': 'Etiopía', 'PHL': 'Filipinas', 'FIN': 'Finlandia', 'FJI': 'Fiyi',
    'FRA': 'Francia', 'GAB': 'Gabón', 'GMB': 'Gambia', 'GEO': 'Georgia', 'GHA': 'Ghana',
    'GRD': 'Granada', 'GRC': 'Grecia', 'GTM': 'Guatemala', 'GNB': 'Guinea-Bisáu', 'GIN': 'Guinea',
    'GNQ': 'Guinea Ecuatorial', 'GUY': 'Guyana', 'HTI': 'Haití', 'HND': 'Honduras', 'HUN': 'Hungría',
    'IND': 'India', 'IDN': 'Indonesia', 'IRQ': 'Irak', 'IRN': 'Irán', 'IRL': 'Irlanda',
    'ISL': 'Islandia', 'MHL': 'Islas Marshall', 'SLB': 'Islas Salomón', 'ISR': 'Israel',
    'ITA': 'Italia', 'JAM': 'Jamaica', 'JPN': 'Japón', 'JOR': 'Jordania', 'KAZ': 'Kazajistán',
    'KEN': 'Kenia', 'KGZ': 'Kirguistán', 'KIR': 'Kiribati', 'KWT': 'Kuwait', 'LAO': 'Laos',
    'LSO': 'Lesoto', 'LVA': 'Letonia', 'LBN': 'Líbano', 'LBR': 'Liberia', 'LBY': 'Libia',
    'LIE': 'Liechtenstein', 'LTU': 'Lituania', 'LUX': 'Luxemburgo', 'MKD': 'Macedonia del Norte',
    'MDG': 'Madagascar', 'MYS': 'Malasia', 'MWI': 'Malaui', 'MDV': 'Maldivas', 'MLI': 'Mali',
    'MLT': 'Malta', 'MAR': 'Marruecos', 'MUS': 'Mauricio', 'MRT': 'Mauritania', 'MEX': 'México',
    'FSM': 'Micronesia', 'MDA': 'Moldavia', 'MCO': 'Mónaco', 'MNG': 'Mongolia', 'MNE': 'Montenegro',
    'MOZ': 'Mozambique', 'NAM': 'Namibia', 'NRU': 'Nauru', 'NPL': 'Nepal', 'NIC': 'Nicaragua',
    'NER': 'Níger', 'NGA': 'Nigeria', 'NOR': 'Noruega', 'NZL': 'Nueva Zelanda', 'OMN': 'Omán',
    'NLD': 'Países Bajos', 'PAK': 'Pakistán', 'PLW': 'Palaos', 'PSE': 'Palestina', 'PAN': 'Panamá',
    'PNG': 'Papúa Nueva Guinea', 'PRY': 'Paraguay', 'PER': 'Perú', 'POL': 'Polonia', 'PRT': 'Portugal',
    'GBR': 'Reino Unido', 'CAF': 'República Centroafricana', 'CZE': 'República Checa',
    'COG': 'República del Congo', 'COD': 'República Democrática del Congo', 'DOM': 'República Dominicana',
    'RWA': 'Ruanda', 'ROU': 'Rumania', 'RUS': 'Rusia', 'WSM': 'Samoa', 'KNA': 'San Cristóbal y Nieves',
    'SMR': 'San Marino', 'VCT': 'San Vicente y las Granadinas', 'LCA': 'Santa Lucía',
    'STP': 'Santo Tomé y Príncipe', 'SEN': 'Senegal', 'SRB': 'Serbia', 'SYC': 'Seychelles',
    'SLE': 'Sierra Leona', 'SGP': 'Singapur', 'SYR': 'Siria', 'SOM': 'Somalia', 'LKA': 'Sri Lanka',
    'SWZ': 'Esuatini', 'ZAF': 'Sudáfrica', 'SDN': 'Sudán', 'SSD': 'Sudán del Sur', 'SWE': 'Suecia',
    'CHE': 'Suiza', 'SUR': 'Surinam', 'THA': 'Tailandia', 'TZA': 'Tanzania', 'TJK': 'Tayikistán',
    'TLS': 'Timor Oriental', 'TGO': 'Togo', 'TON': 'Tonga', 'TTO': 'Trinidad y Tobago', 'TUN': 'Túnez',
    'TKM': 'Turkmenistán', 'TUR': 'Turquía', 'TUV': 'Tuvalu', 'UKR': 'Ucrania', 'UGA': 'Uganda',
    'URY': 'Uruguay', 'UZB': 'Uzbekistán', 'VUT': 'Vanuatu', 'VEN': 'Venezuela', 'VNM': 'Vietnam',
    'YEM': 'Yemen', 'DJI': 'Yibuti', 'ZMB': 'Zambia', 'ZWE': 'Zimbabue',
    # Códigos adicionales de 2 letras comunes
    'CN': 'China', 'US': 'Estados Unidos', 'MX': 'México', 'BR': 'Brasil', 'AR': 'Argentina',
    'CA': 'Canadá', 'JP': 'Japón', 'KR': 'Corea del Sur', 'IN': 'India', 'GB': 'Reino Unido',
    'FR': 'Francia', 'DE': 'Alemania', 'IT': 'Italia', 'ES': 'España', 'RU': 'Rusia',
    'AU': 'Australia', 'NZ': 'Nueva Zelanda', 'TH': 'Tailandia', 'VN': 'Vietnam', 'PH': 'Filipinas',
}


def obtener_nacionalidad(codigo_pais):
    """
    Convierte un código ISO de país a su nombre completo en español.
    Soporta códigos de 2 y 3 letras (ISO 3166-1 alpha-2 y alpha-3).
    
    Args:
        codigo_pais: Código ISO del país (ej: 'CHN', 'CN', 'MEX', 'MX')
        
    Returns:
        Nombre del país en español o el código original si no se encuentra
    """
    if not codigo_pais or pd.isna(codigo_pais):
        return 'N/A'
    
    codigo = str(codigo_pais).strip().upper()
    return PAISES_ISO.get(codigo, codigo)