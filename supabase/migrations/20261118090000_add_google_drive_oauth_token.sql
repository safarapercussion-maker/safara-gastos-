-- Guarda exclusivamente el permiso renovable de Drive, cifrado por la aplicación.
-- La clave de descifrado nunca entra en la base de datos ni en GitHub.

create table safara.google_drive_oauth (
  id smallint primary key default 1 check (id = 1),
  token_cifrado text not null,
  autorizado_por uuid references safara.usuarios(id) on delete set null,
  actualizado_en timestamptz not null default now()
);

alter table safara.google_drive_oauth enable row level security;

create policy google_drive_oauth_sin_acceso_directo
on safara.google_drive_oauth
as restrictive
for all
to anon, authenticated
using (false)
with check (false);
