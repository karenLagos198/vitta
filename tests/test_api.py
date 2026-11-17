"""Pruebas básicas de la API. Ejecutar:  python -m unittest discover tests"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
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


if __name__ == "__main__":
    unittest.main()
