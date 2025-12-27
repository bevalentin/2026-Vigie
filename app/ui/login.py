from nicegui import ui, app
from app.services.auth import authenticate_user
from app.models.domain import UserRole
from app.audit import log_action

def login_page():
    
    # Check if already logged in
    if app.storage.user.get('authenticated', False):
        ui.navigate.to('/')
        return

    def try_login():
        user = authenticate_user(email.value, password.value)
        if user:
            app.storage.user['authenticated'] = True
            app.storage.user['id'] = user.id
            app.storage.user['name'] = user.name
            app.storage.user['role'] = user.role.value if user.role else UserRole.READ.value
            
            log_action(user.name, "LOGIN", "Connexion réussie")
            
            ui.navigate.to('/')
        else:
            log_action(email.value, "LOGIN_FAILED", "Tentative échouée")
            ui.notify('Email ou mot de passe incorrect', type='negative')

    with ui.card().classes('absolute-center w-96 p-8 glass-panel'):
        ui.label('Connexion Vigie').classes('text-2xl font-bold mb-6 text-center w-full')
        
        email = ui.input('Email').classes('w-full')
        password = ui.input('Mot de passe', password=True, password_toggle_button=True).classes('w-full')
        ui.button('Se connecter', on_click=try_login).classes('w-full bg-emerald-500 text-white mt-4')
