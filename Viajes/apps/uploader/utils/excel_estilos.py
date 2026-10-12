"""
Paleta compartida de los reportes en Excel (openpyxl).

Colores tomados tal cual del CSS del reporte (inadmitidos_report.css),
aplanando los rgba() sobre fondo blanco. Prefijo 'FF' = alfa opaco.
"""

MAROON       = 'FF6B1D1D'  # row-vuelo / row-dias
DARK_RED     = 'FF4D060A'  # total-sr / encabezado de sección
ROSA_TITULO  = 'FFFFEEED'  # row-title / row-total-inad
ROSA_FECHAS  = 'FFFFF7F6'  # row-fechas
VERDE_INTERN = 'FFE6EDE9'  # row-total-intern (el verde va aquí, en el Total)
DATA_BG      = 'FFF9F9FC'  # row-data / row-intern-nac
PAX_BG       = 'FFE2E2E5'  # row-total-pax
