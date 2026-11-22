"""Vitta - API Flask + SQLite. Sirve también el frontend estático."""
import os
import sqlite3
from datetime import date
from functools import wraps

from flask import Flask, jsonify, request, send_from_directory, session
from werkzeug.security import check_password_hash, generate_password_hash

import asistente
import db
import validaciones as v

FRONTEND = os.path.join(os.path.dirname(__file__), "..", "frontend")
app = Flask(__name__, static_folder=FRONTEND, static_url_path="")
app.secret_key = os.environ.get("VITTA_SECRET", "clave-de-desarrollo-cambiar")
app.teardown_appcontext(db.close_db)


# ---------- utilidades ----------
def error(mensaje, codigo=400):
    return jsonify(error=mensaje), codigo


def login_required(f):
    @wraps(f)
    def interior(*args, **kwargs):
        if "uid" not in session:
            return error("Debes iniciar sesión", 401)
        return f(*args, **kwargs)
    return interior


def datos():
    return request.get_json(silent=True) or {}


@app.errorhandler(ValueError)
def valor_invalido(e):
    return error(str(e), 400)


@app.route("/")
def inicio():
    return send_from_directory(FRONTEND, "index.html")


# ---------- autenticación ----------
@app.post("/api/registro")
def registro():
    d = datos()
    nombre = v.texto(d.get("nombre"), "El nombre", 2, 60)
    correo = v.email(d.get("email"))
    clave = v.clave(d.get("password"))
    try:
        cur = db.get_db().execute(
            "INSERT INTO usuarios (nombre, email, password_hash) VALUES (?,?,?)",
            (nombre, correo, generate_password_hash(clave)))
        db.get_db().commit()
    except sqlite3.IntegrityError:
        return error("Ese correo ya está registrado", 409)
    session["uid"], session["nombre"] = cur.lastrowid, nombre
    return jsonify(nombre=nombre), 201


@app.post("/api/login")
def login():
    d = datos()
    fila = db.get_db().execute(
        "SELECT * FROM usuarios WHERE email = ?",
        ((d.get("email") or "").strip().lower(),)).fetchone()
    if not fila or not check_password_hash(fila["password_hash"], d.get("password") or ""):
        return error("Correo o contraseña incorrectos", 401)
    session["uid"], session["nombre"] = fila["id"], fila["nombre"]
    return jsonify(nombre=fila["nombre"])


@app.post("/api/logout")
def logout():
    session.clear()
    return jsonify(ok=True)


@app.get("/api/me")
@login_required
def me():
    return jsonify(nombre=session["nombre"])


# ---------- tareas ----------
def fila_tarea(r):
    return {"id": r["id"], "titulo": r["titulo"], "prioridad": r["prioridad"],
            "fecha_limite": r["fecha_limite"], "completada": bool(r["completada"])}


@app.get("/api/tareas")
@login_required
def listar_tareas():
    filas = db.get_db().execute(
        "SELECT * FROM tareas WHERE usuario_id=? "
        "ORDER BY completada, fecha_limite IS NULL, fecha_limite, id", (session["uid"],)).fetchall()
    return jsonify([fila_tarea(r) for r in filas])


@app.post("/api/tareas")
@login_required
def crear_tarea():
    d = datos()
    titulo = v.texto(d.get("titulo"), "El título")
    prioridad = v.opcion(d.get("prioridad", "Media"), v.PRIORIDADES, "La prioridad")
    limite = v.fecha(d.get("fecha_limite"), "La fecha límite")
    conn = db.get_db()
    cur = conn.execute(
        "INSERT INTO tareas (usuario_id, titulo, prioridad, fecha_limite) VALUES (?,?,?,?)",
        (session["uid"], titulo, prioridad, limite))
    conn.commit()
    return jsonify(id=cur.lastrowid), 201


@app.patch("/api/tareas/<int:tid>")
@login_required
def editar_tarea(tid):
    conn = db.get_db()
    t = conn.execute("SELECT * FROM tareas WHERE id=? AND usuario_id=?", (tid, session["uid"])).fetchone()
    if not t:
        return error("Tarea no encontrada", 404)
    d = datos()
    titulo = v.texto(d["titulo"], "El título") if "titulo" in d else t["titulo"]
    completada = int(bool(d["completada"])) if "completada" in d else t["completada"]
    conn.execute("UPDATE tareas SET titulo=?, completada=? WHERE id=?", (titulo, completada, tid))
    conn.commit()
    return jsonify(ok=True)


@app.delete("/api/tareas/<int:tid>")
@login_required
def borrar_tarea(tid):
    conn = db.get_db()
    cur = conn.execute("DELETE FROM tareas WHERE id=? AND usuario_id=?", (tid, session["uid"]))
    conn.commit()
    return jsonify(ok=True) if cur.rowcount else error("Tarea no encontrada", 404)


# ---------- finanzas ----------
@app.get("/api/movimientos")
@login_required
def listar_movimientos():
    filas = db.get_db().execute(
        "SELECT * FROM movimientos WHERE usuario_id=? ORDER BY fecha DESC, id DESC",
        (session["uid"],)).fetchall()
    return jsonify([dict(r) for r in filas])


@app.post("/api/movimientos")
@login_required
def crear_movimiento():
    d = datos()
    desc = v.texto(d.get("descripcion"), "La descripción")
    valor = v.monto(d.get("monto"))
    tipo = v.opcion(d.get("tipo"), v.TIPOS, "El tipo")
    cat = v.opcion(d.get("categoria"), v.CATEGORIAS, "La categoría")
    dia = v.fecha(d.get("fecha")) or date.today().isoformat()
    conn = db.get_db()
    cur = conn.execute(
        "INSERT INTO movimientos (usuario_id, descripcion, monto, tipo, categoria, fecha) VALUES (?,?,?,?,?,?)",
        (session["uid"], desc, valor, tipo, cat, dia))
    conn.commit()
    return jsonify(id=cur.lastrowid), 201


@app.delete("/api/movimientos/<int:mid>")
@login_required
def borrar_movimiento(mid):
    conn = db.get_db()
    cur = conn.execute("DELETE FROM movimientos WHERE id=? AND usuario_id=?", (mid, session["uid"]))
    conn.commit()
    return jsonify(ok=True) if cur.rowcount else error("Movimiento no encontrado", 404)


# ---------- recordatorios ----------
@app.get("/api/recordatorios")
@login_required
def listar_recordatorios():
    filas = db.get_db().execute(
        "SELECT * FROM recordatorios WHERE usuario_id=? ORDER BY fecha, id", (session["uid"],)).fetchall()
    return jsonify([dict(r) for r in filas])


@app.post("/api/recordatorios")
@login_required
def crear_recordatorio():
    d = datos()
    txt = v.texto(d.get("texto"), "El texto")
    dia = v.fecha(d.get("fecha"), "La fecha", obligatoria=True)
    conn = db.get_db()
    cur = conn.execute("INSERT INTO recordatorios (usuario_id, texto, fecha) VALUES (?,?,?)",
                       (session["uid"], txt, dia))
    conn.commit()
    return jsonify(id=cur.lastrowid), 201


@app.delete("/api/recordatorios/<int:rid>")
@login_required
def borrar_recordatorio(rid):
    conn = db.get_db()
    cur = conn.execute("DELETE FROM recordatorios WHERE id=? AND usuario_id=?", (rid, session["uid"]))
    conn.commit()
    return jsonify(ok=True) if cur.rowcount else error("Recordatorio no encontrado", 404)


# ---------- resumen ----------
@app.get("/api/resumen")
@login_required
def resumen():
    conn, uid = db.get_db(), session["uid"]
    hoy = date.today().isoformat()
    t = conn.execute("SELECT COUNT(*) total, COALESCE(SUM(completada),0) hechas FROM tareas WHERE usuario_id=?", (uid,)).fetchone()
    ing = conn.execute("SELECT COALESCE(SUM(monto),0) FROM movimientos WHERE usuario_id=? AND tipo='ingreso'", (uid,)).fetchone()[0]
    gas = conn.execute("SELECT COALESCE(SUM(monto),0) FROM movimientos WHERE usuario_id=? AND tipo='gasto'", (uid,)).fetchone()[0]
    por_cat = {r["categoria"]: r["total"] for r in conn.execute(
        "SELECT categoria, SUM(monto) total FROM movimientos WHERE usuario_id=? AND tipo='gasto' GROUP BY categoria", (uid,))}
    proximos = [dict(r) for r in conn.execute(
        "SELECT texto, fecha FROM recordatorios WHERE usuario_id=? AND fecha>=? ORDER BY fecha LIMIT 5", (uid, hoy))]
    return jsonify(tareas_total=t["total"], tareas_hechas=t["hechas"],
                   tareas_pendientes=t["total"] - t["hechas"],
                   ingresos=ing, gastos=gas, saldo=ing - gas,
                   por_categoria=por_cat, proximos=proximos)


# ---------- asistente IA ----------
@app.post("/api/asistente")
@login_required
def asistente_chat():
    d = datos()
    try:
        texto = asistente.responder(session["uid"], session["nombre"], d.get("mensaje"), d.get("historial"))
    except asistente.AsistenteNoDisponible as e:
        return error(str(e), 503)
    return jsonify(respuesta=texto)


if __name__ == "__main__":
    db.init_db()
    app.run(debug=True)
