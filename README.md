# Vitta
**Vive más, olvida menos.** Organizador personal web para gestionar en un solo lugar las tareas pendientes, las finanzas y los recordatorios de la vida diaria.

**Integrantes:** Santiago Rondon Díaz · Karen Lagos Camacho · Samuel David Gonzalez Petro
**Curso:** Taller de Programación · Ingeniería de Software

## Estado del proyecto
- **Fase I:** repositorio, estructura inicial y primera interfaz (Front-End).
- **Fase II (actual):** prototipo funcional con backend, base de datos, validaciones y navegación entre módulos.
- **Entrega final:** integración del servicio de Inteligencia Artificial. En `frontend/nn.js` hay una vista previa: una red neuronal pequeña que predice la categoría de un gasto.

## Funcionalidades del prototipo
| Módulo | Qué permite |
|---|---|
| Cuenta | Registro e inicio/cierre de sesión (contraseñas cifradas); cada usuario ve solo sus datos |
| Tareas | Crear, editar, completar y eliminar tareas con prioridad y fecha límite |
| Finanzas | Registrar ingresos y gastos por categoría, ver saldo y eliminar movimientos |
| Recordatorios | Crear y eliminar pagos o eventos con fecha |
| Resumen | Tareas pendientes, saldo, próximos recordatorios, gastos por categoría y progreso de tareas |

## Estructura del proyecto
```
vitta/
├── backend/
│   ├── app.py            # API Flask (rutas)
│   ├── db.py             # conexión a SQLite
│   ├── schema.sql        # tablas de la base de datos
│   └── validaciones.py   # validaciones de los datos
├── frontend/
│   ├── index.html        # aplicación principal
│   ├── login.html        # inicio de sesión y registro
│   ├── style.css
│   ├── app.js            # lógica de la aplicación
│   ├── auth.js           # lógica de login/registro
│   └── nn.js             # red neuronal (vista previa)
├── tests/test_api.py     # pruebas de la API
├── docs/evidencias/      # capturas del funcionamiento
├── requirements.txt
└── README.md
```

## Cómo ejecutar
Requisitos: Python 3.10 o superior.
```bash
pip install -r requirements.txt
python backend/app.py
```
Abrir **http://127.0.0.1:5000** en el navegador, crear una cuenta e ingresar. La base de datos `backend/vitta.db` se crea sola al iniciar.

Pruebas: `python -m unittest discover tests`

## API (resumen)
| Método | Ruta | Descripción |
|---|---|---|
| POST | `/api/registro`, `/api/login`, `/api/logout` | Sesión de usuario |
| GET/POST | `/api/tareas` | Listar / crear tareas |
| PATCH/DELETE | `/api/tareas/<id>` | Editar o completar / eliminar |
| GET/POST | `/api/movimientos` | Listar / registrar ingresos y gastos |
| DELETE | `/api/movimientos/<id>` | Eliminar movimiento |
| GET/POST | `/api/recordatorios` | Listar / crear recordatorios |
| DELETE | `/api/recordatorios/<id>` | Eliminar recordatorio |
| GET | `/api/resumen` | Datos del panel principal |

## Validaciones básicas
- **Frontend:** campos obligatorios, monto mayor que 0, fecha obligatoria en recordatorios, correo con formato válido y contraseña de mínimo 6 caracteres.
- **Backend:** se vuelven a validar todos los datos (longitud de textos, prioridad, tipo y categoría permitidos, fechas AAAA-MM-DD, monto numérico positivo, correo único) y cada usuario solo accede a sus propios registros.

## Evidencias del funcionamiento
Capturas en `docs/evidencias/`:
- `01-login.png`: inicio de sesión
- `02-resumen.png`: panel de resumen
- `03-tareas.png`: módulo de tareas
- `04-finanzas.png`: módulo de finanzas
- `05-pruebas.png`: resultado de las pruebas (`OK`)
