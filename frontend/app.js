// Vitta - lógica del frontend (consume la API Flask)
const $ = s => document.querySelector(s);
const money = n => "$" + Number(n).toLocaleString("es-CO");
const esc = s => String(s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

// ---------- comunicación con la API ----------
async function api(ruta, metodo = "GET", cuerpo) {
  const r = await fetch("/api/" + ruta, {
    method: metodo,
    headers: cuerpo ? { "Content-Type": "application/json" } : {},
    body: cuerpo ? JSON.stringify(cuerpo) : undefined
  });
  if (r.status === 401) { location.href = "login.html"; throw new Error("Sesión no iniciada"); }
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.error || "Error del servidor");
  return data;
}

function aviso(msg, ok = false) {
  const el = $("#aviso");
  el.textContent = msg;
  el.className = "aviso " + (ok ? "ok" : "err");
  clearTimeout(aviso.t);
  aviso.t = setTimeout(() => (el.className = "aviso hidden"), 3500);
}
async function intentar(fn) { try { await fn(); } catch (e) { aviso(e.message); } }

// ---------- carga y pintado de datos ----------
async function cargarResumen() {
  const r = await api("resumen");
  $("#kpi-tareas").textContent = r.tareas_pendientes;
  $("#kpi-saldo").textContent = money(r.saldo);
  $("#kpi-rec").textContent = r.proximos.length;
  const pct = r.tareas_total ? Math.round(r.tareas_hechas / r.tareas_total * 100) : 0;
  $("#progreso").style.width = pct + "%";
  $("#progreso-txt").textContent = pct + "% completado (" + r.tareas_hechas + " de " + r.tareas_total + ")";
  const max = Math.max(1, ...Object.values(r.por_categoria));
  $("#grafico").innerHTML = Object.entries(r.por_categoria).map(([c, v]) =>
    `<div class="bar-row"><span class="lbl">${esc(c)}</span><div class="b" style="width:${v / max * 60}%"></div><span>${money(v)}</span></div>`
  ).join("") || "<small>Sin gastos registrados</small>";
  $("#proximos").innerHTML = r.proximos.map(p => `<li><span>${esc(p.texto)}</span><span>${esc(p.fecha)}</span></li>`).join("") || "<li><small>Sin recordatorios próximos</small></li>";
}

async function cargarTareas() {
  const lista = await api("tareas");
  $("#lista-tareas").innerHTML = lista.map(t =>
    `<li class="${t.completada ? "hecha" : ""}"><span>${esc(t.titulo)} <em class="badge ${t.prioridad}">${t.prioridad}</em> ${t.fecha_limite ? esc(t.fecha_limite) : ""}</span>
     <span><button data-ok="${t.id}" data-v="${t.completada ? 0 : 1}" title="Completar">✓</button> <button data-edit="${t.id}" data-t="${esc(t.titulo)}" title="Editar">✎</button> <button data-del="${t.id}" title="Eliminar">✕</button></span></li>`
  ).join("") || "<li><small>No hay tareas todavía</small></li>";
}

async function cargarMovs() {
  const lista = await api("movimientos");
  $("#lista-mov").innerHTML = lista.map(m =>
    `<li><span>${esc(m.descripcion)} · ${esc(m.categoria)} · ${esc(m.fecha)}</span>
     <span><b>${m.tipo === "gasto" ? "-" : "+"}${money(m.monto)}</b> <button data-delm="${m.id}" title="Eliminar">✕</button></span></li>`
  ).join("") || "<li><small>No hay movimientos todavía</small></li>";
}

async function cargarRecs() {
  const lista = await api("recordatorios");
  $("#lista-rec").innerHTML = lista.map(r =>
    `<li><span>${esc(r.texto)}</span><span>${esc(r.fecha)} <button data-delr="${r.id}" title="Eliminar">✕</button></span></li>`
  ).join("") || "<li><small>No hay recordatorios todavía</small></li>";
}

const refrescar = () => Promise.all([cargarResumen(), cargarTareas(), cargarMovs(), cargarRecs()]);

// ---------- formularios (con validaciones básicas) ----------
$("#form-tarea").onsubmit = e => { e.preventDefault(); intentar(async () => {
  const titulo = $("#t-texto").value.trim();
  if (!titulo) throw new Error("Escribe el título de la tarea");
  await api("tareas", "POST", { titulo, prioridad: $("#t-prio").value, fecha_limite: $("#t-fecha").value || null });
  e.target.reset(); await refrescar(); aviso("Tarea agregada", true);
}); };

$("#form-mov").onsubmit = e => { e.preventDefault(); intentar(async () => {
  const descripcion = $("#m-desc").value.trim(), monto = parseFloat($("#m-monto").value);
  if (!descripcion) throw new Error("Escribe una descripción");
  if (!(monto > 0)) throw new Error("El monto debe ser mayor que 0");
  await api("movimientos", "POST", { descripcion, monto, tipo: $("#m-tipo").value, categoria: $("#m-cat").value });
  e.target.reset(); await refrescar(); aviso("Movimiento registrado", true);
}); };

$("#form-rec").onsubmit = e => { e.preventDefault(); intentar(async () => {
  const texto = $("#r-texto").value.trim(), fecha = $("#r-fecha").value;
  if (!texto) throw new Error("Escribe el pago o evento");
  if (!fecha) throw new Error("Elige la fecha del recordatorio");
  await api("recordatorios", "POST", { texto, fecha });
  e.target.reset(); await refrescar(); aviso("Recordatorio agregado", true);
}); };

// ---------- acciones en las listas ----------
document.addEventListener("click", e => {
  const d = e.target.dataset;
  if (d.ok) intentar(async () => { await api("tareas/" + d.ok, "PATCH", { completada: d.v === "1" }); await refrescar(); });
  if (d.edit) intentar(async () => {
    const nuevo = prompt("Editar tarea:", d.t);
    if (nuevo === null) return;
    await api("tareas/" + d.edit, "PATCH", { titulo: nuevo }); await refrescar();
  });
  if (d.del) intentar(async () => { if (confirm("¿Eliminar la tarea?")) { await api("tareas/" + d.del, "DELETE"); await refrescar(); } });
  if (d.delm) intentar(async () => { if (confirm("¿Eliminar el movimiento?")) { await api("movimientos/" + d.delm, "DELETE"); await refrescar(); } });
  if (d.delr) intentar(async () => { if (confirm("¿Eliminar el recordatorio?")) { await api("recordatorios/" + d.delr, "DELETE"); await refrescar(); } });
});

// ---------- sesión y navegación ----------
$("#salir").onclick = async () => { await fetch("/api/logout", { method: "POST" }); location.href = "login.html"; };
$("#fecha").textContent = new Date().toLocaleDateString("es-CO", { weekday: "long", day: "numeric", month: "long" });

const titulos = { resumen: "Resumen del día", tareas: "Tareas", finanzas: "Finanzas", recordatorios: "Recordatorios", asistente: "Asistente IA" };
function ir() {
  const id = (location.hash || "#resumen").slice(1);
  document.querySelectorAll(".view").forEach(v => v.classList.toggle("hidden", v.id !== id));
  document.querySelectorAll(".menu a").forEach(a => a.classList.toggle("active", a.getAttribute("href") === "#" + id));
  $("#titulo").textContent = titulos[id] || "Vitta";
}
window.addEventListener("hashchange", ir);

// ---------- asistente IA (vista previa, red neuronal en el navegador) ----------
$("#ia-btn").onclick = () => {
  const r = predecir($("#ia-texto").value);
  $("#ia-res").innerHTML = r ? r.map(x => `<div class="ia-item"><span style="width:90px">${x.cat}</span><div class="b" style="width:${x.p * 60}%"></div><span>${(x.p * 100).toFixed(0)}%</span></div>`).join("")
    : "<small>No reconozco esas palabras, prueba con otras.</small>";
};

// ---------- inicio ----------
(async () => {
  await intentar(async () => { $("#usuario").textContent = (await api("me")).nombre; });
  ir();
  intentar(refrescar);
})();
