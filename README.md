# Sistema de Administración de Bodegas

Proyecto académico (equipo de 4: 2 Developers, 1 Product Owner, 1 Scrum Master).
Python 3.10+ · Flet 0.28.3 · SQLite.

## 1. Ejecución en Visual Studio Code

```bash
# 1) Entorno virtual
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS / Linux

# 2) Dependencias
pip install -r requirements.txt

# 3) Ejecutar (crea bodega.db y datos demo la primera vez)
python main.py
# o con recarga en caliente:  flet run main.py
```
No ejecutes los archivos dentro de `models/` directamente. Son módulos internos
que dependen de los paquetes `database/` y `utils/`. Para probar el modelo
desde la raíz del proyecto usa:

```bash
python -m models.product_request_model
```

En VS Code: `Ctrl+Shift+P` → *Python: Select Interpreter* → elegir `.venv`.

### Usuarios de demostración
| Usuario  | Contraseña    | Rol                 |
|----------|---------------|---------------------|
| admin    | Admin123!     | Administrador       |
| bodega   | Bodega123!    | Encargado de bodega |
| *(clientes)* | creados por el administrador | Cliente vinculado a una bodega |

Para reiniciar los datos, cierre la app y borre `bodega.db`.

### Matriz de permisos
| Acción                               | Admin | Encargado | Cliente |
|--------------------------------------|:-----:|:---------:|:--------:|
| Ver dashboard / inventario / historial | ✔ (todas) | ✔ (supervisión general) | ✔ (su stock, solo lectura) |
| Crear y editar productos              | ✔ | ✔ | ✖ |
| Registrar entradas y salidas          | ✔ | ✔ | ✖ |
| Desactivar / reactivar productos      | ✔ | ✔ | ✖ |
| Gestionar bodegas y crear usuarios cliente | ✔ | ✖ | ✖ |

El encargado funciona como supervisor operativo y puede consultar todos los
propietarios, sus datos, productos, movimientos, ingresos, salidas y el estado
de todas las bodegas (libres, ocupadas o inactivas). Esta supervisión es de
solo lectura para las bodegas que no opera. Sus entradas y salidas quedan
registradas con su nombre y son visibles en el historial del administrador y del
cliente propietario. Las solicitudes
creadas por clientes (alta de producto, entrada o salida por venta) siguen
requiriendo aprobación del administrador; el encargado no puede aprobarlas,
pero sí puede ejecutar movimientos directos de su bodega.

## 2. Arquitectura

```
main.py            -> arranque, rutas y guards (sesión + permisos)
database/          -> conexión SQLite, esquema, triggers y seed
models/            -> lógica de negocio y SQL (sin código de UI)
views/             -> pantallas Flet (sin SQL)
utils/             -> validadores, hash de contraseñas, sesión y permisos
```
Regla de equipo: **las vistas nunca escriben SQL; los modelos nunca importan Flet.**

Garantías en la base de datos:
- `sku` UNIQUE (sin distinguir mayúsculas) y `PRAGMA foreign_keys = ON`.
- `CHECK (cantidad_actual >= 0)`: imposible un stock negativo.
- Triggers: `movimientos` no admite UPDATE/DELETE y `productos` no admite DELETE.

La aplicación migra automáticamente bases existentes y crea las entidades
`bodegas` y `clientes`. Cada producto y usuario de bodega queda asociado a una
bodega. El admin puede crear clientes desde **Administración**, asignándoles
usuario, contraseña personalizada y bodega. El cliente solo puede consultar el
inventario e historial de su bodega. Si aún no tiene productos, puede solicitar
un alta de inventario desde **Inventario**; la solicitud debe ser aprobada por
el administrador y entonces se crea el producto asociado solo a ese cliente.
También puede solicitar entradas y salidas sobre su propio
stock, por ejemplo una salida para registrar una venta. Estas solicitudes de
entrada/salida requieren exclusivamente aprobación del administrador; el stock
solo cambia después de esa aprobación y queda en el historial del cliente. El
encargado es quien registra entradas, salidas y cambios directos de mercancía.
La cuenta antigua `consulta` se desactiva.
“Eliminar” mercancía se realiza como salida de stock, y
eliminar un producto del catálogo se realiza como desactivación para conservar
su historial.

---

## 3. Estrategia Git (GitFlow simplificado)

### 3.1 Ramas
| Rama        | Propósito                                             | Quién integra |
|-------------|-------------------------------------------------------|---------------|
| `main`      | Código estable, entregable. Solo recibe merges desde `develop` + tag. | Scrum Master / líderes al cerrar sprint |
| `develop`   | Integración continua del sprint.                      | Vía Pull Request |
| `feature/*` | Una rama por historia de usuario / tarea.             | Cada developer |

### 3.2 Crear el repositorio (lo hace UNA persona, p. ej. el Developer 1)
```bash
cd sistema_bodega
git init -b main                      # (Git < 2.28:  git init && git branch -M main)
git add .
git commit -m "chore: estructura inicial del proyecto"

# Crear un repositorio VACÍO en GitHub/GitLab y enlazarlo:
git remote add origin https://github.com/<equipo>/sistema_bodega.git
git push -u origin main

# Rama de integración, creada a partir de main
git switch -c develop
git push -u origin develop
```
Proteger `main` y `develop` en GitHub (*Settings → Branches → Branch protection rules*:
exigir Pull Request y 1 aprobación). Agregar a los 4 integrantes como colaboradores.

### 3.3 Los demás integrantes clonan
```bash
git clone https://github.com/<equipo>/sistema_bodega.git
cd sistema_bodega
git switch develop
```

### 3.4 Flujo de una feature (cada developer, cada tarea)
```bash
git switch develop
git pull origin develop                      # SIEMPRE partir de develop actualizado
git switch -c feature/nombre-descriptivo     # crear rama temporal

# ... programar ...
git add .
git commit -m "feat(inventario): validar salida contra stock actual"
git push -u origin feature/nombre-descriptivo
```
Luego, en GitHub: **Pull Request `feature/...` → `develop`**. El otro developer revisa
(code review), se aprueba y se hace *merge*. Después:
```bash
git switch develop
git pull origin develop
git branch -d feature/nombre-descriptivo     # borrar rama local
git push origin --delete feature/nombre-descriptivo
```

Si `develop` avanzó mientras trabajabas, actualiza tu rama antes del PR:
```bash
git fetch origin
git merge origin/develop        # resuelve conflictos en VS Code (Merge Editor) y luego:
git add . && git commit
```

### 3.5 Reparto sugerido para los 2 programadores
Para evitar conflictos, trabajan en **archivos distintos**:

| Dev | Ramas feature                                                               | Archivos                                              |
|-----|------------------------------------------------------------------------------|-------------------------------------------------------|
| **Dev 1 (Datos y reglas)** | `feature/database-schema`, `feature/auth-login`, `feature/movimientos-stock` | `database/*`, `models/*`, `utils/*`, `views/login_view.py`, `main.py` |
| **Dev 2 (Interfaz)**       | `feature/ui-layout-dashboard`, `feature/ui-inventario-productos`, `feature/ui-historial` | `views/layout.py`, `views/dashboard_view.py`, `views/inventory_view.py`, `views/history_view.py` |

**Orden:** Dev 1 integra primero `feature/database-schema` a `develop` (es el contrato
del que depende Dev 2). Dev 2 puede mientras tanto trabajar con datos simulados.

### 3.6 Cierre de sprint / entrega
```bash
git switch main
git pull origin main
git merge --no-ff develop -m "release: sprint 1"
git tag -a v0.1.0 -m "Sprint 1: login, inventario y movimientos"
git push origin main --tags
git switch develop                    # volver a trabajar en develop
```

### 3.7 Convención de commits
`feat:` nueva funcionalidad · `fix:` corrección · `docs:` documentación ·
`refactor:` reestructuración · `test:` pruebas · `chore:` tareas de mantenimiento.
Ejemplo: `fix(movimientos): impedir salida con cantidad mayor al stock`.

### 3.8 Roles Scrum ↔ Git
- **Product Owner:** redacta las historias de usuario; cada una se convierte en un *issue* y su rama `feature/`.
- **Scrum Master:** vigila el tablero, que los PR no queden estancados y hace el merge `develop → main`.
- **Developers:** una rama por tarea, PR pequeños, revisión cruzada.

## 4. Backlog sugerido / próximos pasos
- Gestión de usuarios desde la UI (ya existe `user_model.create_user`).
- CRUD de categorías y ubicaciones desde la UI.
- Exportar historial a CSV/Excel y reporte de stock bajo.
- Pruebas automatizadas con `pytest` sobre `models/`.
