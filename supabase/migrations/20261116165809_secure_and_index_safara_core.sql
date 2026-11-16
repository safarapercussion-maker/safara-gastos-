Attempting to perform the InitializeDefaultDrives operation on the 'FileSystem' provider failed.
create index actuaciones_creado_por_idx on safara.actuaciones (creado_por);
create index auditoria_usuario_idx on safara.auditoria (usuario_id);
create index caja_actualizado_por_idx on safara.caja (actualizado_por);
create index confesionario_usuario_idx on safara.confesionario (usuario_id);
create index gastos_abonado_por_idx on safara.gastos (abonado_por);
create index invitaciones_emitido_por_idx on safara.invitaciones (emitido_por);
create index invitaciones_usado_por_idx on safara.invitaciones (usado_por);
create index votos_usuario_idx on safara.votos (usuario_id);

create policy "sin acceso directo a usuarios" on safara.usuarios for all to anon, authenticated using (false) with check (false);
create policy "sin acceso directo a invitaciones" on safara.invitaciones for all to anon, authenticated using (false) with check (false);
create policy "sin acceso directo a actuaciones" on safara.actuaciones for all to anon, authenticated using (false) with check (false);
create policy "sin acceso directo a votos" on safara.votos for all to anon, authenticated using (false) with check (false);
create policy "sin acceso directo a gastos" on safara.gastos for all to anon, authenticated using (false) with check (false);
create policy "sin acceso directo a confesionario" on safara.confesionario for all to anon, authenticated using (false) with check (false);
create policy "sin acceso directo a caja" on safara.caja for all to anon, authenticated using (false) with check (false);
create policy "sin acceso directo a auditoria" on safara.auditoria for all to anon, authenticated using (false) with check (false);

