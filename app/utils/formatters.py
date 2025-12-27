from decimal import Decimal

def format_currency(amount: Decimal, show_sign: bool = False, include_symbol: bool = True) -> str:
    """
    Formats a Decimal as a string with European conventions:
    - Dot (.) for thousands separator
    - Comma (,) for decimal separator
    - Fixed 2 decimal places
    - Optional ' €' symbol
    Example: 1234.56 -> "1.234,56 €"
    """
    if amount is None:
        return ""
    
    # Use standard format with US separators first (comma for thousands, dot for decimals)
    fmt = "+,.2f" if show_sign else ",.2f"
    s = format(amount, fmt)
    
    # Swap separators: , -> temp, . -> ,, temp -> .
    s = s.replace(',', 'X').replace('.', ',').replace('X', '.')
    
    return f"{s} €" if include_symbol else s
