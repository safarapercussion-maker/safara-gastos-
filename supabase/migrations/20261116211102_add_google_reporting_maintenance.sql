-- Control de sincronización segura de informes y copias administrativas.
-- Supabase conserva la fuente de verdad; Google recibe solo una vista de consulta.

create table safara.mantenimiento (
  clave text primary key check (clave = 'integracion_google'),
  sheets_revision bigint not null default 0,
  sheets_synced_revision bigint not null default 0,
  ultimo_respaldo date,
  bloqueado_hasta timestamptz,
  proximo_intento_en timestamptz,
  ultimo_error text,
  actualizado_en timestamptz not null default now()
);

insert into safara.mantenimiento (clave) values ('integracion_google');

create or replace function safara.marcar_informe_pendiente()
returns trigger
language plpgsql
security definer
set search_path = safara, pg_temp
as $$
begin
  update safara.mantenimiento
     set sheets_revision = sheets_revision + 1,
         actualizado_en = now()
   where clave = 'integracion_google';
  return null;
end;
$$;

create trigger usuarios_informe_pendiente
after insert or update or delete on safara.usuarios
for each statement execute function safara.marcar_informe_pendiente();

create trigger invitaciones_informe_pendiente
after insert or update or delete on safara.invitaciones
for each statement execute function safara.marcar_informe_pendiente();

create trigger actuaciones_informe_pendiente
after insert or update or delete on safara.actuaciones
for each statement execute function safara.marcar_informe_pendiente();

create trigger votos_informe_pendiente
after insert or update or delete on safara.votos
for each statement execute function safara.marcar_informe_pendiente();

create trigger gastos_informe_pendiente
after insert or update or delete on safara.gastos
for each statement execute function safara.marcar_informe_pendiente();

create trigger caja_informe_pendiente
after insert or update or delete on safara.caja
for each statement execute function safara.marcar_informe_pendiente();

create trigger auditoria_informe_pendiente
after insert or update or delete on safara.auditoria
for each statement execute function safara.marcar_informe_pendiente();

alter table safara.mantenimiento enable row level security;

create policy mantenimiento_sin_acceso_directo
on safara.mantenimiento
as restrictive
for all
to anon, authenticated
using (false)
with check (false);
