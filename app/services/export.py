import csv
import io
from typing import List
from app.models.domain import Operation, Allocation

def generate_operations_csv(operations: List[Operation]) -> str:
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    
    # Header
    writer.writerow(["Date", "Lot", "Compte", "Type", "Categorie", "Libelle", "Montant", "Paye Par"])
    
    for op in operations:
        paid_by = str(op.paid_by_owner_id) if op.paid_by_owner_id else ""
        writer.writerow([
            op.date.isoformat(),
            op.lot.name if op.lot else "?",
            op.bank_account.name if op.bank_account else "?",
            op.type.value,
            op.category_ref.name if op.category_ref else "-",
            op.label,
            str(op.amount),
            paid_by
        ])
        
    return output.getvalue()

def generate_allocations_csv(allocations: List[Allocation]) -> str:
    """
    Detailed export of allocations.
    """
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    
    writer.writerow(["Date", "Operation", "Lot", "Proprietaire", "Montant"])
    
    for alloc in allocations:
        op = alloc.operation
        writer.writerow([
            op.date.isoformat(),
            op.label,
            op.lot.name if op.lot else "?",
            alloc.owner.name if alloc.owner else "?",
            str(alloc.amount)
        ])
        
    return output.getvalue()
