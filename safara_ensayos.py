"""Reglas horarias y de quórum del ciclo semanal de ensayos de SAFARA."""

from __future__ import annotations

import datetime as dt
from typing import Any
from zoneinfo import ZoneInfo


ZONA_HORARIA = ZoneInfo("Europe/Madrid")
HORA_APERTURA_LUNES = dt.time(8, 0)
HORA_CIERRE_VIERNES = dt.time(19, 30)
HORA_ENSAYO_VISIBLE = "19:30h"
QUORUM_ENSAYO_MINIMO = 6

# El ciclo de pruebas comienza con Zizur la semana del 16/11/2026.
FECHA_REFERENCIA_ZIZUR = dt.date(2026, 11, 16)
UBICACION_ZIZUR = "Gaztetxe de Zizur"
UBICACION_BARA = "Baragazte (Barañain)"


def ahora_madrid(ahora: dt.datetime | None = None) -> dt.datetime:
    if ahora is None:
        return dt.datetime.now(ZONA_HORARIA)
    if ahora.tzinfo is None:
        return ahora.replace(tzinfo=ZONA_HORARIA)
    return ahora.astimezone(ZONA_HORARIA)


def lunes_del_ciclo(ahora: dt.datetime | None = None) -> dt.date:
    """Devuelve el lunes que gobierna la encuesta visible.

    De lunes 00:00 a 07:59 se mantiene cerrada la semana anterior. A las 08:00
    la aplicación pasa por reloj a una encuesta nueva sin borrar información.
    """
    local = ahora_madrid(ahora)
    lunes = local.date() - dt.timedelta(days=local.weekday())
    if local.weekday() == 0 and local.time() < HORA_APERTURA_LUNES:
        return lunes - dt.timedelta(days=7)
    return lunes


def ciclo_id_para_lunes(lunes: dt.date) -> str:
    anio, semana, _ = lunes.isocalendar()
    return f"{anio}-W{semana:02d}"


def ubicacion_para_lunes(lunes: dt.date) -> str:
    semanas = (lunes - FECHA_REFERENCIA_ZIZUR).days // 7
    return UBICACION_ZIZUR if semanas % 2 == 0 else UBICACION_BARA


def informacion_ensayo(ahora: dt.datetime | None = None) -> dict[str, Any]:
    local = ahora_madrid(ahora)
    lunes = lunes_del_ciclo(local)
    viernes = lunes + dt.timedelta(days=4)
    cierre = dt.datetime.combine(viernes, HORA_CIERRE_VIERNES, tzinfo=ZONA_HORARIA)
    apertura = dt.datetime.combine(lunes, HORA_APERTURA_LUNES, tzinfo=ZONA_HORARIA)
    return {
        "ciclo_id": ciclo_id_para_lunes(lunes),
        "lunes": lunes,
        "fecha": viernes,
        "hora": HORA_ENSAYO_VISIBLE,
        "hora_cierre": HORA_CIERRE_VIERNES,
        "ubicacion_nombre": ubicacion_para_lunes(lunes),
        "votacion_abierta": apertura <= local < cierre,
        "cierre": cierre,
    }


def ciclos_que_deben_cerrarse(ahora: dt.datetime | None = None) -> list[dict[str, Any]]:
    """Identifica como máximo la semana actual y la inmediatamente anterior."""
    local = ahora_madrid(ahora)
    actual = informacion_ensayo(local)
    candidatos: list[dt.date] = []
    if local >= actual["cierre"]:
        candidatos.append(actual["lunes"])
    anterior = actual["lunes"] - dt.timedelta(days=7)
    if anterior >= FECHA_REFERENCIA_ZIZUR:
        candidatos.append(anterior)

    resultado = []
    for lunes in candidatos:
        viernes = lunes + dt.timedelta(days=4)
        resultado.append(
            {
                "ciclo_id": ciclo_id_para_lunes(lunes),
                "fecha": viernes,
                "hora_cierre": HORA_CIERRE_VIERNES,
                "ubicacion": ubicacion_para_lunes(lunes),
            }
        )
    return resultado


def resultado_quorum(total: int, repenikes: int, cajas: int) -> str:
    return (
        "CONFIRMADO"
        if total >= QUORUM_ENSAYO_MINIMO and repenikes >= 1 and cajas >= 1
        else "NO_REALIZADO"
    )
