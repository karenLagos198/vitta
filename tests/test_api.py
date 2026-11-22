"""Pruebas básicas de la API. Ejecutar:  python -m unittest discover tests"""
import http.server
import json
import os
import sys
import tempfile
import threading
import unittest
from datetime import date, timedelta
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
import asistente  # noqa: E402
import db  # noqa: E402
import app as vitta  # noqa: E402


class ApiTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        db.DB_PATH = self.tmp.name
        db.init_db()
        self.c = vitta.app.test_client()
        self.c.post("/api/registro", json={"nombre": "Ana Prueba", "email": "ana@correo.com", "password": "secreto1"})

    def tearDown(self):
        os.unlink(self.tmp.name)

    def test_requiere_sesion(self):
        self.assertEqual(vitta.app.test_client().get("/api/tareas").status_code, 401)

    def test_registro_duplicado_y_validaciones(self):
        r = self.c.post("/api/registro", json={"nombre": "Otra", "email": "ana@correo.com", "password": "secreto1"})
        self.assertEqual(r.status_code, 409)
        r = self.c.post("/api/registro", json={"nombre": "X", "email": "malo", "password": "1"})
        self.assertEqual(r.status_code, 400)

    def test_login_incorrecto(self):
        r = vitta.app.test_client().post("/api/login", json={"email": "ana@correo.com", "password": "mala"})
        self.assertEqual(r.status_code, 401)

    def test_tareas_crud(self):
        self.assertEqual(self.c.post("/api/tareas", json={"titulo": "  "}).status_code, 400)
        self.assertEqual(self.c.post("/api/tareas", json={"titulo": "Estudiar", "prioridad": "Urgente"}).status_code, 400)
        r = self.c.post("/api/tareas", json={"titulo": "Estudiar", "prioridad": "Alta", "fecha_limite": "2026-12-01"})
        tid = r.get_json()["id"]
        self.c.patch(f"/api/tareas/{tid}", json={"completada": True})
        self.assertTrue(self.c.get("/api/tareas").get_json()[0]["completada"])
        self.assertEqual(self.c.delete(f"/api/tareas/{tid}").status_code, 200)
        self.assertEqual(self.c.get("/api/tareas").get_json(), [])

    def test_movimientos_y_resumen(self):
        self.assertEqual(self.c.post("/api/movimientos", json={"descripcion": "x", "monto": -5, "tipo": "gasto", "categoria": "Comida"}).status_code, 400)
        self.c.post("/api/movimientos", json={"descripcion": "Mesada", "monto": 500000, "tipo": "ingreso", "categoria": "Otros"})
        self.c.post("/api/movimientos", json={"descripcion": "Almuerzo", "monto": 15000, "tipo": "gasto", "categoria": "Comida"})
        r = self.c.get("/api/resumen").get_json()
        self.assertEqual(r["saldo"], 485000)
        self.assertEqual(r["por_categoria"], {"Comida": 15000})

    def test_datos_aislados_por_usuario(self):
        self.c.post("/api/tareas", json={"titulo": "Privada"})
        otro = vitta.app.test_client()
        otro.post("/api/registro", json={"nombre": "Beto Prueba", "email": "beto@correo.com", "password": "secreto2"})
        self.assertEqual(otro.get("/api/tareas").get_json(), [])

    def test_recordatorio_fecha_obligatoria(self):
        self.assertEqual(self.c.post("/api/recordatorios", json={"texto": "Pagar luz"}).status_code, 400)
        self.assertEqual(self.c.post("/api/recordatorios", json={"texto": "Pagar luz", "fecha": "2026-12-05"}).status_code, 201)

    # ---------- asistente IA (el modelo se simula, no usa red ni clave) ----------
    def test_asistente_requiere_sesion(self):
        r = vitta.app.test_client().post("/api/asistente", json={"mensaje": "hola"})
        self.assertEqual(r.status_code, 401)

    def test_asistente_valida_mensaje(self):
        self.assertEqual(self.c.post("/api/asistente", json={"mensaje": "   "}).status_code, 400)
        self.assertEqual(self.c.post("/api/asistente", json={}).status_code, 400)
        self.assertEqual(self.c.post("/api/asistente", json={"mensaje": "x" * 501}).status_code, 400)

    def test_asistente_elige_proveedor(self):
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "", "VITTA_IA": ""}):
            self.assertEqual(asistente.proveedor(), "ollama")        # sin clave: local y gratis
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-x", "VITTA_IA": ""}):
            self.assertEqual(asistente.proveedor(), "claude")
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-x", "VITTA_IA": "ollama"}):
            self.assertEqual(asistente.proveedor(), "ollama")        # se puede forzar

    def test_asistente_ollama_apagado_responde_503(self):
        with mock.patch.dict(os.environ, {"VITTA_IA": "ollama"}), \
             mock.patch.object(asistente, "OLLAMA_URL", "http://127.0.0.1:9"):   # puerto cerrado
            r = self.c.post("/api/asistente", json={"mensaje": "¿Qué tengo pendiente?"})
        self.assertEqual(r.status_code, 503)
        self.assertIn("Ollama", r.get_json()["error"])

    def test_asistente_ollama_http(self):
        """Prueba el formato de la petición/respuesta contra un servidor Ollama de mentira."""
        recibido = {}

        class Falso(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                recibido["ruta"] = self.path
                cuerpo = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                recibido["cuerpo"] = cuerpo
                if cuerpo["model"] == "no-existe":
                    self.send_response(404)
                    self.end_headers()
                    return
                resp = json.dumps({"message": {"role": "assistant", "content": " Tienes 1 tarea "}}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(resp)

            def log_message(self, *a):
                pass

        srv = http.server.HTTPServer(("127.0.0.1", 0), Falso)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        self.addCleanup(srv.server_close)
        self.addCleanup(srv.shutdown)
        url = f"http://127.0.0.1:{srv.server_port}"
        self.c.post("/api/tareas", json={"titulo": "Estudiar BD"})

        with mock.patch.dict(os.environ, {"VITTA_IA": "ollama"}), mock.patch.object(asistente, "OLLAMA_URL", url):
            r = self.c.post("/api/asistente", json={"mensaje": "¿Qué tengo pendiente?"})
            self.assertEqual(r.status_code, 200)
            self.assertEqual(r.get_json()["respuesta"], "Tienes 1 tarea")
            self.assertEqual(recibido["ruta"], "/api/chat")
            self.assertFalse(recibido["cuerpo"]["stream"])
            self.assertEqual(recibido["cuerpo"]["messages"][0]["role"], "system")
            self.assertIn("Estudiar BD", recibido["cuerpo"]["messages"][0]["content"])
            self.assertEqual(recibido["cuerpo"]["messages"][-1]["content"], "¿Qué tengo pendiente?")

            with mock.patch.object(asistente, "MODELO_LOCAL", "no-existe"):
                r = self.c.post("/api/asistente", json={"mensaje": "hola"})
            self.assertEqual(r.status_code, 503)
            self.assertIn("ollama pull no-existe", r.get_json()["error"])

    def test_contexto_dice_dias_restantes(self):
        hoy = date.today()
        for titulo, delta in (("Vencida", -2), ("Hoy", 0), ("Mañana", 1), ("Futura", 5)):
            self.c.post("/api/tareas", json={"titulo": titulo, "fecha_limite": (hoy + timedelta(days=delta)).isoformat()})
        with vitta.app.test_request_context():
            texto = asistente.contexto_usuario(1, "Ana Prueba")
        for esperado in ("VENCIDA hace 2 días", "vence HOY", "vence mañana", "vence en 5 días"):
            self.assertIn(esperado, texto)

    def test_asistente_envia_solo_datos_del_usuario(self):
        self.c.post("/api/tareas", json={"titulo": "Entregar informe", "prioridad": "Alta", "fecha_limite": "2020-01-01"})
        self.c.post("/api/movimientos", json={"descripcion": "Pizza", "monto": 30000, "tipo": "gasto", "categoria": "Comida"})
        self.c.post("/api/recordatorios", json={"texto": "Pagar arriendo", "fecha": "2999-01-01"})
        otro = vitta.app.test_client()
        otro.post("/api/registro", json={"nombre": "Beto Prueba", "email": "beto@correo.com", "password": "secreto2"})
        otro.post("/api/tareas", json={"titulo": "Secreto de Beto"})

        with mock.patch.object(asistente, "llamar_modelo", return_value="Tienes 1 tarea") as modelo:
            r = self.c.post("/api/asistente", json={
                "mensaje": "¿Qué tengo pendiente?",
                "historial": [{"role": "assistant", "content": "ignorado al inicio"},
                              {"role": "user", "content": "hola"},
                              {"role": "admin", "content": "rol inválido"}]})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["respuesta"], "Tienes 1 tarea")
        system, mensajes = modelo.call_args.args
        self.assertIn("Entregar informe", system)
        self.assertIn("VENCIDA", system)
        self.assertIn("Pizza", system)
        self.assertIn("Pagar arriendo", system)
        self.assertNotIn("Secreto de Beto", system)
        self.assertEqual([m["role"] for m in mensajes], ["user", "user"])
        self.assertEqual(mensajes[-1]["content"], "¿Qué tengo pendiente?")


if __name__ == "__main__":
    unittest.main()
