-- Red de seguridad para despliegues escalonados.
-- Si una instancia anterior de la app registra un gasto sin referencia anual,
-- la base la completa de forma transaccional antes de validar el registro.

create or replace function safara.asignar_referencia_anual_gasto()
returns trigger
language plpgsql
set search_path = safara, pg_temp
as $$
declare
  ejercicio integer;
  siguiente integer;
begin
  if new.referencia_anual is null or btrim(new.referencia_anual) = '' then
    ejercicio := extract(year from new.fecha)::integer;
    perform pg_advisory_xact_lock(hashtext('safara-gastos-referencia-' || ejercicio::text));
    select coalesce(max(split_part(referencia_anual, '-', 2)::integer), 0) + 1
      into siguiente
      from safara.gastos
     where referencia_anual like ejercicio::text || '-%';
    new.referencia_anual := ejercicio::text || '-' || lpad(siguiente::text, 3, '0');
  end if;
  return new;
end;
$$;

drop trigger if exists asignar_referencia_anual_gasto on safara.gastos;

create trigger asignar_referencia_anual_gasto
before insert on safara.gastos
for each row execute function safara.asignar_referencia_anual_gasto();

revoke all on function safara.asignar_referencia_anual_gasto() from public;
