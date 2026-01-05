from nicegui import ui, app
from app.ui.theme import frame
from app.models.domain import Operation, Lot, BankAccount, Owner, OperationType, Allocation, UserRole
from app.database import get_session
from app.services.accounting import distribute_operation
from app.audit import log_action
from sqlmodel import select
from datetime import date
from decimal import Decimal
from app.utils.formatters import format_currency

def operations_page():
    # State
    op_id_ref = {'value': None}
    
    # Load helpers (Shared for Filters and Dialog)
    lots_map = {}
    accounts_map = {}
    owners_map = {}
    categories_map = {}
    reversement_ids = set()

    with next(get_session()) as session:
        lots = session.exec(select(Lot)).all()
        lots_map = {l.id: l.name for l in lots}
        
        accs = session.exec(select(BankAccount)).all()
        accounts_map = {a.id: a.name for a in accs}
        
        owners = session.exec(select(Owner)).all()
        owners_map = {o.id: o.name for o in owners}

        from app.models.domain import Category
        cats = session.exec(select(Category)).all()
        categories_map = {c.id: c.name for c in cats}
        reversement_ids = {c.id for c in cats if c.is_reversement}
    
    # --- DIALOG ---
    with ui.dialog() as dialog, ui.card().classes('w-full max-w-2xl'):
        ui.label('Opération').classes('text-xl font-bold mb-4')

        if not lots_map or not accounts_map:
            ui.label("Veuillez d'abord créer des Lots et des Comptes Bancaires.").classes('text-red-400')
        
        with ui.grid(columns=2).classes('w-full gap-4'):
            date_input = ui.input('Date (YYYY-MM-DD)', value=date.today().isoformat())
            amount_input = ui.number('Montant', value=0.0, format='%.2f')
            
            lot_select = ui.select(lots_map, label='Lot').classes('w-full')
            acc_select = ui.select(accounts_map, label='Compte Bancaire').classes('w-full')
            
            type_select = ui.select([t.value for t in OperationType], label='Type', value=OperationType.SORTIE.value)
            cat_select = ui.select(categories_map, label='Catégorie').classes('w-full')
            
            label_input = ui.input('Libellé').classes('col-span-2')
            
            # Distribution Recipient (only for REVERSEMENT categories)
            recipient_select = ui.select(owners_map, label='Propriétaire Bénéficiaire (si hors lot)', clearable=True).classes('col-span-2')
            recipient_select.bind_visibility_from(cat_select, 'value', backward=lambda v: v in reversement_ids)

            # Note de frais
            paid_by_select = ui.select(owners_map, label='Payé par (Optionnel - Note de frais)', clearable=True).classes('col-span-2')

        def save():
            try:
                d = date.fromisoformat(date_input.value)
                amt = Decimal(str(amount_input.value))
                
                is_reversement = cat_select.value in reversement_ids
                
                if not lot_select.value and not is_reversement:
                    ui.notify("Veuillez sélectionner un Lot", type='warning')
                    return
                
                if is_reversement and not lot_select.value and not recipient_select.value:
                    ui.notify("Veuillez sélectionner un Bénéficiaire pour ce reversement hors-lot", type='warning')
                    return
 
                if not acc_select.value:
                    ui.notify("Veuillez sélectionner un Compte Bancaire", type='warning')
                    return
                
                if not cat_select.value:
                    ui.notify("Veuillez sélectionner une Catégorie", type='warning')
                    return
 
                with next(get_session()) as session:
                    if op_id_ref['value']:
                        # UPDATE
                        op = session.get(Operation, op_id_ref['value'])
                        op.date = d
                        op.amount = amt
                        op.lot_id = lot_select.value
                        op.bank_account_id = acc_select.value
                        op.type = OperationType(type_select.value)
                        op.category_id = cat_select.value
                        op.label = label_input.value
                        op.paid_by_owner_id = paid_by_select.value
                        
                        # Delete old allocations to re-calculate
                        for old_alloc in op.allocations:
                            session.delete(old_alloc)
                    else:
                        # INSERT
                        op = Operation(
                            date=d,
                            amount=amt,
                            lot_id=lot_select.value,
                            bank_account_id=acc_select.value,
                            type=OperationType(type_select.value),
                            category_id=cat_select.value,
                            label=label_input.value,
                            paid_by_owner_id=paid_by_select.value
                        )
                        session.add(op)
                    
                    session.flush() # Ensure ID and persistence
                    
                    # Re-Calculate allocations (for both insert and update)
                    if lot_select.value:
                        allocs = distribute_operation(session, op)
                    elif is_reversement and recipient_select.value:
                        # Manual allocation for personal distribution
                        allocs = [Allocation(owner_id=recipient_select.value, amount=amt)]
                    else:
                        allocs = []

                    for a in allocs:
                        a.operation_id = op.id 
                        session.add(a)
                    
                    session.commit()
                    
                    user_name = app.storage.user.get('name', 'Unknown')
                    action_type = "UPDATE_OPERATION" if op_id_ref['value'] else "CREATE_OPERATION"
                    log_action(user_name, action_type, f"Montant: {amt}, Lot: {lot_select.value}, Label: {label_input.value}")
                    
                    ui.notify('Opération enregistrée et répartie')
                    dialog.close()
                    refresh_ops_ui()
            except Exception as e:
                ui.notify(f"Erreur: {str(e)}", type='negative', close_button=True)

        def delete_op():
            if not op_id_ref['value']: return
            try:
                with next(get_session()) as session:
                    op = session.get(Operation, op_id_ref['value'])
                    # Cascade delete allocations explicitly
                    for a in op.allocations:
                        session.delete(a)
                    session.delete(op)
                    session.commit()
                ui.notify('Opération supprimée')
                dialog.close()
                refresh_ops_ui()
            except Exception as e:
                ui.notify(f"Erreur suppression: {e}", type='negative')

        with ui.row().classes('w-full justify-between mt-4'):
            del_op_btn = ui.button('Supprimer', on_click=delete_op).classes('bg-red-500 text-white')
            del_op_btn.visible = False
            
            ui.button('Enregistrer', on_click=save).classes('bg-emerald-500 text-white')

    # --- TRANSFER DIALOG ---
    with ui.dialog() as transfer_dialog, ui.card().classes('w-full max-w-2xl'):
        ui.label('Virement Inter-comptes').classes('text-xl font-bold mb-4')
        
        t_date = ui.input('Date', value=date.today().isoformat())
        t_amount = ui.number('Montant', value=0.0, format='%.2f')
        t_label = ui.input('Libellé (ex: Épargne mensuelle)')
        
        with ui.row().classes('w-full'):
            t_from = ui.select(accounts_map, label='Compte Source').classes('w-1/2')
            ui.icon('arrow_forward').classes('text-2xl mt-4 text-slate-500')
            t_to = ui.select(accounts_map, label='Compte Destination').classes('w-1/2')
            
        def execute_transfer():
            try:
                d = date.fromisoformat(t_date.value)
                amt = Decimal(str(t_amount.value))
                
                if t_from.value == t_to.value:
                    ui.notify('Comptes source et destination identiques', type='warning')
                    return
                
                from app.services.accounting import create_transfer # Import logic
                
                with next(get_session()) as session:
                    create_transfer(session, d, amt, t_from.value, t_to.value, None, t_label.value)
                    session.commit()
                    
                    user = app.storage.user.get('name', 'Unknown')
                    log_action(user, "TRANSFER", f"{amt} from {t_from.value} to {t_to.value}")
                    
                    ui.notify('Virement effectué')
                    transfer_dialog.close()
                    refresh_ops_ui()
                    
            except Exception as e:
                ui.notify(f"Erreur: {e}", type='negative')

        ui.button('Exécuter le virement', on_click=execute_transfer).classes('mt-4 w-full bg-cyan-600 text-white')

    # --- CONTENT ---
    def content():
        # Check Permissions
        user_role = app.storage.user.get('role', UserRole.READ.value)
        can_edit = user_role in [UserRole.WRITE.value, UserRole.ADMIN.value]
        
        def open_create():
            op_id_ref['value'] = None
            # Reset
            date_input.value = date.today().isoformat()
            amount_input.value = 0.0
            type_select.value = OperationType.SORTIE.value
            
            # Find ID of "AUTRE" category for default
            autre_id = None
            for c_id, c_name in categories_map.items():
                if c_name == "AUTRE":
                    autre_id = c_id
                    break
            cat_select.value = autre_id
            
            label_input.value = ''
            paid_by_select.value = None
            recipient_select.value = None
            del_op_btn.visible = False
            dialog.open()
            
        def open_transfer():
            t_date.value = date.today().isoformat()
            t_amount.value = 0.0
            t_label.value = ''
            t_from.value = None
            t_to.value = None
            transfer_dialog.open()
            
        def open_edit(op_id):
            op_id_ref['value'] = op_id
            with next(get_session()) as session:
                op = session.get(Operation, op_id)
                if op:
                    date_input.value = op.date.isoformat()
                    amount_input.value = float(op.amount)
                    lot_select.value = op.lot_id
                    acc_select.value = op.bank_account_id
                    type_select.value = op.type.value
                    cat_select.value = op.category_id
                    label_input.value = op.label
                    paid_by_select.value = op.paid_by_owner_id
                    
                    # Logic to find recipient for Lot-free Reversements
                    if not op.lot_id and op.category_id in reversement_ids:
                        recipient_select.value = op.allocations[0].owner_id if op.allocations else None
                    else:
                        recipient_select.value = None
                        
                    del_op_btn.visible = True
                    dialog.open()

        # --- FILTER DIALOG ---
        today = date.today()
        jan_1 = date(today.year-1, 1, 1)

        filter_state = {
            'lot': None,
            'acc': None,
            'type': None,
            'cat': None,
            'start': jan_1.isoformat(),
            'end': today.isoformat(),
            'label': '',
        }
        
        with ui.dialog() as filter_dialog, ui.card().classes('w-full max-w-lg'):
            ui.label('Filtres de recherche').classes('text-xl font-bold mb-4')
            
            # Form
            with ui.column().classes('w-full gap-4'):
                f_label = ui.input('Libellé (contient)', value=filter_state['label']).bind_value(filter_state, 'label').classes('w-full')
                # Temporary workaround for bind_value not working with input fields:
                # https://github.com/zauberzeug/nicegui/issues/2149#issuecomment-2507225590
                f_label.LOOPBACK = True

                with ui.grid(columns=2).classes('w-full gap-4'):
                    f_start = ui.input('Date Début', value=filter_state['start']).bind_value(filter_state, 'start').props('type=date')
                    f_start.LOOPBACK = True  # Same workaround
                    f_end = ui.input('Date Fin', value=filter_state['end']).bind_value(filter_state, 'end').props('type=date')
                    f_end.LOOPBACK = True  # Same workaround
                
                f_lot = ui.select(lots_map, label='Lot', clearable=True, value=filter_state['lot']).bind_value(filter_state, 'lot').classes('w-full')
                f_acc = ui.select(accounts_map, label='Compte', clearable=True, value=filter_state['acc']).bind_value(filter_state, 'acc').classes('w-full')
                f_type = ui.select([t.value for t in OperationType], label='Type', clearable=True, value=filter_state['type']).bind_value(filter_state, 'type').classes('w-full')
                f_cat = ui.select(categories_map, label='Catégorie', clearable=True, value=filter_state['cat']).bind_value(filter_state, 'cat').classes('w-full')
            
            
            
            def reset_filters():
                f_label.value = ''
                f_start.value = jan_1.isoformat()
                f_end.value = today.isoformat()
                f_lot.value = None
                f_acc.value = None
                f_type.value = None
                f_cat.value = None

            with ui.row().classes('w-full justify-between mt-4'):
                ui.button('Réinitialiser', on_click=reset_filters).props('flat color=grey')
                with ui.row().classes('gap-2'):
                    ui.button('Fermer', on_click=filter_dialog.close).props('flat')
                    ui.button('Appliquer', on_click=lambda: [refresh_table(), filter_dialog.close()]).classes('bg-primary text-white')

        # Toolbar
        with ui.row().classes('w-full gap-2 mb-4 justify-between'):
            with ui.row().classes('gap-2'):
                if can_edit:
                    ui.button('Opération Simple', on_click=open_create, icon='add').classes('bg-emerald-500 text-white')
                    ui.button('Virement', on_click=open_transfer, icon='swap_horiz').classes('bg-cyan-600 text-white')
            
            filter_btn = ui.button('Filtres', icon='filter_list', on_click=filter_dialog.open).classes('bg-slate-500 text-white')
            
            def update_filter_indicator():
                 is_filtered = (
                     filter_state['lot'] is not None or
                     filter_state['acc'] is not None or
                     filter_state['type'] is not None or
                     filter_state['cat'] is not None or
                     filter_state['label'] != '' or
                     filter_state['start'] != jan_1.isoformat() or
                     filter_state['end'] != today.isoformat()
                 )
                 if is_filtered:
                     filter_btn.classes('bg-orange-500', remove='bg-slate-500').props('icon=filter_list_alt')
                 else:
                     filter_btn.classes('bg-slate-500', remove='bg-orange-500').props('icon=filter_list')
        
        columns = [
            {'name': 'date', 'label': 'Date', 'field': 'date', 'align': 'left', 'sortable': True},
            {'name': 'label', 'label': 'Libellé', 'field': 'label', 'align': 'left'},
            {'name': 'amount', 'label': 'Montant', 'field': 'amount_fmt', 'align': 'right'},
            {'name': 'lot', 'label': 'Lot', 'field': 'lot_name', 'align': 'left'},
            {'name': 'bank_account', 'label': 'Compte', 'field': 'bank_account_name', 'align': 'left'},
            {'name': 'category', 'label': 'Catégorie', 'field': 'category_name', 'align': 'left'},
            {'name': 'actions', 'label': 'Actions', 'field': 'id'},
        ]
        
        # Remove actions column if read-only
        if not can_edit:
             columns = [c for c in columns if c['name'] != 'actions']
        
        table = ui.table(columns=columns, rows=[], pagination=10).classes('w-full glass-panel')
        
        if can_edit:
            table.add_slot('body-cell-actions', '''
                <q-td :props="props">
                    <q-btn size="sm" color="primary" round dense icon="edit" @click="$parent.$emit('edit', props.value)" />
                </q-td>
            ''')
            table.on('edit', lambda e: open_edit(e.args))

        def refresh_table():
            update_filter_indicator()

            with next(get_session()) as session:
                query = select(Operation)
                 
                # Apply Filters
                if filter_state['lot']:
                    query = query.where(Operation.lot_id == filter_state['lot'])
                if filter_state['acc']:
                    query = query.where(Operation.bank_account_id == filter_state['acc'])
                if filter_state['type']:
                    query = query.where(Operation.type == OperationType(filter_state['type']))
                if filter_state['cat']:
                    query = query.where(Operation.category_id == filter_state['cat'])
                if filter_state['start']:
                    query = query.where(Operation.date >= date.fromisoformat(filter_state['start']))
                if filter_state['end']:
                    query = query.where(Operation.date <= date.fromisoformat(filter_state['end']))
                if filter_state['label']:
                    # Case insensitive search
                    query = query.where(Operation.label.ilike(f"%{filter_state['label']}%"))

                ops = session.exec(query.order_by(Operation.date.desc())).all()
                rows = []
                for o in ops: # Lazy load refs
                    l_name = o.lot.name if o.lot else "-"
                    acc_name = o.bank_account.name if o.bank_account else "?"
                    # Amount color
                    sign = -1 if o.type == OperationType.SORTIE else 1
                    amt_fmt = format_currency(o.amount * sign, show_sign=True)
                          
                    rows.append({
                        'id': o.id,
                        'date': o.date.isoformat(),
                        'label': o.label,
                        'amount_fmt': amt_fmt,
                        'lot_name': l_name,
                        'bank_account_name': acc_name,
                        'category_name': categories_map.get(o.category_id, "?"),
                    })
                table.rows = rows
                table.update()
                 
        refresh_table()
        global refresh_ops_ref
        refresh_ops_ref = refresh_table

    frame("Journal des Opérations", content)

refresh_ops_ref = None
def refresh_ops_ui():
    if refresh_ops_ref: 
        refresh_ops_ref()
