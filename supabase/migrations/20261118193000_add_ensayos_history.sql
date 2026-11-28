-- Historial inmutable de cierres semanales de ensayo. Los votos continúan en
-- safara.votos; esta tabla conserva el resultado oficial de cada semana.

create table safara.ensayos_historial (
  ciclo_id text primary key check (length(btrim(ciclo_id)) between 2 and 180),
  fecha date not null,
  hora_cierre time not null,
  ubicacion text not null check (length(btrim(ubicacion)) between 2 and 180),
  estado text not null check (estado in ('CONFIRMADO', 'NO_REALIZADO')),
  asistentes_confirmados integer not null check (asistentes_confirmados >= 0),
  repenikes_confirmados integer not null check (repenikes_confirmados >= 0),
  cajas_confirmadas integer not null check (cajas_confirmadas >= 0),
  cerrado_en timestamptz not null default now()
);

create index ensayos_historial_fecha_idx on safara.ensayos_historial (fecha desc);
create index google_drive_oauth_autorizado_por_idx
  on safara.google_drive_oauth (autorizado_por);

alter table safara.ensayos_historial enable row level security;

create policy ensayos_historial_sin_acceso_directo
on safara.ensayos_historial
as restrictive
for all
to anon, authenticated
using (false)
with check (false);
