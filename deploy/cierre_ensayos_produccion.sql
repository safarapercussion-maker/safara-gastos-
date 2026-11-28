-- Aplicar solo en el proyecto de producción, después de las migraciones versionadas.
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
  if ahora_madrid < lunes_candidato + 4 + time '19:30' then
    lunes_candidato := lunes_candidato - 7;
  end if;
  if not exists (
    select 1 from safara.usuarios
    where (creado_en at time zone 'Europe/Madrid')::date <= lunes_candidato + 4
  ) then
    return;
  end if;

  ciclo := to_char(lunes_candidato, 'IYYY-"W"IW');
  perform pg_advisory_xact_lock(hashtext('safara-weekly-rehearsal'));
  perform pg_advisory_xact_lock(hashtext('safara-weekly-rehearsal-plan'));
  select ubicacion, estado, motivo_pausa
    into ubicacion_plan, estado_plan, motivo_plan
    from safara.ensayos_planificacion where ciclo_id = ciclo;

  if not found then
    select case ubicacion
             when 'Gaztetxe de Zizur' then 'Baragazte (Barañain)'
             when 'Baragazte (Barañain)' then 'Gaztetxe de Zizur'
             else case when ((lunes_candidato - date '2026-11-16') / 7) % 2 = 0
                then 'Gaztetxe de Zizur' else 'Baragazte (Barañain)' end
           end into ubicacion_plan
      from safara.ensayos_planificacion
     where lunes < lunes_candidato and estado = 'ACTIVO'
     order by lunes desc limit 1;
    if not found then
      ubicacion_plan := case when ((lunes_candidato - date '2026-11-16') / 7) % 2 = 0
        then 'Gaztetxe de Zizur' else 'Baragazte (Barañain)' end;
    end if;
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
    (ciclo, lunes_candidato + 4, time '19:30', ubicacion_plan, resultado,
     coalesce(motivo_plan, ''), asistentes, repenikes, cajas)
  on conflict (ciclo_id) do nothing;
end;
$$;

revoke all on function safara.cerrar_ensayos_vencidos() from public;
