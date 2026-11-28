-- Referencia visible, estable y consecutiva por ejercicio fiscal.
-- El id numérico histórico no cambia: sigue siendo la clave técnica interna.

alter table safara.gastos
  add column if not exists referencia_anual text;

with referencias as (
  select id,
         extract(year from fecha)::integer::text || '-' ||
         lpad(row_number() over (
           partition by extract(year from fecha)::integer
           order by fecha, id
         )::text, 3, '0') as referencia
  from safara.gastos
  where referencia_anual is null
)
update safara.gastos gastos
set referencia_anual = referencias.referencia
from referencias
where gastos.id = referencias.id;

alter table safara.gastos
  alter column referencia_anual set not null;

alter table safara.gastos
  drop constraint if exists gastos_referencia_anual_formato;

alter table safara.gastos
  add constraint gastos_referencia_anual_formato
  check (referencia_anual ~ '^[0-9]{4}-[0-9]{3,}$');

create unique index if not exists gastos_referencia_anual_unica_idx
  on safara.gastos (referencia_anual);

-- Obliga a regenerar la vista de Google tras la migración de referencias.
update safara.mantenimiento
set sheets_revision = sheets_revision + 1,
    bloqueado_hasta = null,
    proximo_intento_en = null,
    actualizado_en = now()
where clave = 'integracion_google';
