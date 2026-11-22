-- Puntuación de asistencia basada exclusivamente en confirmaciones de voto.
-- La fecha de activación evita sumar puntos de votos anteriores a este modelo.

create table if not exists safara.puntuacion_asistencia_configuracion (
  clave text primary key check (clave = 'votos_confirmados_desde'),
  activada_en timestamptz not null,
  creado_en timestamptz not null default now()
);

insert into safara.puntuacion_asistencia_configuracion (clave, activada_en)
values ('votos_confirmados_desde', now())
on conflict (clave) do nothing;

-- Una votación sólo puede contarse si sigue siendo afirmativa. Por tanto, si
-- alguien cambia a «No puedo», desaparece automáticamente de su puntuación.
create index if not exists votos_compromiso_asistencia_idx
  on safara.votos (usuario_id, encuesta_id, actualizado_en)
  where respuesta = 'SI';

alter table safara.puntuacion_asistencia_configuracion enable row level security;
revoke all on table safara.puntuacion_asistencia_configuracion from anon, authenticated;
grant select, insert, update, delete on table safara.puntuacion_asistencia_configuracion to service_role;

drop policy if exists puntuacion_asistencia_configuracion_sin_acceso_directo
  on safara.puntuacion_asistencia_configuracion;
create policy puntuacion_asistencia_configuracion_sin_acceso_directo
  on safara.puntuacion_asistencia_configuracion
  as restrictive
  for all
  to anon, authenticated
  using (false)
  with check (false);
