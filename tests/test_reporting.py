import pytest
from datetime import date
from decimal import Decimal
from sqlmodel import Session, select
from app.models.domain import Operation, Allocation, Owner, Lot, QuotePart, OperationType, Category
from app.services.accounting import distribute_operation
from app.services.pdf_reports import generate_owner_annual_report

def test_annual_report_calculation(session: Session, test_lot: Lot, test_account):
    # Setup Owners
    owner1 = Owner(name="Propriété A", email="a@test.com")
    owner2 = Owner(name="Propriété B", email="b@test.com")
    session.add(owner1)
    session.add(owner2)
    session.commit()

    # QuoteParts: Owner 1 (100%) until June 30, then Owner 2 (100%) from July 1st
    qp1 = QuotePart(lot_id=test_lot.id, owner_id=owner1.id, numerator=1, denominator=1, 
                    start_date=date(2024, 1, 1), end_date=date(2024, 6, 30))
    qp2 = QuotePart(lot_id=test_lot.id, owner_id=owner2.id, numerator=1, denominator=1, 
                    start_date=date(2024, 7, 1))
    session.add(qp1)
    session.add(qp2)
    session.commit()

    # Operations
    # 1. Jan 10: Sortie 100€ (Owner 1 should get 100%)
    op1 = Operation(date=date(2024, 1, 10), amount=Decimal("100.00"), lot_id=test_lot.id, 
                    bank_account_id=test_account.id, type=OperationType.SORTIE, label="Test Janvier")
    session.add(op1)
    session.flush()
    allocs1 = distribute_operation(session, op1)
    for a in allocs1: session.add(a)

    # 2. Aug 15: Sortie 200€ (Owner 2 should get 100%)
    op2 = Operation(date=date(2024, 8, 15), amount=Decimal("200.00"), lot_id=test_lot.id, 
                    bank_account_id=test_account.id, type=OperationType.SORTIE, label="Test Aout")
    session.add(op2)
    session.flush()
    allocs2 = distribute_operation(session, op2)
    for a in allocs2: session.add(a)

    # 3. 2023 Operation (Should be ignored in 2024 report)
    op3 = Operation(date=date(2023, 12, 31), amount=Decimal("50.00"), lot_id=test_lot.id, 
                    bank_account_id=test_account.id, type=OperationType.SORTIE, label="Test 2023")
    session.add(op3)
    session.flush()
    allocs3 = distribute_operation(session, op3)
    for a in allocs3: session.add(a)
    
    session.commit()

    # Generate Report for Owner 1 in 2024
    # We can't easily "test" the PDF binary content here without a parser, 
    # but we can verify the service doesn't crash and we can test the logic separately if we refactor it.
    # For now, let's just check it runs.
    pdf_bytes = generate_owner_annual_report(session, owner1.id, 2024)
    assert len(pdf_bytes) > 0

    # Verification of data filtering (internal logic check)
    def get_totals(owner_id, year):
        start = date(year, 1, 1)
        end = date(year, 12, 31)
        stmt = select(func.sum(Allocation.amount)).join(Operation).where(
            Allocation.owner_id == owner_id,
            Operation.date >= start,
            Operation.date <= end
        )
        return session.exec(stmt).one() or Decimal("0.00")

    from sqlmodel import func
    total_o1_2024 = get_totals(owner1.id, 2024)
    total_o2_2024 = get_totals(owner2.id, 2024)
    total_o1_2023 = get_totals(owner1.id, 2023)

    assert total_o1_2024 == Decimal("100.00")
    assert total_o2_2024 == Decimal("200.00")
    # Owner 1 has 100% in 2023 too? Yes because no end date on initial parts if we follow logic.
    # Wait, qp1 starts from 2024-01-01. So op3 (2023) has NO matching parts?
    # distribute_operation would return [] allocs.
    assert total_o1_2023 == Decimal("0.00")
