"""Safara Gastos: secure, persistent test application.

This module deliberately keeps all application state out of Streamlit's
ephemeral filesystem.  It is configured through Streamlit Secrets and can be
deployed unchanged to a PostgreSQL database (recommended) or run locally with
SQLite while developing.
"""

from __future__ import annotations

import base64
import datetime as dt
import hashlib
import hmac
from io import BytesIO
import os

import pandas as pd
import streamlit as st
from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship


class Base(DeclarativeBase):
  pass


class User(Base):
  __tablename__ = "users"
  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
  pin_hash: Mapped[str] = mapped_column(String(255))
  role: Mapped[str] = mapped_column(String(20), default="member")
  instrument: Mapped[str] = mapped_column(String(80), default="")
  created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)


class Event(Base):
  __tablename__ = "events"
  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  title: Mapped[str] = mapped_column(String(180))
  place: Mapped[str] = mapped_column(String(180))
  event_date: Mapped[dt.date] = mapped_column(Date)
  event_time: Mapped[str] = mapped_column(String(40))
  status: Mapped[str] = mapped_column(String(30), default="EVALUACION")
  sheet_column: Mapped[int | None] = mapped_column(Integer, nullable=True, unique=True)
  sync_status: Mapped[str] = mapped_column(String(30), default="pending")
  sync_error: Mapped[str | None] = mapped_column(Text, nullable=True)
  created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)
  votes: Mapped[list["Vote"]] = relationship(back_populates="event", cascade="all, delete-orphan")


class Vote(Base):
  __tablename__ = "votes"
  __table_args__ = (UniqueConstraint("event_id", "user_id", name="uq_vote_event_user"),)
  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  event_id: Mapped[int] = mapped_column(ForeignKey("events.id"))
  user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
  answer: Mapped[str] = mapped_column(String(3))
  sync_status: Mapped[str] = mapped_column(String(30), default="pending")
  sync_error: Mapped[str | None] = mapped_column(Text, nullable=True)
  updated_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow)
  event: Mapped[Event] = relationship(back_populates="votes")


class Expense(Base):
  __tablename__ = "expenses"
  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
  expense_date: Mapped[dt.date] = mapped_column(Date)
  category: Mapped[str] = mapped_column(String(120))
  concept: Mapped[str] = mapped_column(String(240))
  amount: Mapped[float] = mapped_column(Float)
  reimbursed: Mapped[bool] = mapped_column(Boolean, default=False)
  receipt_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
  receipt_mime: Mapped[str | None] = mapped_column(String(100), nullable=True)
  receipt_drive_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
  receipt_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
  created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)


class Message(Base):
  __tablename__ = "messages"
  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
  text: Mapped[str] = mapped_column(Text)
  anonymous: Mapped[bool] = mapped_column(Boolean, default=False)
  created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)


def _hash_pin(pin: str, salt: bytes | None = None) -> str:
  salt = salt or os.urandom(16)
  digest = hashlib.pbkdf2_hmac("sha256", pin.encode(), salt, 310_000)
  return base64.b64encode(salt + digest).decode()


def _valid_pin(pin: str, encoded: str) -> bool:
  raw = base64.b64decode(encoded.encode())
  return hmac.compare_digest(_hash_pin(pin, raw[:16]), encoded)


def _secret(name: str, default=None):
  try:
    return st.secrets.get(name, default)
  except Exception:
    return default


@st.cache_resource
def _engine(url: str):
  return create_engine(url, pool_pre_ping=True, future=True)


def _database_url() -> str | None:
  url = _secret("database_url") or _secret("DATABASE_URL")
  if url and str(url).startswith("postgresql://"):
    return "postgresql+psycopg://" + str(url)[len("postgresql://"):]
  return url


def _setup_database() -> tuple[object | None, str | None]:
  url = _database_url()
  if not url:
    return None, "Falta configurar la base de datos segura de este entorno."
  try:
    engine = _engine(url)
    Base.metadata.create_all(engine)
    bootstrap_name = _secret("bootstrap_admin_name")
    bootstrap_pin = _secret("bootstrap_admin_pin")
    if bootstrap_name and bootstrap_pin:
      with Session(engine) as db:
        if not db.scalar(select(User).where(User.name == str(bootstrap_name))):
          db.add(User(name=str(bootstrap_name), pin_hash=_hash_pin(str(bootstrap_pin)), role="admin"))
          db.commit()
    return engine, None
  except Exception:
    return None, "No se puede abrir la base de datos de este entorno. Revisa su configuración segura."


def _google_credentials():
  account = _secret("gcp_service_account")
  if not account:
    return None, "La conexión segura con Google aún no está configurada."
  try:
    from google.oauth2.service_account import Credentials
    credentials = Credentials.from_service_account_info(
        account,
        scopes=[
          "https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive",
        ],
    )
    return credentials, None
  except Exception:
    return None, "No se pudo autenticar la conexión con Google."


def _sheets_client():
  sheet_id = _secret("google_sheet_id")
  credentials, error = _google_credentials()
  if not sheet_id or error:
    return None, None, error or "Google Sheets aún no está configurado en este entorno."
  try:
    import gspread
    return gspread.authorize(credentials), sheet_id, None
  except Exception:
    return None, None, "No se pudo abrir la sincronización con Google Sheets."


def _upload_receipt(receipt) -> tuple[str | None, str | None, str | None]:
  """Store originals in the association Drive, never in the database."""
  folder_id = _secret("receipts_folder_id")
  credentials, error = _google_credentials()
  if not folder_id or error:
    return None, None, error or "Google Drive aún no está configurado para justificantes."
  try:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload
    media = MediaIoBaseUpload(BytesIO(receipt.getvalue()), mimetype=receipt.type or "application/octet-stream", resumable=False)
    drive = build("drive", "v3", credentials=credentials, cache_discovery=False)
    stored = drive.files().create(
      body={"name": receipt.name, "parents": [folder_id]},
      media_body=media,
      fields="id,webViewLink",
    ).execute()
    return stored.get("id"), stored.get("webViewLink"), None
  except Exception:
    return None, None, "No se ha podido archivar el justificante en Google Drive. El gasto no se ha guardado."


def _sync_event(event: Event) -> tuple[bool, str | None, int | None]:
  client, sheet_id, error = _sheets_client()
  if error:
    return False, error, None
  try:
    worksheet = client.open_by_key(sheet_id).worksheet(str(_secret("events_worksheet", "ACTUACIONES 2026")))
    rows = worksheet.get("A1:ZZ5")
    marker = f"safara-event:{event.id}"
    existing = next((idx + 1 for idx, value in enumerate(rows[0]) if value == marker), None) if rows else None
    column = existing or max(3, max((len(row) for row in rows), default=2) + 1)
    col_letter = _column_letter(column)
    values = [[marker], [event.status], [f"{event.title} — {event.place}"], [event.event_date.strftime("%d/%m/%Y")], [event.event_time]]
    worksheet.batch_update([{"range": f"{col_letter}1:{col_letter}5", "values": values}])
    return True, None, column
  except Exception:
    return False, "La actuación se ha guardado, pero Google Sheets no ha confirmado la sincronización.", None


def _column_letter(number: int) -> str:
  result = ""
  while number:
    number, remainder = divmod(number - 1, 26)
    result = chr(65 + remainder) + result
  return result


def _sync_vote(event: Event, user: User, vote: Vote) -> tuple[bool, str | None]:
  """Write one availability response using the shared sheet's existing layout."""
  if not event.sheet_column:
    return False, "La actuación aún espera su primera sincronización con Google Sheets."
  client, sheet_id, error = _sheets_client()
  if error:
    return False, error
  try:
    worksheet = client.open_by_key(sheet_id).worksheet(str(_secret("events_worksheet", "ACTUACIONES 2026")))
    members = worksheet.col_values(2)
    row = next((number for number, name in enumerate(members, start=1) if number >= 6 and name.strip().casefold() == user.name.casefold()), None)
    if not row:
      row = max(6, len(members) + 1)
      worksheet.batch_update([
          {"range": f"B{row}", "values": [[user.name]]},
          {"range": f"{_column_letter(event.sheet_column)}{row}", "values": [[vote.answer]]},
      ])
    else:
      worksheet.batch_update([{"range": f"{_column_letter(event.sheet_column)}{row}", "values": [[vote.answer]]}])
    return True, None
  except Exception:
    return False, "La respuesta está guardada, pero Google Sheets no ha confirmado la sincronización."


def _current_user(engine) -> User | None:
  user_id = st.session_state.get("secure_user_id")
  if not user_id:
    return None
  with Session(engine) as db:
    return db.get(User, user_id)


def _login_screen(engine):
  st.title("Safara Gastos · entorno de pruebas seguro")
  st.caption("Este entorno ya no permite acceder con enlaces que suplanten a una persona.")
  left, right = st.columns(2)
  with left:
    st.subheader("Acceder")
    with Session(engine) as db:
      names = [u.name for u in db.scalars(select(User).order_by(User.name)).all()]
    if names:
      name = st.selectbox("Usuario", names)
      pin = st.text_input("PIN", type="password")
      if st.button("Entrar", use_container_width=True):
        with Session(engine) as db:
          user = db.scalar(select(User).where(User.name == name))
          if user and _valid_pin(pin, user.pin_hash):
            st.session_state.secure_user_id = user.id
            st.rerun()
          st.error("Acceso no válido.")
    else:
      st.info("La primera alta de este entorno de pruebas será administradora.")
  with right:
    st.subheader("Solicitar alta")
    with st.form("signup"):
      name = st.text_input("Nombre")
      instrument = st.text_input("Instrumento")
      pin = st.text_input("Elige un PIN de al menos 6 caracteres", type="password")
      accepted = st.checkbox("Acepto el uso interno de mis datos para Safara Percussion")
      submitted = st.form_submit_button("Crear acceso", use_container_width=True)
    if submitted:
      if len(pin) < 6 or not name.strip() or not accepted:
        st.error("Completa nombre, consentimiento y un PIN de al menos 6 caracteres.")
      else:
        with Session(engine) as db:
          if db.scalar(select(User).where(User.name == name.strip())):
            st.error("Ese nombre ya está registrado.")
          else:
            # A test-only secret explicitly permits the first self-registered
            # person to administer a brand-new test database. Production never
            # enables this path.
            first_test_user = db.scalar(select(User.id).limit(1)) is None
            test_admin = first_test_user and bool(_secret("allow_first_test_admin", False))
            created_user = User(
              name=name.strip(),
              instrument=instrument.strip(),
              pin_hash=_hash_pin(pin),
              role="admin" if test_admin else "member",
            )
            db.add(created_user)
            db.commit()
            db.refresh(created_user)
            st.session_state.secure_user_id = created_user.id
            st.rerun()


def _event_tab(engine, user: User):
  st.subheader("Agenda y bolos")
  with Session(engine) as db:
    events = db.scalars(select(Event).order_by(Event.event_date)).all()
    for event in events:
      votes = db.scalars(select(Vote).where(Vote.event_id == event.id)).all()
      yes_count = sum(v.answer == "SI" for v in votes)
      st.markdown(f"### {event.title}")
      st.write(f"{event.event_date.strftime('%d/%m/%Y')} · {event.event_time} · {event.place}")
      st.caption(f"Estado: {event.status} · Confirmaciones: {yes_count} · Google Sheets: {event.sync_status}")
      vote = next((v for v in votes if v.user_id == user.id), None)
      c1, c2 = st.columns(2)
      selected_answer = "SI" if c1.button("Asistiré", key=f"yes-{event.id}") else "NO" if c2.button("No puedo", key=f"no-{event.id}") else None
      if selected_answer:
        try:
          if vote:
            vote.answer = selected_answer
          else:
            vote = Vote(event_id=event.id, user_id=user.id, answer=selected_answer)
            db.add(vote)
          db.commit()
        except IntegrityError:
          # A second browser session saved at the same time. Keep one answer.
          db.rollback()
          vote = db.scalar(select(Vote).where(Vote.event_id == event.id, Vote.user_id == user.id))
          if not vote:
            st.error("No se ha podido guardar la respuesta. Inténtalo de nuevo.")
            return
          vote.answer = selected_answer
          db.commit()
        ok, error = _sync_vote(event, user, vote)
        vote.sync_status = "synced" if ok else "pending"
        vote.sync_error = error
        db.commit()
        if error:
          st.warning(error)
        else:
          st.success("Respuesta guardada y sincronizada.")
      st.divider()


def _expenses_tab(engine, user: User):
  st.subheader("Caja y finanzas")
  with st.form("expense"):
    category = st.selectbox("Categoría", ["Parking", "Instrumentos", "Bebidas", "Accesorios", "Equipamiento", "Dietas", "Gasolina", "Otros"])
    concept = st.text_input("Concepto")
    amount = st.number_input("Importe (€)", min_value=0.01, step=0.5)
    expense_date = st.date_input("Fecha", dt.date.today())
    receipt = st.file_uploader("Ticket (imagen o PDF, máximo 6 MB)", type=["png", "jpg", "jpeg", "pdf"])
    submitted = st.form_submit_button("Registrar gasto", use_container_width=True)
  if submitted:
    if not concept.strip() or receipt is None or receipt.size > 6 * 1024 * 1024:
      st.error("Añade un concepto y un ticket de un máximo de 6 MB.")
    else:
      drive_id, drive_url, error = _upload_receipt(receipt)
      if error:
        st.error(error)
      else:
        with Session(engine) as db:
          db.add(Expense(user_id=user.id, expense_date=expense_date, category=category, concept=concept.strip(), amount=float(amount), receipt_name=receipt.name, receipt_mime=receipt.type, receipt_drive_id=drive_id, receipt_url=drive_url))
          db.commit()
        st.success("Gasto y justificante archivados de forma persistente.")
  with Session(engine) as db:
    expenses = db.scalars(select(Expense).order_by(Expense.expense_date.desc())).all()
    users = {u.id: u.name for u in db.scalars(select(User)).all()}
    rows = [{"Fecha": e.expense_date, "Persona": users.get(e.user_id, ""), "Categoría": e.category, "Concepto": e.concept, "Importe": e.amount, "Abonado": "Sí" if e.reimbursed else "Pendiente"} for e in expenses]
  if rows:
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.caption("Los justificantes originales se archivan en Google Drive; la aplicación guarda una referencia segura.")
    for expense in expenses:
      if expense.receipt_url and expense.receipt_name:
        st.link_button(f"Abrir justificante · {expense.concept}", expense.receipt_url, use_container_width=True)


def _messages_tab(engine, user: User):
  st.subheader("Sugerencias y avisos")
  with st.form("message"):
    text = st.text_area("Comparte una idea, incidencia o aviso")
    anonymous = st.checkbox("Publicar sin mostrar mi nombre")
    sent = st.form_submit_button("Enviar", use_container_width=True)
  if sent:
    if not text.strip():
      st.error("Escribe un mensaje antes de enviarlo.")
    else:
      with Session(engine) as db:
        db.add(Message(user_id=None if anonymous else user.id, text=text.strip(), anonymous=anonymous))
        db.commit()
      st.success("Mensaje guardado.")
  with Session(engine) as db:
    messages = db.scalars(select(Message).order_by(Message.created_at.desc())).all()
    names = {member.id: member.name for member in db.scalars(select(User)).all()}
  for message in messages:
    author = "Anónimo" if message.anonymous else names.get(message.user_id, "Miembro")
    st.markdown(f"**{author}** · {message.created_at.strftime('%d/%m/%Y %H:%M')}")
    st.write(message.text)
    st.divider()


def _home_tab(engine, user: User):
  st.header("Todo Safara, de un vistazo")
  st.caption("Elige una pestaña para consultar la agenda, registrar un gasto o dejar una sugerencia.")
  with Session(engine) as db:
    upcoming = db.scalars(select(Event).where(Event.event_date >= dt.date.today()).order_by(Event.event_date)).all()
    pending_expenses = db.scalars(select(Expense).where(Expense.reimbursed.is_(False))).all()
    messages = db.scalars(select(Message)).all()
  a, b, c = st.columns(3)
  a.metric("Próximas actuaciones", len(upcoming))
  b.metric("Gastos pendientes", len(pending_expenses))
  c.metric("Sugerencias", len(messages))
  st.divider()
  if upcoming:
    next_event = upcoming[0]
    st.subheader("Próxima actuación")
    st.write(f"**{next_event.title}**")
    st.write(f"{next_event.event_date.strftime('%d/%m/%Y')} · {next_event.event_time} · {next_event.place}")
    st.caption("Confirma tu disponibilidad en la pestaña Agenda.")
  else:
    st.info("Aún no hay actuaciones programadas. Administración puede crear la primera desde su pestaña.")
  if user.role == "admin":
    st.success("Tienes acceso de administración en este entorno de pruebas.")


def _admin_tab(engine, user: User):
  if user.role != "admin":
    st.info("Esta zona está reservada para administración.")
    return
  st.subheader("Administración")
  with st.form("event"):
    title = st.text_input("Título de la actuación")
    place = st.text_input("Lugar")
    event_date = st.date_input("Fecha", dt.date.today())
    event_time = st.text_input("Hora", "19:00")
    status = st.selectbox("Estado", ["EVALUACION", "CONFIRMADA", "STANDBY"])
    create = st.form_submit_button("Crear actuación", use_container_width=True)
  if create:
    if not title.strip() or not place.strip():
      st.error("Indica título y lugar.")
    else:
      with Session(engine) as db:
        event = Event(title=title.strip(), place=place.strip(), event_date=event_date, event_time=event_time.strip(), status=status)
        db.add(event)
        db.commit()
        db.refresh(event)
        ok, error, column = _sync_event(event)
        event.sync_status = "synced" if ok else "pending"
        event.sync_error = error
        event.sheet_column = column
        db.commit()
      if ok:
        st.success("Actuación guardada y sincronizada con Google Sheets.")
      else:
        st.warning(error)
  st.divider()
  with Session(engine) as db:
    pending = db.scalars(select(Event).where(Event.sync_status != "synced")).all()
  if pending:
    st.warning("Hay actuaciones pendientes de sincronizar. No se han perdido: siguen guardadas en la base de datos.")
    if st.button("Reintentar sincronización de actuaciones", use_container_width=True):
      with Session(engine) as db:
        for event in db.scalars(select(Event).where(Event.sync_status != "synced")).all():
          ok, error, column = _sync_event(event)
          event.sync_status = "synced" if ok else "pending"
          event.sync_error = error
          event.sheet_column = column or event.sheet_column
        db.commit()
      st.rerun()
  with Session(engine) as db:
    expenses = db.scalars(select(Expense).where(Expense.reimbursed.is_(False)).order_by(Expense.expense_date)).all()
  if expenses:
    st.subheader("Gastos pendientes de abono")
    for expense in expenses:
      label = f"{expense.expense_date.strftime('%d/%m/%Y')} · {expense.concept} · {expense.amount:.2f} €"
      if st.button(f"Marcar abonado · {label}", key=f"reimbursed-{expense.id}"):
        with Session(engine) as db:
          record = db.get(Expense, expense.id)
          if record:
            record.reimbursed = True
            db.commit()
        st.rerun()


def run():
  st.markdown("""
  <style>
    .block-container {max-width: 860px; padding-top: 1.4rem; padding-bottom: 2rem;}
    [data-testid="stMetric"] {background: #f6f7fb; border: 1px solid #e4e6ee; border-radius: 12px; padding: .65rem;}
    [data-testid="stTabs"] button {font-size: .96rem; padding: .45rem .7rem;}
    @media (max-width: 640px) {
      .block-container {padding-left: 1rem; padding-right: 1rem;}
      [data-testid="stMetricValue"] {font-size: 1.4rem;}
    }
  </style>
  """, unsafe_allow_html=True)
  engine, error = _setup_database()
  if error:
    st.title("Safara Gastos · preparación de pruebas")
    st.error(error)
    st.info("La aplicación ya no usará archivos locales. Configura la base de datos y el administrador inicial en los secretos de Streamlit para activar este entorno.")
    return
  user = _current_user(engine)
  if not user:
    _login_screen(engine)
    return
  st.sidebar.write(f"Sesión: {user.name}")
  if st.sidebar.button("Salir"):
    st.session_state.pop("secure_user_id", None)
    st.rerun()
  st.title("Safara Gastos")
  st.caption("Entorno de pruebas · datos separados de la aplicación oficial")
  tab_home, tab_events, tab_expenses, tab_messages, tab_admin = st.tabs(["Inicio", "Agenda", "Gastos", "Sugerencias", "Administración"])
  with tab_home:
    _home_tab(engine, user)
  with tab_events:
    _event_tab(engine, user)
  with tab_expenses:
    _expenses_tab(engine, user)
  with tab_messages:
    _messages_tab(engine, user)
  with tab_admin:
    _admin_tab(engine, user)
