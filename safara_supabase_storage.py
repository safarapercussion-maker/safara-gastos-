"""Almacenamiento transaccional de SAFARA GASTOS en Supabase.

Este módulo se usa solo desde el servidor Streamlit. La credencial de base de
datos permanece en Streamlit Secrets y nunca se escribe en Git.
"""

from __future__ import annotations

import datetime as dt
import time
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

from safara_security import verify_invitation_code


class SupabaseStorageConfigurationError(RuntimeError):
    """La persistencia de Supabase se activó sin una configuración válida."""


class SupabaseStorageOperationError(RuntimeError):
    """Una operación transaccional no se pudo completar."""


class SupabaseStorageAuthenticationError(SupabaseStorageOperationError):
    """La contraseña configurada no permite abrir la conexión privada."""


_SECRET_SECTIONS = ("safara_supabase_storage", "safara_google_storage")


def _section_values(secrets: Any, section_name: str) -> dict[str, Any]:
    """Lee una sección TOML sin depender de la implementación de Streamlit."""
    try:
        section = secrets.get(section_name, {})
        return section.to_dict() if hasattr(section, "to_dict") else dict(section)
    except (AttributeError, TypeError, ValueError):
        return {}


def _configured_database_url(secrets: Any) -> str:
    """Acepta la configuración histórica y la sección específica nueva."""
    candidates: list[Any] = []
    try:
        candidates.append(secrets.get("database_url", ""))
    except (AttributeError, TypeError):
        pass
    for section_name in _SECRET_SECTIONS:
        candidates.append(_section_values(secrets, section_name).get("database_url", ""))

    for candidate in candidates:
        value = str(candidate or "").strip()
        if value.startswith(("postgresql://", "postgres://", "postgresql+psycopg://")):
            return value
    return ""


def _configured_enablement(secrets: Any) -> list[Any]:
    values: list[Any] = []
    try:
        values.append(secrets.get("enable_supabase_storage", None))
    except (AttributeError, TypeError):
        pass
    for section_name in _SECRET_SECTIONS:
        values.append(
            _section_values(secrets, section_name).get("enable_supabase_storage", None)
        )
    return values


def is_enabled(secrets: Any) -> bool:
    for value in _configured_enablement(secrets):
        if value is True or str(value).strip().lower() in {"true", "1", "si", "sí"}:
            return True
    # Si la URL privada está presente, se trata de una configuración deliberada;
    # evita que una cabecera TOML movida deje los datos críticos sin persistencia.
    return bool(_configured_database_url(secrets))


@dataclass(frozen=True)
class SupabaseStorageConfig:
    database_url: str

    @classmethod
    def from_secrets(cls, secrets: Any) -> "SupabaseStorageConfig":
        url = _configured_database_url(secrets)
        if not url:
            raise SupabaseStorageConfigurationError(
                "La conexión privada de Supabase no tiene un formato válido."
            )
        # El formato +psycopg es habitual en SQLAlchemy; psycopg usa postgresql://.
        return cls(url.replace("postgresql+psycopg://", "postgresql://", 1))


class SupabaseSafaraStorage:
    """Acceso transaccional a la estructura privada ``safara``.

    La aplicación no expone las tablas mediante API pública: toda operación se
    realiza en el servidor con consultas parametrizadas y transacciones cortas.
    """

    def __init__(self, config: SupabaseStorageConfig):
        try:
            import psycopg  # noqa: F401
            from psycopg.rows import dict_row  # noqa: F401
            from psycopg_pool import ConnectionPool  # noqa: F401
        except ImportError as error:
            raise SupabaseStorageConfigurationError(
                "Falta la dependencia segura de PostgreSQL."
            ) from error
        self._database_url = config.database_url
        self._connection_failure: SupabaseStorageOperationError | None = None
        from psycopg.rows import dict_row
        from psycopg_pool import ConnectionPool

        self._pool = ConnectionPool(
            conninfo=self._database_url,
            # Streamlit mantiene procesos de corta duración. Una conexión
            # caliente evita que cada primer acceso pague el coste completo de
            # negociar TLS con la base; el límite reducido protege el plan de
            # pruebas cuando coinciden varias sesiones.
            min_size=1,
            max_size=3,
            max_waiting=12,
            timeout=4,
            max_idle=60,
            max_lifetime=900,
            kwargs={
                "row_factory": dict_row,
                "sslmode": "require",
                "options": "-c search_path=safara,public",
                # La aplicación usa el pool compartido de Supabase. Desactivar
                # sentencias preparadas evita incompatibilidades si el secreto
                # apunta al modo transaccional del pooler.
                "prepare_threshold": None,
            },
        )

    def _connection(self):
        """Obtiene una conexión breve de un grupo compartido por la aplicación."""
        return self._pool.connection()

    @staticmethod
    def _as_text(value: Any) -> str:
        return "" if value is None else str(value)

    @staticmethod
    def _as_date(value: Any) -> dt.date:
        if isinstance(value, dt.date):
            return value
        raw = str(value)
        try:
            return dt.date.fromisoformat(raw)
        except ValueError:
            return dt.datetime.strptime(raw, "%d/%m/%Y").date()

    @staticmethod
    def _nombre_ticket(referencia: str, fichero_origen: str) -> str:
        """Crea un nombre fiscal claro sin incorporar datos personales."""
        extension = Path(str(fichero_origen)).suffix.lower()
        if extension not in {".png", ".jpg", ".jpeg", ".pdf"}:
            extension = ".bin"
        return f"{referencia}_ticket{extension}"

    def _siguiente_referencia_gasto(self, cursor, fecha: Any) -> str:
        ejercicio = self._as_date(fecha).year
        cursor.execute(
            "select pg_advisory_xact_lock(hashtext(%s))",
            (f"safara-gastos-referencia-{ejercicio}",),
        )
        cursor.execute(
            """select coalesce(max(split_part(referencia_anual, '-', 2)::integer), 0) + 1 as siguiente
               from safara.gastos where referencia_anual like %s""",
            (f"{ejercicio}-%",),
        )
        siguiente = int((cursor.fetchone() or {"siguiente": 1})["siguiente"] or 1)
        return f"{ejercicio}-{siguiente:03d}"

    def _run(self, callback):
        if self._connection_failure is not None:
            raise self._connection_failure
        last_error = None
        # Un único reintento breve absorbe el despertar del pooler o un corte
        # transitorio sin convertir cada clic en una espera larga.
        for attempt in range(2):
            try:
                with self._connection() as connection:
                    with connection.cursor() as cursor:
                        return callback(cursor)
            except SupabaseStorageOperationError:
                raise
            except Exception as error:
                last_error = error
                if "password authentication failed" in str(error).lower():
                    failure = SupabaseStorageAuthenticationError(
                        "La contraseña de la conexión privada de Supabase no coincide."
                    )
                    # Una contraseña errónea no se corrige sola; se evita abrir
                    # una conexión por cada interacción hasta actualizar Secrets.
                    self._connection_failure = failure
                    raise failure from error
                if attempt == 0:
                    time.sleep(0.15)

        # Un corte temporal de red no debe dejar toda la app marcada como
        # fallida hasta el siguiente despliegue. La siguiente acción podrá
        # recuperar la conexión de forma normal.
        raise SupabaseStorageOperationError(
            "No se ha podido guardar la información en Supabase."
        ) from last_error

    def verificar_conexion_segura(self) -> bool:
        """Comprueba la conexión privada antes de habilitar operaciones críticas."""
        def callback(cursor):
            cursor.execute("select 1 as listo")
            row = cursor.fetchone()
            return bool(row and row.get("listo") == 1)

        return bool(self._run(callback))

    def actualizar_rol_usuario(self, objetivo: str, nuevo_rol: str, actor: str) -> bool:
        """Concede o retira administración con controles dentro de la transacción."""
        if nuevo_rol not in {"admin", "usuario"}:
            raise SupabaseStorageOperationError("El permiso solicitado no es válido.")

        def callback(cursor):
            cursor.execute("select pg_advisory_xact_lock(hashtext('safara-role-management'))")
            cursor.execute(
                "select id, rol from safara.usuarios where lower(btrim(nombre))=lower(btrim(%s)) and activo",
                (actor,),
            )
            actor_record = cursor.fetchone()
            if not actor_record or actor_record["rol"] != "admin":
                raise SupabaseStorageOperationError("Solo una persona administradora puede gestionar permisos.")

            cursor.execute(
                "select id, rol, nombre from safara.usuarios where lower(btrim(nombre))=lower(btrim(%s)) and activo for update",
                (objetivo,),
            )
            target = cursor.fetchone()
            if not target:
                raise SupabaseStorageOperationError("La persona seleccionada ya no está disponible.")
            if target["id"] == actor_record["id"]:
                raise SupabaseStorageOperationError("No puedes modificar tu propio permiso de administración.")
            if target["rol"] == nuevo_rol:
                return False

            if target["rol"] == "admin" and nuevo_rol == "usuario":
                cursor.execute("select count(*) as total from safara.usuarios where activo and rol='admin'")
                if cursor.fetchone()["total"] <= 1:
                    raise SupabaseStorageOperationError("No se puede retirar a la última persona administradora.")

            cursor.execute("update safara.usuarios set rol=%s where id=%s", (nuevo_rol, target["id"]))
            evento = "permiso_admin_concedido" if nuevo_rol == "admin" else "permiso_admin_retirado"
            cursor.execute(
                "insert into safara.auditoria (evento, usuario_id, detalle) values (%s, %s, %s)",
                (evento, target["id"], f"Gestionado por: {actor}"),
            )
            return True

        return bool(self._run(callback))

    def obtener_token_google_drive_cifrado(self) -> str:
        """Devuelve el permiso cifrado de Drive, si una persona administradora lo autorizó."""
        def callback(cursor):
            cursor.execute(
                "select token_cifrado from safara.google_drive_oauth where id = 1"
            )
            row = cursor.fetchone()
            return str(row["token_cifrado"]) if row else ""

        return str(self._run(callback) or "")

    def obtener_autorizacion_google_drive(self) -> dict[str, str]:
        """Devuelve solo el permiso cifrado y la carpeta creada por la aplicación."""
        def callback(cursor):
            cursor.execute(
                "select token_cifrado, carpeta_id from safara.google_drive_oauth where id = 1"
            )
            row = cursor.fetchone()
            if not row:
                return {"token_cifrado": "", "carpeta_id": ""}
            return {
                "token_cifrado": str(row.get("token_cifrado") or ""),
                "carpeta_id": str(row.get("carpeta_id") or ""),
            }

        return self._run(callback)

    def guardar_token_google_drive_cifrado(self, token_cifrado: str, actor: str) -> None:
        """Registra un permiso de Drive cifrado, solo tras comprobar administración en BD."""
        if not token_cifrado:
            raise SupabaseStorageOperationError("No se recibió el permiso seguro de Google.")

        def callback(cursor):
            cursor.execute(
                """select id from safara.usuarios
                   where lower(btrim(nombre)) = lower(btrim(%s)) and activo and rol = 'admin'""",
                (actor,),
            )
            admin = cursor.fetchone()
            if not admin:
                raise SupabaseStorageOperationError(
                    "Solo una persona administradora puede autorizar Google Drive."
                )
            cursor.execute(
                """insert into safara.google_drive_oauth
                   (id, token_cifrado, autorizado_por, actualizado_en)
                   values (1, %s, %s, now())
                   on conflict (id) do update set
                     token_cifrado = excluded.token_cifrado,
                     autorizado_por = excluded.autorizado_por,
                     actualizado_en = now()""",
                (token_cifrado, admin["id"]),
            )
            cursor.execute(
                """insert into safara.auditoria (evento, usuario_id, detalle)
                   values ('autorizacion_google_drive_actualizada', %s,
                   'Permiso de Drive renovado de forma cifrada')""",
                (admin["id"],),
            )

        self._run(callback)

    def guardar_autorizacion_google_drive(
        self, token_cifrado: str, carpeta_id: str, actor: str
    ) -> None:
        """Guarda una autorización ya verificada junto a su carpeta propia."""
        if not token_cifrado or not carpeta_id:
            raise SupabaseStorageOperationError(
                "Google Drive no devolvió una autorización completa."
            )

        def callback(cursor):
            cursor.execute(
                """select id from safara.usuarios
                   where lower(btrim(nombre)) = lower(btrim(%s)) and activo and rol = 'admin'""",
                (actor,),
            )
            admin = cursor.fetchone()
            if not admin:
                raise SupabaseStorageOperationError(
                    "Solo una persona administradora puede autorizar Google Drive."
                )
            cursor.execute(
                """insert into safara.google_drive_oauth
                   (id, token_cifrado, carpeta_id, autorizado_por, actualizado_en)
                   values (1, %s, %s, %s, now())
                   on conflict (id) do update set
                     token_cifrado = excluded.token_cifrado,
                     carpeta_id = excluded.carpeta_id,
                     autorizado_por = excluded.autorizado_por,
                     actualizado_en = now()""",
                (token_cifrado, carpeta_id, admin["id"]),
            )
            cursor.execute(
                """insert into safara.auditoria (evento, usuario_id, detalle)
                   values ('autorizacion_google_drive_verificada', %s,
                   'Permiso y carpeta privada de Drive verificados')""",
                (admin["id"],),
            )

        self._run(callback)

    def _user_id(self, cursor, nombre: str):
        cursor.execute(
            """select id from safara.usuarios
               where lower(btrim(nombre)) = lower(btrim(%s)) and activo""",
            (nombre,),
        )
        row = cursor.fetchone()
        if not row:
            raise SupabaseStorageOperationError("La persona usuaria ya no está disponible.")
        return row["id"]

    def read_records(self, entity: str) -> list[dict[str, Any]]:
        queries = {
            "Usuarios": """select nombre as \"Nombre\", rol, password_salt, password_hash,
                email, telefono as tel, fecha_nacimiento as fnac, instrumento,
                true as rgpd from safara.usuarios where activo order by lower(nombre)""",
            "Invitaciones": """select i.codigo_hash, em.nombre as emitido_por,
                i.creado_en, i.caduca_en, coalesce(us.nombre, '') as usado_por, i.usado_en
                from safara.invitaciones i join safara.usuarios em on em.id=i.emitido_por
                left join safara.usuarios us on us.id=i.usado_por order by i.creado_en desc""",
            "Votos": """select v.encuesta_id, v.ciclo_id, u.nombre as usuario_id,
                v.respuesta, v.actualizado_en from safara.votos v
                join safara.usuarios u on u.id=v.usuario_id""",
            "Actuaciones": """select id, titulo, fecha, hora, lugar, estado,
                id + 2 as sheet_col from safara.actuaciones order by fecha, id""",
            "Gastos": """select g.id as \"ID\", g.referencia_anual as \"Referencia\", g.fecha as \"Fecha\", u.nombre as \"Usuario\",
                g.concepto as \"Concepto\", g.importe as \"Importe\", g.fichero as \"Fichero\",
                g.estado_reembolso as \"Reembolsado\", coalesce(g.enlace_ticket, '') as \"Enlace Ticket\",
                coalesce(g.drive_file_id, '') as \"Drive File ID\", coalesce(g.mime_type, '') as \"MIME Type\",
                g.estado_justificante as \"Estado Justificante\"
                from safara.gastos g join safara.usuarios u on u.id=g.usuario_id order by g.fecha desc, g.id desc""",
            "Confesionario": """select u.nombre as usuario, c.mensaje, c.creado_en as fecha
                from safara.confesionario c join safara.usuarios u on u.id=c.usuario_id
                order by c.creado_en""",
            "Caja": "select clave, valor from safara.caja",
        }
        if entity not in queries:
            return []

        def callback(cursor):
            cursor.execute(queries[entity])
            records = list(cursor.fetchall())
            for record in records:
                for key, value in list(record.items()):
                    if isinstance(value, Decimal):
                        record[key] = float(value)
                    elif isinstance(value, (dt.datetime, dt.date)):
                        record[key] = value.isoformat()
            return records

        return self._run(callback)

    def append_audit(self, event: str, user: str = "", detail: str = "", when: str = "") -> None:
        def callback(cursor):
            user_id = None
            if user:
                cursor.execute(
                    "select id from safara.usuarios where lower(btrim(nombre))=lower(btrim(%s))",
                    (user,),
                )
                row = cursor.fetchone()
                user_id = row["id"] if row else None
            timestamp = dt.datetime.fromisoformat(when) if when else dt.datetime.now(dt.timezone.utc)
            cursor.execute(
                "insert into safara.auditoria (fecha_hora, evento, usuario_id, detalle) values (%s, %s, %s, %s)",
                (timestamp, event, user_id, detail.replace("\n", " ")[:2000]),
            )
        try:
            self._run(callback)
        except SupabaseStorageOperationError:
            return

    def registrar_usuario(self, nombre: str, data: dict[str, Any], codigo_invitacion: str = "") -> bool:
        def callback(cursor):
            # Serializa solo el primer alta para impedir dos administradores iniciales.
            cursor.execute("select pg_advisory_xact_lock(hashtext('safara-bootstrap-admin'))")
            cursor.execute("select count(*) as total from safara.usuarios where activo")
            primer_usuario = cursor.fetchone()["total"] == 0
            if not primer_usuario:
                candidate = None
                cursor.execute(
                    """select id, codigo_hash from safara.invitaciones
                       where usado_por is null and caduca_en > now() for update"""
                )
                for invitation in cursor.fetchall():
                    if verify_invitation_code(codigo_invitacion, invitation["codigo_hash"]):
                        candidate = invitation["id"]
                        break
                if not candidate:
                    return False
            cursor.execute(
                """insert into safara.usuarios
                   (nombre, rol, password_salt, password_hash, email, telefono, fecha_nacimiento, instrumento, rgpd_aceptado_en)
                   values (%s,%s,%s,%s,%s,%s,%s,%s,now()) returning id""",
                (nombre, data["rol"], data["password_salt"], data["password_hash"], data["email"],
                 data["tel"], self._as_date(data["fnac"]), data["instrumento"]),
            )
            created_id = cursor.fetchone()["id"]
            if not primer_usuario:
                cursor.execute(
                    "update safara.invitaciones set usado_por=%s, usado_en=now() where id=%s and usado_por is null",
                    (created_id, candidate),
                )
                if cursor.rowcount != 1:
                    raise SupabaseStorageOperationError("El código de alta ya ha sido utilizado.")
            return True
        return bool(self._run(callback))

    def crear_invitacion(self, codigo_hash: str, emitido_por: str, caduca_en: str) -> None:
        def callback(cursor):
            cursor.execute(
                """insert into safara.invitaciones (codigo_hash, emitido_por, caduca_en)
                   values (%s, %s, %s)""",
                (codigo_hash, self._user_id(cursor, emitido_por), dt.datetime.fromisoformat(caduca_en)),
            )
        self._run(callback)

    def guardar_voto(self, encuesta_id: str, ciclo_id: str, usuario: str, respuesta: str) -> None:
        def callback(cursor):
            cursor.execute(
                """insert into safara.votos (encuesta_id, ciclo_id, usuario_id, respuesta)
                   select %s, %s, id, %s
                   from safara.usuarios
                   where lower(btrim(nombre)) = lower(btrim(%s)) and activo
                   on conflict (encuesta_id, ciclo_id, usuario_id)
                   do update set respuesta=excluded.respuesta, actualizado_en=now()
                   returning id""",
                (encuesta_id, ciclo_id, respuesta, usuario),
            )
            if not cursor.fetchone():
                raise SupabaseStorageOperationError("La persona usuaria ya no está activa.")
        self._run(callback)

    def obtener_o_crear_plan_ensayo(
        self, ciclo_id: str, lunes: dt.date, ubicacion_predeterminada: str
    ) -> dict[str, Any]:
        """Obtiene el plan oficial o crea uno respetando la última sede activa."""
        def callback(cursor):
            cursor.execute("select pg_advisory_xact_lock(hashtext('safara-weekly-rehearsal-plan'))")
            cursor.execute(
                """select ciclo_id, lunes, ubicacion, estado, motivo_pausa
                   from safara.ensayos_planificacion where ciclo_id=%s""",
                (ciclo_id,),
            )
            plan = cursor.fetchone()
            if plan:
                return plan
            cursor.execute(
                """select ubicacion from safara.ensayos_planificacion
                   where lunes < %s and estado='ACTIVO'
                   order by lunes desc limit 1""",
                (lunes,),
            )
            anterior = cursor.fetchone()
            ubicacion = ubicacion_predeterminada
            if anterior:
                ultima = str(anterior.get("ubicacion") or "")
                if ultima == "Gaztetxe de Zizur":
                    ubicacion = "Baragazte (Barañain)"
                elif ultima == "Baragazte (Barañain)":
                    ubicacion = "Gaztetxe de Zizur"
            cursor.execute(
                """insert into safara.ensayos_planificacion
                   (ciclo_id, lunes, ubicacion) values (%s, %s, %s)
                   returning ciclo_id, lunes, ubicacion, estado, motivo_pausa""",
                (ciclo_id, lunes, ubicacion),
            )
            return cursor.fetchone()
        return dict(self._run(callback))

    def actualizar_plan_ensayo(
        self,
        ciclo_id: str,
        lunes: dt.date,
        ubicacion: str,
        pausado: bool,
        motivo: str,
        administrador: str,
    ) -> dict[str, Any] | None:
        """Cambia una semana abierta; nunca altera un historial ya cerrado."""
        estado = "PAUSADO" if pausado else "ACTIVO"
        motivo_seguro = str(motivo or "").strip()[:500] if pausado else ""

        def callback(cursor):
            cursor.execute("select pg_advisory_xact_lock(hashtext('safara-weekly-rehearsal-plan'))")
            cursor.execute(
                "select 1 from safara.ensayos_historial where ciclo_id=%s",
                (ciclo_id,),
            )
            if cursor.fetchone():
                return None
            admin_id = self._user_id(cursor, administrador)
            cursor.execute(
                """insert into safara.ensayos_planificacion
                   (ciclo_id, lunes, ubicacion, estado, motivo_pausa, actualizado_por)
                   values (%s, %s, %s, %s, %s, %s)
                   on conflict (ciclo_id) do update set
                     lunes=excluded.lunes, ubicacion=excluded.ubicacion,
                     estado=excluded.estado, motivo_pausa=excluded.motivo_pausa,
                     actualizado_por=excluded.actualizado_por, actualizado_en=now()
                   returning ciclo_id, lunes, ubicacion, estado, motivo_pausa""",
                (ciclo_id, lunes, ubicacion, estado, motivo_seguro, admin_id),
            )
            cursor.execute(
                """insert into safara.auditoria (evento, usuario_id, detalle)
                   values ('plan_ensayo_actualizado', %s, %s)""",
                (admin_id, f"{ciclo_id}: {estado} - {ubicacion}"),
            )
            return cursor.fetchone()
        result = self._run(callback)
        return dict(result) if result else None

    def cerrar_ensayo_semanal(
        self,
        ciclo_id: str,
        fecha: dt.date,
        hora_cierre: dt.time,
        ubicacion: str,
        quorum_minimo: int,
    ) -> dict[str, Any]:
        """Cierra una semana de ensayo una sola vez y conserva su resultado.

        La exclusión transaccional evita que dos visitas simultáneas generen
        resultados distintos. Los votos originales no se modifican ni eliminan.
        """
        def callback(cursor):
            cursor.execute("select pg_advisory_xact_lock(hashtext('safara-weekly-rehearsal'))")
            cursor.execute(
                """select ubicacion, estado, motivo_pausa
                   from safara.ensayos_planificacion where ciclo_id=%s""",
                (ciclo_id,),
            )
            plan = cursor.fetchone() or {}
            ubicacion_oficial = str(plan.get("ubicacion") or ubicacion)
            pausado = str(plan.get("estado") or "ACTIVO") == "PAUSADO"
            motivo = str(plan.get("motivo_pausa") or "") if pausado else ""
            cursor.execute(
                """select count(*)::integer as asistentes,
                          count(*) filter (where u.instrumento = 'Repenike')::integer as repenikes,
                          count(*) filter (where u.instrumento = 'Caja')::integer as cajas
                   from safara.votos v
                   join safara.usuarios u on u.id = v.usuario_id and u.activo
                   where v.encuesta_id = 'ensayo_proximo'
                     and v.ciclo_id = %s and v.respuesta = 'SI'""",
                (ciclo_id,),
            )
            resumen = cursor.fetchone() or {"asistentes": 0, "repenikes": 0, "cajas": 0}
            asistentes = int(resumen["asistentes"] or 0)
            repenikes = int(resumen["repenikes"] or 0)
            cajas = int(resumen["cajas"] or 0)
            estado = (
                "PAUSADO" if pausado else "CONFIRMADO"
                if asistentes >= quorum_minimo and repenikes >= 1 and cajas >= 1
                else "NO_REALIZADO"
            )
            cursor.execute(
                """insert into safara.ensayos_historial
                   (ciclo_id, fecha, hora_cierre, ubicacion, estado, motivo,
                    asistentes_confirmados, repenikes_confirmados, cajas_confirmadas)
                   values (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                   on conflict (ciclo_id) do nothing
                   returning ciclo_id, fecha, hora_cierre, ubicacion, estado, motivo,
                             asistentes_confirmados, repenikes_confirmados,
                             cajas_confirmadas, cerrado_en""",
                (ciclo_id, fecha, hora_cierre, ubicacion_oficial, estado, motivo,
                 asistentes, repenikes, cajas),
            )
            cerrado = cursor.fetchone()
            if cerrado:
                cursor.execute(
                    """insert into safara.auditoria (evento, detalle)
                       values ('ensayo_semanal_cerrado', %s)""",
                    (f"{ciclo_id}: {estado} ({asistentes} asistentes, "
                     f"{repenikes} repenikes, {cajas} cajas)",),
                )
                return cerrado
            cursor.execute(
                """select ciclo_id, fecha, hora_cierre, ubicacion, estado, motivo,
                          asistentes_confirmados, repenikes_confirmados,
                          cajas_confirmadas, cerrado_en
                   from safara.ensayos_historial where ciclo_id = %s""",
                (ciclo_id,),
            )
            return cursor.fetchone()

        return self._run(callback)

    def obtener_historial_ensayos(self, limite: int = 52) -> list[dict[str, Any]]:
        """Devuelve el historial semanal más reciente, sin exponer votos individuales."""
        limite = max(1, min(int(limite), 260))

        def callback(cursor):
            cursor.execute(
                """select h.ciclo_id, h.fecha, h.hora_cierre, h.ubicacion, h.estado,
                          h.motivo,
                          h.asistentes_confirmados, h.repenikes_confirmados,
                          h.cajas_confirmadas, h.cerrado_en,
                          count(a.usuario_id)::integer as asistentes_reales
                   from safara.ensayos_historial h
                   left join safara.ensayos_asistencias a on a.ciclo_id=h.ciclo_id
                   group by h.ciclo_id, h.fecha, h.hora_cierre, h.ubicacion, h.estado,
                            h.motivo, h.asistentes_confirmados, h.repenikes_confirmados,
                            h.cajas_confirmadas, h.cerrado_en
                   order by h.fecha desc limit %s""",
                (limite,),
            )
            rows = list(cursor.fetchall())
            for row in rows:
                for key, value in list(row.items()):
                    if isinstance(value, (dt.datetime, dt.date, dt.time)):
                        row[key] = value.isoformat()
            return rows

        return self._run(callback)

    def candidatos_asistencia_ensayo(self, ciclo_id: str) -> list[dict[str, Any]]:
        """Lista personas activas y marca las que confirmaron la encuesta."""
        def callback(cursor):
            cursor.execute(
                """select u.nombre,
                    exists(select 1 from safara.votos v
                           where v.encuesta_id='ensayo_proximo' and v.ciclo_id=%s
                             and v.usuario_id=u.id and v.respuesta='SI') as confirmado,
                    exists(select 1 from safara.ensayos_asistencias a
                           where a.ciclo_id=%s and a.usuario_id=u.id) as asistio
                   from safara.usuarios u where u.activo order by lower(u.nombre)""",
                (ciclo_id, ciclo_id),
            )
            return list(cursor.fetchall())
        return [dict(row) for row in self._run(callback)]

    def confirmar_asistencias_ensayo(
        self, ciclo_id: str, asistentes: list[str], administrador: str
    ) -> int:
        """Sustituye la lista oficial de asistencia; un punto equivale a una asistencia."""
        nombres = sorted({str(nombre).strip() for nombre in asistentes if str(nombre).strip()})

        def callback(cursor):
            cursor.execute("select pg_advisory_xact_lock(hashtext('safara-weekly-rehearsal-attendance'))")
            cursor.execute(
                "select estado from safara.ensayos_historial where ciclo_id=%s for update",
                (ciclo_id,),
            )
            historial = cursor.fetchone()
            if not historial or historial["estado"] != "CONFIRMADO":
                return -1
            admin_id = self._user_id(cursor, administrador)
            usuarios = [self._user_id(cursor, nombre) for nombre in nombres]
            cursor.execute("delete from safara.ensayos_asistencias where ciclo_id=%s", (ciclo_id,))
            for usuario_id in usuarios:
                cursor.execute(
                    """insert into safara.ensayos_asistencias
                       (ciclo_id, usuario_id, confirmado_por) values (%s, %s, %s)""",
                    (ciclo_id, usuario_id, admin_id),
                )
            cursor.execute(
                """insert into safara.auditoria (evento, usuario_id, detalle)
                   values ('asistencia_ensayo_confirmada', %s, %s)""",
                (admin_id, f"{ciclo_id}: {len(usuarios)} asistencia(s) confirmada(s)"),
            )
            return len(usuarios)
        return int(self._run(callback))

    def obtener_puntuacion_ensayos(self, limite: int = 10) -> list[dict[str, Any]]:
        """Clasificación derivada: no hay contadores duplicados ni puntos repetidos."""
        limite = max(1, min(int(limite), 50))
        def callback(cursor):
            cursor.execute(
                """select u.nombre, count(a.ciclo_id)::integer as puntos
                   from safara.usuarios u
                   left join safara.ensayos_asistencias a on a.usuario_id=u.id
                   where u.activo
                   group by u.id, u.nombre
                   order by puntos desc, lower(u.nombre) asc limit %s""",
                (limite,),
            )
            return list(cursor.fetchall())
        return [dict(row) for row in self._run(callback)]

    def crear_actuacion(self, data: dict[str, Any], usuario: str) -> dict[str, Any]:
        def callback(cursor):
            cursor.execute(
                """insert into safara.actuaciones (titulo, fecha, hora, lugar, estado, creado_por)
                   values (%s,%s,%s,%s,%s,%s) returning id""",
                (data["titulo"], self._as_date(data["fecha"]), data["hora"], data["lugar"],
                 data["estado"], self._user_id(cursor, usuario)),
            )
            record = dict(data)
            record["id"] = int(cursor.fetchone()["id"])
            record["sheet_col"] = record["id"] + 2
            return record
        return self._run(callback)

    def cambiar_estado_actuacion(self, actuacion_id: int, estado: str) -> bool:
        def callback(cursor):
            cursor.execute("update safara.actuaciones set estado=%s where id=%s", (estado, actuacion_id))
            return cursor.rowcount == 1
        return bool(self._run(callback))

    def eliminar_actuacion(self, actuacion_id: int) -> bool:
        def callback(cursor):
            cursor.execute("delete from safara.actuaciones where id=%s", (actuacion_id,))
            return cursor.rowcount == 1
        return bool(self._run(callback))

    def crear_gasto(self, data: dict[str, Any]) -> dict[str, Any]:
        def callback(cursor):
            referencia = self._siguiente_referencia_gasto(cursor, data["Fecha"])
            fichero = self._nombre_ticket(referencia, str(data["Fichero"]))
            cursor.execute(
                """insert into safara.gastos
                   (fecha, usuario_id, concepto, importe, fichero, referencia_anual, estado_reembolso, enlace_ticket, drive_file_id, mime_type)
                   values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) returning id""",
                (self._as_date(data["Fecha"]), self._user_id(cursor, data["Usuario"]), data["Concepto"],
                 data["Importe"], fichero, referencia, data["Reembolsado"], data.get("Enlace Ticket") or None,
                 data.get("Drive File ID") or None, data.get("MIME Type") or None),
            )
            record = dict(data)
            record["ID"] = int(cursor.fetchone()["id"])
            record["Referencia"] = referencia
            record["Fichero"] = fichero
            return record
        return self._run(callback)

    def crear_gasto_con_justificante_pendiente(
        self, data: dict[str, Any], contenido: bytes
    ) -> dict[str, Any]:
        """Confirma primero el gasto y conserva el archivo hasta que Drive responda.

        No se vuelve a pedir al usuario un ticket que ya ha enviado cuando Google
        tenga una incidencia temporal.
        """
        if not contenido or len(contenido) > 10 * 1024 * 1024:
            raise SupabaseStorageOperationError("El justificante no tiene un tamaño válido.")

        def callback(cursor):
            referencia = self._siguiente_referencia_gasto(cursor, data["Fecha"])
            fichero = self._nombre_ticket(referencia, str(data["Fichero"]))
            usuario_id = self._user_id(cursor, data["Usuario"])
            cursor.execute(
                """insert into safara.gastos
                   (fecha, usuario_id, concepto, importe, fichero, referencia_anual, estado_reembolso,
                    enlace_ticket, drive_file_id, mime_type, estado_justificante)
                   values (%s,%s,%s,%s,%s,%s,%s,null,null,%s,'PENDIENTE_DRIVE') returning id""",
                (
                    self._as_date(data["Fecha"]), usuario_id,
                    data["Concepto"], data["Importe"], fichero, referencia,
                    data["Reembolsado"], data.get("MIME Type") or None,
                ),
            )
            gasto_id = int(cursor.fetchone()["id"])
            cursor.execute(
                """insert into safara.justificantes_pendientes
                   (gasto_id, contenido, nombre_fichero, mime_type)
                   values (%s, %s, %s, %s)""",
                (gasto_id, contenido, fichero, data.get("MIME Type") or None),
            )
            # El registro económico y su huella de auditoría se confirman en
            # la misma transacción. Aunque el proceso se interrumpa después,
            # nunca existirá un gasto fiscal sin trazabilidad.
            cursor.execute(
                """insert into safara.auditoria (evento, usuario_id, detalle)
                   values ('gasto_registrado', %s, %s)""",
                (usuario_id, f"Gasto {referencia} registrado"),
            )
            record = dict(data)
            record["ID"] = gasto_id
            record["Referencia"] = referencia
            record["Fichero"] = fichero
            record["Estado Justificante"] = "PENDIENTE_DRIVE"
            return record

        return self._run(callback)

    def obtener_justificante_pendiente(self, gasto_id: int) -> dict[str, Any] | None:
        def callback(cursor):
            cursor.execute(
                """select gasto_id, contenido, nombre_fichero, mime_type, intentos
                   from safara.justificantes_pendientes where gasto_id = %s""",
                (int(gasto_id),),
            )
            return cursor.fetchone()

        return self._run(callback)

    def reservar_justificantes_pendientes(
        self, limite: int = 10, forzar: bool = False
    ) -> list[dict[str, Any]]:
        """Reserva tickets para un único envío de Drive sin duplicarlos.

        La reserva se guarda antes de salir de la transacción. Así dos sesiones
        de Streamlit nunca suben por error el mismo justificante a Drive.
        """
        limite = max(1, min(int(limite), 25))

        def callback(cursor):
            condition = "true" if forzar else "(p.proximo_intento_en is null or p.proximo_intento_en <= now())"
            cursor.execute(
                f"""select p.gasto_id, p.contenido, p.nombre_fichero, p.mime_type
                       from safara.justificantes_pendientes p
                      where {condition}
                      order by p.actualizado_en asc
                      limit %s for update skip locked""",
                (limite,),
            )
            pendientes = list(cursor.fetchall())
            if not pendientes:
                return []
            cursor.execute(
                """update safara.justificantes_pendientes
                      set intentos = intentos + 1, ultimo_intento_en = now(),
                          proximo_intento_en = now() + interval '5 minutes',
                          actualizado_en = now()
                    where gasto_id = any(%s)""",
                ([int(item["gasto_id"]) for item in pendientes],),
            )
            return pendientes

        return list(self._run(callback))

    def confirmar_justificante_drive(
        self, gasto_id: int, drive_file_id: str, enlace_ticket: str
    ) -> None:
        if not drive_file_id:
            raise SupabaseStorageOperationError("Drive no devolvió el identificador del justificante.")

        def callback(cursor):
            cursor.execute(
                """update safara.gastos set drive_file_id=%s, enlace_ticket=%s,
                   estado_justificante='GUARDADO' where id=%s""",
                (drive_file_id, enlace_ticket or None, int(gasto_id)),
            )
            if cursor.rowcount != 1:
                raise SupabaseStorageOperationError("No se encuentra el gasto que se iba a actualizar.")
            cursor.execute(
                "delete from safara.justificantes_pendientes where gasto_id=%s", (int(gasto_id),)
            )

        self._run(callback)

    def marcar_justificante_pendiente(self, gasto_id: int, error: str) -> None:
        """Anota el fallo sin borrar el justificante pendiente ni bloquear al usuario."""
        def callback(cursor):
            cursor.execute(
                """update safara.justificantes_pendientes
                   set ultimo_error = %s,
                       proximo_intento_en = now() + (
                         least(60, power(2, least(intentos, 6))::integer) * interval '1 minute'
                       ),
                       actualizado_en = now()
                   where gasto_id = %s""",
                (str(error)[:1000], int(gasto_id)),
            )
            cursor.execute(
                "update safara.gastos set estado_justificante='PENDIENTE_DRIVE' where id=%s",
                (int(gasto_id),),
            )

        self._run(callback)

    def listar_justificantes_pendientes(self, limite: int = 50) -> list[dict[str, Any]]:
        limite = max(1, min(int(limite), 100))

        def callback(cursor):
            cursor.execute(
                """select p.gasto_id, p.nombre_fichero, p.mime_type, p.intentos,
                          p.ultimo_error, p.proximo_intento_en, p.actualizado_en, u.nombre as usuario
                   from safara.justificantes_pendientes p
                   join safara.gastos g on g.id=p.gasto_id
                   join safara.usuarios u on u.id=g.usuario_id
                   order by p.actualizado_en asc limit %s""",
                (limite,),
            )
            return list(cursor.fetchall())

        return self._run(callback)

    def listar_justificantes_para_archivar(self) -> list[dict[str, Any]]:
        """Devuelve tickets existentes para su organización física en Drive."""
        def callback(cursor):
            cursor.execute(
                """select id as gasto_id, referencia_anual, fichero, drive_file_id
                   from safara.gastos
                   where drive_file_id is not null and drive_file_id <> ''
                   order by fecha, id"""
            )
            return list(cursor.fetchall())
        return self._run(callback)

    def confirmar_nombre_justificante(self, gasto_id: int, fichero: str) -> None:
        """Actualiza el nombre visible de Drive sin cambiar enlace ni identificador."""
        def callback(cursor):
            cursor.execute(
                """update safara.gastos set fichero=%s
                   where id=%s and fichero is distinct from %s""",
                (str(fichero)[:255], int(gasto_id), str(fichero)[:255]),
            )
        self._run(callback)

    def marcar_gasto_abonado(self, gasto_id: int, usuario: str) -> bool:
        def callback(cursor):
            usuario_id = self._user_id(cursor, usuario)
            cursor.execute(
                """update safara.gastos set estado_reembolso='ABONADO', abonado_en=now(), abonado_por=%s
                   where id=%s and estado_reembolso='PENDIENTE ABONO'""",
                (usuario_id, gasto_id),
            )
            actualizado = cursor.rowcount == 1
            if actualizado:
                cursor.execute(
                    """insert into safara.auditoria (evento, usuario_id, detalle)
                       values ('gasto_abonado', %s, %s)""",
                    (usuario_id, f"Gasto {int(gasto_id)} marcado como abonado"),
                )
            return actualizado
        return bool(self._run(callback))

    def guardar_confesion(self, usuario: str, mensaje: str) -> None:
        def callback(cursor):
            cursor.execute(
                "insert into safara.confesionario (usuario_id, mensaje) values (%s, %s)",
                (self._user_id(cursor, usuario), mensaje.strip()),
            )
        self._run(callback)

    def actualizar_saldo(self, saldo: float, usuario: str) -> bool:
        def callback(cursor):
            cursor.execute(
                """update safara.caja set valor=%s, version=version+1, actualizado_por=%s, actualizado_en=now()
                   where clave='saldo_caja'""",
                (saldo, self._user_id(cursor, usuario)),
            )
            return cursor.rowcount == 1
        return bool(self._run(callback))

    def desactivar_usuario(self, nombre: str) -> bool:
        def callback(cursor):
            cursor.execute("update safara.usuarios set activo=false where lower(btrim(nombre))=lower(btrim(%s))", (nombre,))
            return cursor.rowcount == 1
        return bool(self._run(callback))

    def iniciar_mantenimiento_google(self) -> dict[str, Any] | None:
        """Obtiene una exclusión temporal para sincronizar sin bloquear a usuarios."""
        def callback(cursor):
            cursor.execute(
                """update safara.mantenimiento
                   set bloqueado_hasta = now() + interval '15 minutes', actualizado_en = now()
                   where clave = 'integracion_google'
                     and (bloqueado_hasta is null or bloqueado_hasta < now())
                     and (proximo_intento_en is null or proximo_intento_en <= now())
                     and (sheets_revision <> sheets_synced_revision or ultimo_respaldo is null or ultimo_respaldo < current_date)
                   returning sheets_revision, sheets_synced_revision,
                             (ultimo_respaldo is null or ultimo_respaldo < current_date) as respaldo_pendiente"""
            )
            return cursor.fetchone()
        return self._run(callback)

    def terminar_mantenimiento_google(self, revision_sincronizada: int, respaldo_realizado: bool) -> None:
        def callback(cursor):
            cursor.execute(
                """update safara.mantenimiento
                   set sheets_synced_revision = greatest(sheets_synced_revision, %s),
                       ultimo_respaldo = case when %s then current_date else ultimo_respaldo end,
                       bloqueado_hasta = null, proximo_intento_en = null, ultimo_error = null,
                       actualizado_en = now()
                   where clave = 'integracion_google'""",
                (revision_sincronizada, respaldo_realizado),
            )
        self._run(callback)

    def confirmar_informes_google(self, revision_sincronizada: int) -> None:
        """Confirma Sheets antes de intentar la copia adicional de Drive.

        Los informes son una vista de consulta. Si la copia diaria tuviera una
        incidencia, no debe dejar a la administración sin poder ver los gastos
        que ya se sincronizaron correctamente.
        """
        def callback(cursor):
            cursor.execute(
                """update safara.mantenimiento
                   set sheets_synced_revision = greatest(sheets_synced_revision, %s),
                       actualizado_en = now()
                   where clave = 'integracion_google'""",
                (revision_sincronizada,),
            )
        self._run(callback)

    def fallar_respaldo_google(self, error: str) -> None:
        """Deja pendiente solo la copia de respaldo, nunca los informes."""
        def callback(cursor):
            cursor.execute(
                """update safara.mantenimiento
                   set bloqueado_hasta = null, proximo_intento_en = now() + interval '5 minutes',
                       ultimo_error = %s, actualizado_en = now()
                   where clave = 'integracion_google'""",
                (error[:1000],),
            )
        try:
            self._run(callback)
        except SupabaseStorageOperationError:
            return

    def estado_mantenimiento_google(self) -> dict[str, Any]:
        """Estado seguro para administración; no devuelve credenciales ni rutas privadas."""
        def callback(cursor):
            cursor.execute(
                """select sheets_revision, sheets_synced_revision, ultimo_respaldo,
                          proximo_intento_en, ultimo_error, actualizado_en
                   from safara.mantenimiento where clave = 'integracion_google'"""
            )
            return cursor.fetchone() or {}
        return dict(self._run(callback))

    def fallar_mantenimiento_google(self, error: str) -> None:
        def callback(cursor):
            cursor.execute(
                """update safara.mantenimiento
                   set bloqueado_hasta = null, proximo_intento_en = now() + interval '5 minutes',
                       ultimo_error = %s, actualizado_en = now()
                   where clave = 'integracion_google'""",
                (error[:1000],),
            )
        try:
            self._run(callback)
        except SupabaseStorageOperationError:
            return

    def obtener_informes_google(self) -> dict[str, list[dict[str, Any]]]:
        """Genera una vista minimizada para administración, no una copia de credenciales."""
        queries = {
            "Informe Socios": """select nombre as \"Nombre\", rol as \"Rol\", instrumento as \"Instrumento\",
                creado_en::date as \"Activo desde\" from safara.usuarios where activo order by lower(nombre)""",
            "Informe Invitaciones": """select em.nombre as \"Emitida por\", i.creado_en as \"Creada\", i.caduca_en as \"Caduca\",
                coalesce(us.nombre, '') as \"Usada por\", coalesce(i.usado_en::text, '') as \"Usada el\"
                from safara.invitaciones i join safara.usuarios em on em.id=i.emitido_por
                left join safara.usuarios us on us.id=i.usado_por order by i.creado_en desc""",
            "Informe Votos": """select v.encuesta_id as \"Encuesta\", v.ciclo_id as \"Ciclo\", u.nombre as \"Persona\",
                v.respuesta as \"Respuesta\", v.actualizado_en as \"Actualizado\" from safara.votos v
                join safara.usuarios u on u.id=v.usuario_id order by v.actualizado_en desc""",
            "Informe Actuaciones": """select id as \"ID\", titulo as \"Título\", fecha as \"Fecha\", hora as \"Hora\",
                lugar as \"Lugar\", estado as \"Estado\" from safara.actuaciones order by fecha, id""",
            "Informe Gastos": """select g.referencia_anual as \"Referencia\", g.id as \"ID\", g.fecha as \"Fecha\", u.nombre as \"Persona\", g.concepto as \"Concepto\",
                g.importe as \"Importe\", g.estado_reembolso as \"Estado\", coalesce(g.enlace_ticket, '') as \"Ticket\"
                from safara.gastos g join safara.usuarios u on u.id=g.usuario_id order by g.fecha desc, g.id desc""",
            "Informe Caja": """select 'Saldo de caja' as \"Concepto\", valor as \"Importe\", actualizado_en as \"Actualizado\"
                from safara.caja where clave='saldo_caja'""",
        }
        def callback(cursor):
            result: dict[str, list[dict[str, Any]]] = {}
            for title, query in queries.items():
                cursor.execute(query)
                rows = list(cursor.fetchall())
                for row in rows:
                    for key, value in list(row.items()):
                        if isinstance(value, Decimal):
                            row[key] = float(value)
                        elif isinstance(value, (dt.datetime, dt.date)):
                            row[key] = value.isoformat()
                result[title] = rows
            return result
        return self._run(callback)

    def obtener_archivo_financiero(self) -> dict[str, list[dict[str, Any]]]:
        """Devuelve solo la información necesaria para copias administrativas y fiscales."""
        reports = self.obtener_informes_google()
        def callback(cursor):
            cursor.execute(
                """select a.fecha_hora as "Fecha", a.evento as "Evento",
                          coalesce(u.nombre, '') as "Persona", a.detalle as "Detalle"
                   from safara.auditoria a
                   left join safara.usuarios u on u.id=a.usuario_id
                   order by a.fecha_hora desc, a.id desc
                   limit 1000"""
            )
            rows = list(cursor.fetchall())
            for row in rows:
                for key, value in list(row.items()):
                    if isinstance(value, (dt.datetime, dt.date)):
                        row[key] = value.isoformat()
            return rows
        return {
            "gastos": reports["Informe Gastos"],
            "caja": reports["Informe Caja"],
            "actuaciones": reports["Informe Actuaciones"],
            "auditoria": self._run(callback),
        }

