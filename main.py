"""
main.py
-------
Punto de entrada: inicializa la BD y configura Flet con enrutamiento básico.

    Rutas:  /login  ->  /dashboard  |  /inventory  |  /history
Guards:     sin sesión -> /login ;  sin permiso -> /dashboard

Ejecutar:   python main.py      (o  flet run main.py  para recarga en caliente)
"""
import flet as ft

from database.connection import init_db
from database.seed import seed_database
from utils.session import session, ROUTE_PERMISSIONS
from views.login_view import build_login_view
from views.dashboard_view import build_dashboard_view
from views.inventory_view import build_inventory_view
from views.history_view import build_history_view
from views.admin_view import build_admin_view

ROUTES = {
    "/login": build_login_view,
    "/dashboard": build_dashboard_view,
    "/inventory": build_inventory_view,
    "/history": build_history_view,
    "/admin": build_admin_view,
}


def main(page: ft.Page):
    page.title = "Sistema de Administración de Bodegas"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = ft.Theme(color_scheme_seed=ft.Colors.BLUE_700)
    page.window.width = 1280
    page.window.height = 800
    page.window.min_width = 900
    page.window.min_height = 600

    def on_route_change(e: ft.RouteChangeEvent):
        route = page.route

        # --- Guards de seguridad -------------------------------------------
        if route not in ROUTES:
            page.go("/dashboard" if session.is_authenticated else "/login")
            return
        if route != "/login" and not session.is_authenticated:
            page.go("/login")
            return
        if route == "/login" and session.is_authenticated:
            page.go("/dashboard")
            return
        required = ROUTE_PERMISSIONS.get(route)
        if required and not session.can(required):
            page.go("/dashboard")
            return

        # --- Render ---------------------------------------------------------
        page.views.clear()
        page.views.append(ROUTES[route](page))
        page.update()

    page.on_route_change = on_route_change
    page.go("/login")


if __name__ == "__main__":
    init_db()          # crea tablas si no existen
    seed_database()    # roles, usuarios por defecto y datos demo (idempotente)
    ft.app(target=main)
