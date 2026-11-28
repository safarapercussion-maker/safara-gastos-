-- Los gastos se confirman en Supabase antes de intentar Drive. Si Google está
-- temporalmente indisponible, el ticket queda cifrado por el canal privado de
-- base de datos hasta que una persona administradora lo reintente.

alter table safara.google_drive_oauth
  add column if not exists carpeta_id text;

alter table safara.gastos
  add column if not exists estado_justificante text not null default 'PENDIENTE_DRIVE'
  check (estado_justificante in ('PENDIENTE_DRIVE', 'GUARDADO'));

create index if not exists gastos_estado_justificante_idx
  on safara.gastos (estado_justificante, creado_en asc);

create table if not exists safara.justificantes_pendientes (
  gasto_id bigint primary key references safara.gastos(id) on delete cascade,
  contenido bytea not null check (octet_length(contenido) between 1 and 10485760),
  nombre_fichero text not null check (length(btrim(nombre_fichero)) between 1 and 255),
  mime_type text check (mime_type in ('image/png', 'image/jpeg', 'application/pdf')),
  intentos integer not null default 0 check (intentos >= 0),
  ultimo_error text,
  creado_en timestamptz not null default now(),
  actualizado_en timestamptz not null default now()
);

create trigger justificantes_pendientes_actualizado_en
before update on safara.justificantes_pendientes
for each row execute function safara.establecer_actualizado_en();

alter table safara.justificantes_pendientes enable row level security;

create policy justificantes_pendientes_sin_acceso_directo
on safara.justificantes_pendientes
as restrictive
for all
to anon, authenticated
using (false)
with check (false);
