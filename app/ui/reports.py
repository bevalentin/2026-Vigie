from nicegui import ui, app
from app.ui.theme import frame
from app.database import get_session
from app.models.domain import Operation, Allocation, Owner
from sqlmodel import select
from datetime import date
import os

# Directory for generated reports
REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'reports')

def reports_page():
    # Container for generated report links
    report_links_container = {'ref': None}
    
    def download_ops():
        try:
            from app.services.export import generate_operations_csv
            with next(get_session()) as session:
                ops = session.exec(select(Operation)).all()
                content = generate_operations_csv(ops)
                ui.download(content.encode('utf-8'), 'operations.csv')
        except Exception as e:
            ui.notify(f"Erreur export: {e}", type="negative")

    def download_allocs():
        try:
            from app.services.export import generate_allocations_csv
            with next(get_session()) as session:
                allocs = session.exec(select(Allocation)).all()
                content = generate_allocations_csv(allocs)
                ui.download(content.encode('utf-8'), 'allocations.csv')
        except Exception as e:
            ui.notify(f"Erreur export: {e}", type="negative")

    def generate_annual_pdf(owner_id: int, year: int):
        """Generate the PDF and save it to the reports directory."""
        if not owner_id:
            ui.notify("Veuillez sélectionner un propriétaire", type="warning")
            return
        
        try:
            from app.services.pdf_reports import generate_owner_annual_report
            with next(get_session()) as session:
                owner = session.get(Owner, owner_id)
                if not owner:
                    ui.notify("Propriétaire introuvable", type="negative")
                    return
                
                pdf_content = generate_owner_annual_report(session, owner_id, year)
                if pdf_content:
                    # Create safe filename
                    safe_name = owner.name.replace(" ", "_").replace("/", "-")
                    filename = f"Rapport_{safe_name}_{year}.pdf"
                    filepath = os.path.join(REPORTS_DIR, filename)
                    
                    # Write PDF to file
                    with open(filepath, 'wb') as f:
                        f.write(pdf_content)
                    
                    ui.notify(f"Rapport généré : {filename}", type="positive")
                    
                    # Refresh the links container
                    refresh_report_links()
                else:
                    ui.notify("Aucune donnée pour ce rapport", type="warning")
        except Exception as e:
            ui.notify(f"Erreur PDF: {e}", type="negative")

    def delete_report(filename: str):
        """Delete a report file."""
        try:
            filepath = os.path.join(REPORTS_DIR, filename)
            if os.path.exists(filepath):
                os.remove(filepath)
                ui.notify(f"Rapport supprimé : {filename}", type="positive")
                refresh_report_links()
        except Exception as e:
            ui.notify(f"Erreur suppression: {e}", type="negative")

    def refresh_report_links():
        """Refresh the list of available report links."""
        if report_links_container['ref']:
            report_links_container['ref'].clear()
            with report_links_container['ref']:
                # List all PDFs in the reports directory
                if os.path.exists(REPORTS_DIR):
                    pdf_files = sorted([f for f in os.listdir(REPORTS_DIR) if f.endswith('.pdf')], reverse=True)
                    if pdf_files:
                        for pdf in pdf_files[:10]:  # Show last 10 reports
                            with ui.row().classes('items-center gap-2 w-full'):
                                ui.icon('picture_as_pdf', color='red')
                                ui.link(pdf, f'/reports/{pdf}').classes('text-blue-500 hover:underline flex-grow')
                                ui.button(icon='delete', on_click=lambda p=pdf: delete_report(p))\
                                    .props('flat round size=sm color=negative')
                    else:
                        ui.label("Aucun rapport généré.").classes('text-slate-400 italic')

    def content():
        ui.label('Exports & Rapports').classes('text-xl font-bold mb-4')
        
        # Load owners for the dropdown
        owners_map = {}
        try:
            with next(get_session()) as session:
                owners = session.exec(select(Owner)).all()
                owners_map = {o.id: o.name for o in owners}
        except Exception as e:
            ui.label(f"Erreur base de données: {e}").classes('text-red-500')

        with ui.grid(columns=2).classes('w-full gap-4'):
            # CSV Section
            with ui.card().classes('glass-panel p-6'):
                with ui.row().classes('items-center mb-4'):
                    ui.icon('table_view', color='primary').classes('text-3xl')
                    ui.label('Exports CSV (Données Brutes)').classes('text-lg font-bold')
                
                with ui.column().classes('gap-2 w-full'):
                    ui.button('Journal des Opérations', icon='download', on_click=download_ops)\
                        .props('outline').classes('w-full justify-start')
                    ui.button('Détail des Répartitions', icon='download', on_click=download_allocs)\
                        .props('outline').classes('w-full justify-start')

            # PDF Section
            with ui.card().classes('glass-panel p-6'):
                with ui.row().classes('items-center mb-4'):
                    ui.icon('picture_as_pdf', color='red').classes('text-3xl')
                    ui.label('Compte Rendu Annuel (PDF)').classes('text-lg font-bold')
                
                current_year = date.today().year
                years = [current_year - i for i in range(5)]
                
                year_select = ui.select(years, label='Année', value=current_year).classes('w-full mb-2')
                owner_select = ui.select(owners_map, label='Propriétaire').classes('w-full mb-4')
                
                ui.button('Générer le Rapport PDF', icon='auto_awesome', 
                          on_click=lambda: generate_annual_pdf(owner_select.value, year_select.value))\
                    .classes('w-full bg-red-600 text-white shadow-md hover:scale-105 transition-transform')

        # Section for generated reports
        ui.label('Rapports Générés').classes('text-lg font-bold mt-6 mb-2')
        with ui.card().classes('glass-panel p-4 w-full'):
            report_links_container['ref'] = ui.column().classes('gap-1 w-full')
            refresh_report_links()

    frame("Rapports", content)

# Serve the reports directory as static files
app.add_static_files('/reports', REPORTS_DIR)
