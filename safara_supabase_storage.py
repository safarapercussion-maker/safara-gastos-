Attempting to perform the InitializeDefaultDrives operation on the 'FileSystem' provider failed.
"""Almacenamiento transaccional de SAFARA GASTOS en Supabase.

Este módulo se usa solo desde el servidor Streamlit. La credencial de base de
datos permanece en Streamlit Secrets y nunca se escribe en Git.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from safara_security import verify_invitation_code


class SupabaseStorageConfigurationError(RuntimeError):
    """La persistencia de Supabase se activó sin una configuración válida."""


class SupabaseStorageOperationError(RuntimeError):
    """Una operación transaccional no se pudo completar."""


def is_enabled(secrets: Any) -> bool:
    try:
        value = secrets.get("enable_supabase_storage", False)
    except (AttributeError, TypeError):
        return False
    return value is True or str(value).strip().lower() in {"true", "1", "si", "sí"}


@dataclass(frozen=True)
class SupabaseStorageConfig:
    database_url: str

    @classmethod
    def from_secrets(cls, secrets: Any) -> "SupabaseStorageConfig":
        try:
            url = str(secrets.get("database_url", "")).strip()
        except (AttributeError, TypeError) as error:
            raise SupabaseStorageConfigurationError(
                "Falta la conexión privada de Supabase en Streamlit Secrets."
            ) from error
        if not url.startswith(("postgresql://", "postgres://", "postgresql+psycopg://")):
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
        except ImportError as error:
            raise SupabaseStorageConfigurationError(
                "Falta la dependencia segura de PostgreSQL."
            ) from error
        self._database_url = config.database_url

    def _connect(self):
        import psycopg
        from psycopg.rows import dict_row

        return psycopg.connect(
            self._database_url,
            row_factory=dict_row,
            connect_timeout=10,
            options="-c search_path=safara,public",
        )

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

    def _run(self, callback):
        try:
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    return callback(cursor)
        except SupabaseStorageOperationError:
            raise
        except Exception as error:
            raise SupabaseStorageOperationError(
                "No se ha podido guardar la información en Supabase."
            ) from error

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
            "Gastos": """select g.id as \"ID\", g.fecha as \"Fecha\", u.nombre as \"Usuario\",
                g.concepto as \"Concepto\", g.importe as \"Importe\", g.fichero as \"Fichero\",
                g.estado_reembolso as \"Reembolsado\", coalesce(g.enlace_ticket, '') as \"Enlace Ticket\",
                coalesce(g.drive_file_id, '') as \"Drive File ID\", coalesce(g.mime_type, '') as \"MIME Type\"
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
                   values (%s, %s, %s, %s)
                   on conflict (encuesta_id, ciclo_id, usuario_id)
                   do update set respuesta=excluded.respuesta, actualizado_en=now()""",
                (encuesta_id, ciclo_id, self._user_id(cursor, usuario), respuesta),
            )
        self._run(callback)

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
            cursor.execute(
                """insert into safara.gastos
                   (fecha, usuario_id, concepto, importe, fichero, estado_reembolso, enlace_ticket, drive_file_id, mime_type)
                   values (%s,%s,%s,%s,%s,%s,%s,%s,%s) returning id""",
                (self._as_date(data["Fecha"]), self._user_id(cursor, data["Usuario"]), data["Concepto"],
                 data["Importe"], data["Fichero"], data["Reembolsado"], data.get("Enlace Ticket") or None,
                 data.get("Drive File ID") or None, data.get("MIME Type") or None),
            )
            record = dict(data)
            record["ID"] = int(cursor.fetchone()["id"])
            return record
        return self._run(callback)

    def marcar_gasto_abonado(self, gasto_id: int, usuario: str) -> bool:
        def callback(cursor):
            cursor.execute(
                """update safara.gastos set estado_reembolso='ABONADO', abonado_en=now(), abonado_por=%s
                   where id=%s and estado_reembolso='PENDIENTE ABONO'""",
                (self._user_id(cursor, usuario), gasto_id),
            )
            return cursor.rowcount == 1
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
            "Informe Gastos": """select g.id as \"ID\", g.fecha as \"Fecha\", u.nombre as \"Persona\", g.concepto as \"Concepto\",
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
        return {
            "gastos": reports["Informe Gastos"],
            "caja": reports["Informe Caja"],
            "actuaciones": reports["Informe Actuaciones"],
        }

