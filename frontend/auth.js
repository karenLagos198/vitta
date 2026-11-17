// Inicio de sesión y registro (con validaciones básicas en el navegador)
const $ = s => document.querySelector(s);

function aviso(msg, ok = false) {
  const el = $("#aviso");
  el.textContent = msg;
  el.className = "aviso " + (ok ? "ok" : "err");
}

async function enviar(ruta, cuerpo) {
  const r = await fetch("/api/" + ruta, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(cuerpo)
  });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.error || "Error del servidor");
  return data;
}

function cambiar(login) {
  $("#form-login").classList.toggle("hidden", !login);
  $("#form-reg").classList.toggle("hidden", login);
  $("#tab-login").classList.toggle("active", login);
  $("#tab-reg").classList.toggle("active", !login);
  $("#aviso").className = "aviso hidden";
}
$("#tab-login").onclick = () => cambiar(true);
$("#tab-reg").onclick = () => cambiar(false);

const emailOk = e => /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(e);

$("#form-login").onsubmit = async e => {
  e.preventDefault();
  const email = $("#l-email").value.trim(), password = $("#l-pass").value;
  if (!emailOk(email)) return aviso("Escribe un correo válido");
  if (!password) return aviso("Escribe tu contraseña");
  try { await enviar("login", { email, password }); location.href = "index.html"; }
  catch (err) { aviso(err.message); }
};

$("#form-reg").onsubmit = async e => {
  e.preventDefault();
  const nombre = $("#r-nombre").value.trim(), email = $("#r-email").value.trim(), password = $("#r-pass").value;
  if (nombre.length < 2) return aviso("El nombre debe tener al menos 2 caracteres");
  if (!emailOk(email)) return aviso("Escribe un correo válido");
  if (password.length < 6) return aviso("La contraseña debe tener al menos 6 caracteres");
  try { await enviar("registro", { nombre, email, password }); location.href = "index.html"; }
  catch (err) { aviso(err.message); }
};
