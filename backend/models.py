"""
models.py — Modelos Pydantic para validación y serialización
Principio SOLID: cada clase tiene una única responsabilidad
"""

from pydantic import BaseModel, field_validator, model_validator
from typing import Optional
from datetime import date


# ── USUARIOS ─────────────────────────────────────────────────────────────────

class UsuarioCreate(BaseModel):
    nombre: str
    rol: str  # 'administrador' | 'operador'

    @field_validator("rol")
    @classmethod
    def validar_rol(cls, v):
        if v not in ("administrador", "operador"):
            raise ValueError("El rol debe ser 'administrador' u 'operador'")
        return v

    @field_validator("nombre")
    @classmethod
    def validar_nombre(cls, v):
        if not v or not v.strip():
            raise ValueError("El nombre es obligatorio")
        return v.strip()


class UsuarioResponse(BaseModel):
    id: int
    nombre: str
    rol: str
    creado_en: str


# ── DIAGNÓSTICO INICIAL (SCRUM-7) ─────────────────────────────────────────────

class DiagnosticoCreate(BaseModel):
    anio: int
    periodo: str
    organico: float = 0.0
    reciclable: float = 0.0
    no_aprovechable: float = 0.0
    especial: float = 0.0
    observaciones: Optional[str] = None
    usuario_id: Optional[int] = None

    @field_validator("anio")
    @classmethod
    def validar_anio(cls, v):
        if v < 2000 or v > 2099:
            raise ValueError("El año debe estar entre 2000 y 2099")
        return v

    @field_validator("periodo")
    @classmethod
    def validar_periodo(cls, v):
        if not v or not v.strip():
            raise ValueError("El período es obligatorio")
        return v.strip()

    @model_validator(mode="after")
    def al_menos_un_tipo(self):
        total = self.organico + self.reciclable + self.no_aprovechable + self.especial
        if total == 0:
            raise ValueError("Ingrese al menos una cantidad de residuos")
        return self

    @field_validator("organico", "reciclable", "no_aprovechable", "especial")
    @classmethod
    def no_negativos(cls, v):
        if v < 0:
            raise ValueError("Las cantidades no pueden ser negativas")
        return v


class DiagnosticoResponse(BaseModel):
    id: int
    anio: int
    periodo: str
    organico: float
    reciclable: float
    no_aprovechable: float
    especial: float
    total: float
    observaciones: Optional[str]
    usuario_id: Optional[int]
    creado_en: str


# ── METAS PGIRS (SCRUM-8) ────────────────────────────────────────────────────

class MetaCreate(BaseModel):
    periodo: str
    tipo_residuo: str
    valor_meta: float
    indicador: Optional[str] = None
    diagnostico_id: Optional[int] = None
    usuario_id: Optional[int] = None

    @field_validator("valor_meta")
    @classmethod
    def valor_numerico_positivo(cls, v):
        if v < 0:
            raise ValueError("El valor de la meta no puede ser negativo")
        return v

    @field_validator("periodo", "tipo_residuo")
    @classmethod
    def obligatorios(cls, v):
        if not v or not v.strip():
            raise ValueError("Campo obligatorio")
        return v.strip()


class MetaResponse(BaseModel):
    id: int
    periodo: str
    tipo_residuo: str
    valor_meta: float
    indicador: Optional[str]
    diagnostico_id: Optional[int]
    usuario_id: Optional[int]
    creado_en: str


# ── CLASIFICACIÓN (SCRUM-9) ──────────────────────────────────────────────────

TIPOS_VALIDOS = ("Orgánico", "Reciclable", "No Aprovechable", "Especial")


class ClasificacionCreate(BaseModel):
    tipo_residuo: str
    fecha_recoleccion: str
    ruta_zona: Optional[str] = None
    vehiculo: Optional[str] = None
    observaciones: Optional[str] = None
    usuario_id: Optional[int] = None

    @field_validator("tipo_residuo")
    @classmethod
    def tipo_obligatorio(cls, v):
        if not v or not v.strip():
            raise ValueError("El tipo de residuo es obligatorio")
        if v not in TIPOS_VALIDOS:
            raise ValueError(f"Tipo inválido. Use: {TIPOS_VALIDOS}")
        return v

    @field_validator("fecha_recoleccion")
    @classmethod
    def fecha_obligatoria(cls, v):
        if not v or not v.strip():
            raise ValueError("La fecha de recolección es obligatoria")
        return v.strip()


class ClasificacionResponse(BaseModel):
    id: int
    tipo_residuo: str
    fecha_recoleccion: str
    ruta_zona: Optional[str]
    vehiculo: Optional[str]
    observaciones: Optional[str]
    usuario_id: Optional[int]
    creado_en: str


# ── CANTIDADES (SCRUM-10) ────────────────────────────────────────────────────

class CantidadCreate(BaseModel):
    fecha: Optional[str] = None       # se asigna automáticamente si está vacía
    organico: float = 0.0
    reciclable: float = 0.0
    no_aprovechable: float = 0.0
    especial: float = 0.0
    usuario_id: Optional[int] = None

    @field_validator("organico", "reciclable", "no_aprovechable", "especial")
    @classmethod
    def no_negativos(cls, v):
        if v < 0:
            raise ValueError("Las cantidades no pueden ser negativas")
        return v


class CantidadResponse(BaseModel):
    id: int
    fecha: str
    organico: float
    reciclable: float
    no_aprovechable: float
    especial: float
    total: float
    usuario_id: Optional[int]
    creado_en: str


# ── INDICADORES (SCRUM-11) ───────────────────────────────────────────────────

class IndicadorResponse(BaseModel):
    periodo: Optional[str]
    total_general: float
    total_organico: float
    total_reciclable: float
    total_no_aprovechable: float
    total_especial: float
    pct_organico: float
    pct_reciclable: float
    pct_no_aprovechable: float
    tasa_aprovechamiento: float
    registros_cantidad: int


# ── TRAZABILIDAD (SCRUM-12) ──────────────────────────────────────────────────

class AccionLogResponse(BaseModel):
    id: int
    accion: str
    entidad: str
    detalle: Optional[str]
    usuario_id: Optional[int]
    fecha_hora: str
