-- Planificación semanal, pausas y asistencia confirmada de ensayos.
-- Supabase es la fuente de verdad; Streamlit únicamente administra estas reglas.

create table if not exists safara.ensayos_planificacion (
  ciclo_id text primary key check (length(btrim(ciclo_id)) between 2 and 180),
  lunes date not null unique,
  ubicacion text not null check (length(btrim(ubicacion)) between 2 and 180),
  estado text not null default 'ACTIVO' check (estado in ('ACTIVO', 'PAUSADO')),
  motivo_pausa text not null default '' check (length(motivo_pausa) <= 500),
  actualizado_por uuid references safara.usuarios(id),
  actualizado_en timestamptz not null default now()
);

alter table safara.ensayos_historial
  add column if not exists motivo text not null default '' check (length(motivo) <= 500);

alter table safara.ensayos_historial
  drop constraint if exists ensayos_historial_estado_check;

alter table safara.ensayos_historial
  add constraint ensayos_historial_estado_check
  check (estado in ('CONFIRMADO', 'NO_REALIZADO', 'PAUSADO'));

create table if not exists safara.ensayos_asistencias (
  ciclo_id text not null references safara.ensayos_historial(ciclo_id) on delete restrict,
  usuario_id uuid not null references safara.usuarios(id) on delete restrict,
  confirmado_por uuid not null references safara.usuarios(id) on delete restrict,
  confirmado_en timestamptz not null default now(),
  primary key (ciclo_id, usuario_id)
);

create index if not exists ensayos_planificacion_lunes_idx
  on safara.ensayos_planificacion (lunes desc);
create index if not exists ensayos_asistencias_usuario_idx
  on safara.ensayos_asistencias (usuario_id, ciclo_id);

alter table safara.ensayos_planificacion enable row level security;
alter table safara.ensayos_asistencias enable row level security;

drop policy if exists ensayos_planificacion_sin_acceso_directo on safara.ensayos_planificacion;
create policy ensayos_planificacion_sin_acceso_directo
on safara.ensayos_planificacion as restrictive for all to anon, authenticated
using (false) with check (false);

drop policy if exists ensayos_asistencias_sin_acceso_directo on safara.ensayos_asistencias;
create policy ensayos_asistencias_sin_acceso_directo
on safara.ensayos_asistencias as restrictive for all to anon, authenticated
using (false) with check (false);

create or replace function safara.cerrar_ensayos_vencidos()
returns void
language plpgsql
security definer
set search_path = safara, pg_temp
as $$
declare
  ahora_madrid timestamp := now() at time zone 'Europe/Madrid';
  lunes_candidato date;
  ciclo text;
  asistentes integer := 0;
  repenikes integer := 0;
  cajas integer := 0;
  resultado text;
  ubicacion_plan text;
  estado_plan text;
  motivo_plan text;
begin
  lunes_candidato := date_trunc('week', ahora_madrid)::date;
  if ahora_madrid < lunes_candidato + 4 + time '19:00' then
    lunes_candidato := lunes_candidato - 7;
  end if;
  if lunes_candidato < date '2026-11-16' then
    return;
  end if;

  ciclo := to_char(lunes_candidato, 'IYYY-"W"IW');
  perform pg_advisory_xact_lock(hashtext('safara-weekly-rehearsal'));
  select ubicacion, estado, motivo_pausa
    into ubicacion_plan, estado_plan, motivo_plan
    from safara.ensayos_planificacion where ciclo_id = ciclo;

  if not found then
    ubicacion_plan := case when ((lunes_candidato - date '2026-11-16') / 7) % 2 = 0
      then 'Gaztetxe de Zizur' else 'Baragazte (Barañain)' end;
    estado_plan := 'ACTIVO';
    motivo_plan := '';
    insert into safara.ensayos_planificacion (ciclo_id, lunes, ubicacion)
    values (ciclo, lunes_candidato, ubicacion_plan)
    on conflict (ciclo_id) do nothing;
  end if;

  if estado_plan = 'PAUSADO' then
    resultado := 'PAUSADO';
  else
    select count(*)::integer,
           count(*) filter (where u.instrumento = 'Repenike')::integer,
           count(*) filter (where u.instrumento = 'Caja')::integer
      into asistentes, repenikes, cajas
      from safara.votos v
      join safara.usuarios u on u.id = v.usuario_id and u.activo
     where v.encuesta_id = 'ensayo_proximo'
       and v.ciclo_id = ciclo and v.respuesta = 'SI';
    resultado := case
      when asistentes >= 6 and repenikes >= 1 and cajas >= 1 then 'CONFIRMADO'
      else 'NO_REALIZADO'
    end;
  end if;

  insert into safara.ensayos_historial
    (ciclo_id, fecha, hora_cierre, ubicacion, estado, motivo,
     asistentes_confirmados, repenikes_confirmados, cajas_confirmadas)
  values
    (ciclo, lunes_candidato + 4, time '19:00', ubicacion_plan, resultado,
     coalesce(motivo_plan, ''), asistentes, repenikes, cajas)
  on conflict (ciclo_id) do nothing;
end;
$$;

revoke all on function safara.cerrar_ensayos_vencidos() from public;
