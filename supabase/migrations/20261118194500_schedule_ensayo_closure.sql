-- Cierre autónomo: no depende de que una persona abra Streamlit el viernes.
-- La función calcula siempre la hora local de Madrid; la base permanece en UTC.

create extension if not exists pg_cron with schema pg_catalog;

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
  asistentes integer;
  repenikes integer;
  cajas integer;
  resultado text;
begin
  lunes_candidato := date_trunc('week', ahora_madrid)::date;
  if ahora_madrid < lunes_candidato + 4 + time '19:00' then
    lunes_candidato := lunes_candidato - 7;
  end if;

  -- No fabricar historial anterior a la puesta en marcha de esta fase.
  if lunes_candidato < date '2026-11-16' then
    return;
  end if;

  ciclo := to_char(lunes_candidato, 'IYYY-"W"IW');
  select count(*)::integer,
         count(*) filter (where u.instrumento = 'Repenike')::integer,
         count(*) filter (where u.instrumento = 'Caja')::integer
    into asistentes, repenikes, cajas
    from safara.votos v
    join safara.usuarios u on u.id = v.usuario_id and u.activo
   where v.encuesta_id = 'ensayo_proximo'
     and v.ciclo_id = ciclo
     and v.respuesta = 'SI';

  resultado := case
    when asistentes >= 6 and repenikes >= 1 and cajas >= 1 then 'CONFIRMADO'
    else 'NO_REALIZADO'
  end;

  insert into safara.ensayos_historial
    (ciclo_id, fecha, hora_cierre, ubicacion, estado,
     asistentes_confirmados, repenikes_confirmados, cajas_confirmadas)
  values
    (ciclo, lunes_candidato + 4, time '19:00',
     case when ((lunes_candidato - date '2026-11-16') / 7) % 2 = 0
          then 'Gaztetxe de Zizur' else 'Baragazte (Barañain)' end,
     resultado, asistentes, repenikes, cajas)
  on conflict (ciclo_id) do nothing;
end;
$$;

revoke all on function safara.cerrar_ensayos_vencidos() from public;

select cron.schedule(
  'safara-cierre-semanal-ensayos',
  '*/5 17-20 * * 5',
  $$select safara.cerrar_ensayos_vencidos();$$
);
