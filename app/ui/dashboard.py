from nicegui import ui
from app.ui.theme import frame
from app.database import get_session
from app.models.domain import BankAccount, Operation, OperationType
from sqlmodel import select
import locale
from decimal import Decimal
from app.utils.formatters import format_currency

# Try to set locale for currency, fallback if not available
try:
    locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')
except:
    pass

def dashboard_page():
    
    def content():
        # Quick Stats Row
        with ui.row().classes('w-full gap-4 sm:gap-6 mb-8 flex-wrap'):
            
            with next(get_session()) as session:
                # 1. Fetch Accounts
                accounts = session.exec(select(BankAccount)).all()
                
                # 2. Fetch All Operations (In future: Filter by year)
                ops = session.exec(select(Operation)).all()
                
                # 3. Calculate Totals
                total_income = Decimal("0.00")
                total_expense = Decimal("0.00")
                
                # Track balance per account
                account_balances = {a.id: a.initial_balance for a in accounts}
                
                for op in ops:
                    if op.type == OperationType.ENTREE:
                        total_income += op.amount
                        if op.bank_account_id in account_balances:
                            account_balances[op.bank_account_id] += op.amount
                    else:
                        total_expense += op.amount
                        if op.bank_account_id in account_balances:
                            account_balances[op.bank_account_id] -= op.amount
                            
                global_balance = sum(account_balances.values())

            # Stat Card 1
            with ui.card().classes('w-full sm:w-64 p-4 glass-panel border-none flex-grow'):
                with ui.row().classes('items-center justify-between mb-2'):
                    ui.label('Solde Total').classes('text-sm text-slate-400 font-medium')
                    ui.icon('account_balance_wallet').classes('text-emerald-400 bg-emerald-400/10 p-2 rounded-lg')
                ui.label(format_currency(global_balance)).classes('text-xl font-bold dark:text-white')

            # Stat Card 2
            with ui.card().classes('w-full sm:w-64 p-4 glass-panel border-none flex-grow'):
                with ui.row().classes('items-center justify-between mb-2'):
                    ui.label('Entrées').classes('text-sm text-slate-400 font-medium')
                    ui.icon('trending_up').classes('text-cyan-400 bg-cyan-400/10 p-2 rounded-lg')
                ui.label(format_currency(total_income)).classes('text-xl font-bold dark:text-white')

            # Stat Card 3
            with ui.card().classes('w-full sm:w-64 p-4 glass-panel border-none flex-grow'):
                with ui.row().classes('items-center justify-between mb-2'):
                    ui.label('Sorties').classes('text-sm text-slate-400 font-medium')
                    ui.icon('trending_down').classes('text-rose-400 bg-rose-400/10 p-2 rounded-lg')
                ui.label(format_currency(total_expense)).classes('text-xl font-bold dark:text-white')
        
        # Accounts Overview
        ui.label('Vos Comptes').classes('text-xl font-bold dark:text-white mb-4')
        
        with ui.row().classes('w-full gap-4 flex-wrap'):
             for acc in accounts:
                 current_bal = account_balances.get(acc.id, acc.initial_balance)
                 with ui.card().classes('glass-panel border-none p-4 flex-grow min-w-[280px]'):
                     ui.label(acc.name).classes('font-bold text-lg mb-1')
                     ui.label(f'IBAN: {acc.iban or "?"}').classes('text-xs text-slate-400 mb-4')
                     color = 'text-emerald-400' if current_bal >= 0 else 'text-rose-400'
                     ui.label(format_currency(current_bal, show_sign=True)).classes(f'text-xl font-bold {color} whitespace-nowrap')

        ui.label('Activité Récente').classes('text-xl font-bold dark:text-white mt-8 mb-4')
        with ui.card().classes('w-full glass-panel border-none p-0'):
            # Latest 5 ops
            recent_ops = sorted(ops, key=lambda x: x.date, reverse=True)[:5]
            
            columns = [
                {'name': 'date', 'label': 'Date', 'field': 'date', 'align': 'left'},
                {'name': 'label', 'label': 'Libellé', 'field': 'label', 'align': 'left'},
                {'name': 'amount', 'label': 'Montant', 'field': 'amount_fmt', 'align': 'right'},
            ]
            rows = []
            for o in recent_ops:
                sign = -1 if o.type == OperationType.SORTIE else 1
                rows.append({
                    'date': o.date.isoformat(),
                    'label': o.label,
                    'amount_fmt': format_currency(o.amount * sign, show_sign=True)
                })
                
            ui.table(columns=columns, rows=rows, pagination=5).classes('w-full no-shadow dark:text-white bg-transparent')

    frame("Tableau de bord", content)
