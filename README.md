# EcoGestión — PGIRS Municipal
**Gestión integral de residuos sólidos** | Decreto 1077/2015 · Ley 142/1994

## Stack tecnológico
| Capa | Tecnología |
|---|---|
| Frontend | HTML5 + CSS3 + JavaScript (Vanilla) |
| Backend | Python 3.11+ · FastAPI |
| Base de datos | SQLite (archivo `ecogestion.db`) |
| Arquitectura | Cliente-Servidor (API REST) |
| Patrones | SOLID (SRP, OCP, LSP, ISP, DIP) |

## Estructura del proyecto
```
ecogestion/
├── backend/
│   ├── main.py           # FastAPI app + rutas (SCRUM-7 a 12)
│   ├── database.py       # Conexión SQLite + DDL + seed
│   ├── models.py         # Pydantic models (validación)
│   ├── crud.py           # Operaciones CRUD
│   └── requirements.txt
└── frontend/
    ├── index.html        # SPA principal
    ├── css/styles.css
    └── js/
        ├── api.js        # Cliente HTTP (fetch a FastAPI)
        ├── ui.js         # Helpers DOM
        └── app.js        # Controlador principal
```

## Cómo ejecutar

### 1. Backend (FastAPI)
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
# API disponible en: http://127.0.0.1:8000
# Docs automáticas:  http://127.0.0.1:8000/docs
```

### 2. Frontend (HTML)
Abre `frontend/index.html` directamente en el navegador,  
**o** sirve con un servidor local para evitar restricciones CORS:
```bash
cd frontend
python -m http.server 5500 --bind 127.0.0.1
# http://localhost:5500
```

## Endpoints de la API
| Método | Ruta | Historia |
|---|---|---|
| POST/GET | `/api/diagnosticos` | SCRUM-7 |
| POST/GET | `/api/metas` | SCRUM-8 |
| POST/GET | `/api/clasificaciones` | SCRUM-9 |
| POST/GET | `/api/cantidades` | SCRUM-10 |
| GET | `/api/indicadores` | SCRUM-11 |
| POST/GET | `/api/usuarios` | SCRUM-12 |
| GET | `/api/acciones` | SCRUM-12 |
| GET | `/api/health` | Sistema |

## Principios SOLID aplicados
- **S** — Cada archivo tiene una única responsabilidad (`crud.py`, `models.py`, `api.js`, `ui.js`)
- **O** — Nuevas entidades se agregan sin modificar el código existente
- **L** — Los modelos Pydantic son sustituibles entre sí
- **I** — Interfaces específicas por módulo (CRUD ≠ validación ≠ rutas)
- **D** — FastAPI usa inyección de dependencias (`Depends(get_db)`)

## Tiempo de respuesta del backend
PerformanceMonitor.reporteConsola();