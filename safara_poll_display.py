"""Presentación compartida de personas confirmadas por instrumento."""

INSTRUMENTOS = (
    "Repenike",
    "Caja",
    "Surdo",
    "Surdo de contra",
    "Ganza (bailarinas)",
)


def agrupar_por_instrumento(confirmados, usuarios):
    """Devuelve todos los instrumentos y sus personas, sin duplicar votos."""
    grupos = {instrumento: [] for instrumento in INSTRUMENTOS}
    for nombre in dict.fromkeys(str(item) for item in confirmados):
        instrumento = str(usuarios.get(nombre, {}).get("instrumento") or "").strip()
        if instrumento not in grupos:
            instrumento = "Sin instrumento asignado"
        grupos.setdefault(instrumento, []).append(nombre)
    return {nombre: sorted(personas, key=str.casefold) for nombre, personas in grupos.items()}
