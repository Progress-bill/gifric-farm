import io
import csv
import re
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# Standard OpenXML compliant format strings (strictly quoted to prevent Excel repair errors)
CURRENCY_FORMAT = '"$"#,##0.00;("-"$"#,##0.00);"-"'
INT_FORMAT = '#,##0'

def sanitize_excel_text(val):
    """
    Sanitizes string inputs to prevent XML character corruption in Excel.
    Strips illegal non-printable control characters (ASCII 0-8, 11-12, 14-31).
    """
    if val is None:
        return ""
    text = str(val)
    # Remove XML illegal control characters
    text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f]', '', text)
    # Normalize carriage returns
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    return text.strip()

def generate_financial_excel_report(orders, products, cost_ratio=0.55, expense_ratio=0.10, start_date=None, end_date=None):
    """
    Generates a 100% Excel-compliant multi-sheet Workbook (.xlsx) free of character warnings.
    1. Sheet: 'Financial Summary'
    2. Sheet: 'Order Transactions'
    3. Sheet: 'Stock Inventory'
    """
    wb = openpyxl.Workbook()
    default_sheet = wb.active

    # Standard safe fonts & fills
    font_title = Font(name="Calibri", size=15, bold=True, color="14532D")
    font_subtitle = Font(name="Calibri", size=10, italic=True, color="475569")
    font_section = Font(name="Calibri", size=11, bold=True, color="0F172A")
    font_header = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
    font_bold = Font(name="Calibri", size=10, bold=True)
    font_regular = Font(name="Calibri", size=10)
    font_profit = Font(name="Calibri", size=11, bold=True, color="15803D")
    font_loss = Font(name="Calibri", size=11, bold=True, color="B91C1C")

    fill_emerald = PatternFill(start_color="15803D", end_color="15803D", fill_type="solid")
    fill_navy = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
    fill_amber = PatternFill(start_color="D97706", end_color="D97706", fill_type="solid")
    fill_light_green = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid")
    fill_light_gray = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
    fill_light_red = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")

    thin_side = Side(border_style="thin", color="CBD5E1")
    border_box = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)
    double_bottom = Border(bottom=Side(border_style="double", color="0F172A"), top=thin_side, left=thin_side, right=thin_side)

    # -------------------------------------------------------------
    # 1. Sheet 1: Financial Summary (Renamed to avoid '&' in sheet name)
    # -------------------------------------------------------------
    ws_pnl = wb.create_sheet(title="Financial Summary")
    ws_pnl.views.sheetView[0].showGridLines = True

    # Title Block
    ws_pnl["B2"] = "GIFRIC FARM - AGRICULTURAL PRODUCE & POULTRY"
    ws_pnl["B2"].font = font_title
    gen_time_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    ws_pnl["B3"] = f"Official Financial Balance, Order Flow and Profit/Loss Statement (Generated: {gen_time_str})"
    ws_pnl["B3"].font = font_subtitle
    ws_pnl["B4"] = "Motto: To carry on the trade or business of farmers, farm managers, agricultural producers"
    ws_pnl["B4"].font = font_subtitle

    # Calculations
    total_orders_count = len(orders)
    confirmed_orders = [o for o in orders if o.status in ['Confirmed', 'Delivered']]
    pending_orders = [o for o in orders if o.status == 'Pending']
    cancelled_orders = [o for o in orders if o.status == 'Cancelled']

    gross_revenue = sum(o.total_amount for o in orders if o.status != 'Cancelled')
    confirmed_revenue = sum(o.total_amount for o in confirmed_orders)
    pending_revenue = sum(o.total_amount for o in pending_orders)

    ecocash_sales = sum(o.total_amount for o in orders if o.payment_method == 'ecocash' and o.status != 'Cancelled')
    cash_sales = sum(o.total_amount for o in orders if o.payment_method == 'cash' and o.status != 'Cancelled')

    estimated_cogs = gross_revenue * cost_ratio
    estimated_expenses = gross_revenue * expense_ratio
    net_profit = gross_revenue - (estimated_cogs + estimated_expenses)
    profit_margin_pct = (net_profit / gross_revenue * 100) if gross_revenue > 0 else 0.0

    total_stock_units = sum(p.stock_quantity for p in products)
    total_stock_value = sum(p.stock_quantity * p.price for p in products)
    total_assets = confirmed_revenue + total_stock_value

    # Section 1: Revenue & Order Flow Metrics
    ws_pnl["B6"] = "1. ORDER FLOW AND REVENUE BALANCE"
    ws_pnl["B6"].font = font_section

    metrics_rev = [
        ("Total Customer Orders Recorded", total_orders_count, "number"),
        ("Confirmed and Delivered Orders", len(confirmed_orders), "number"),
        ("Pending Orders Awaiting Fulfillment", len(pending_orders), "number"),
        ("Cancelled Orders", len(cancelled_orders), "number"),
        ("Gross Sales Revenue Balance", gross_revenue, "currency"),
        ("Realized Revenue (Confirmed/Delivered)", confirmed_revenue, "currency"),
        ("Pending Revenue in Pipeline", pending_revenue, "currency"),
        ("EcoCash Mobile Collections (+263 77 223 9953)", ecocash_sales, "currency"),
        ("Cash on Delivery (COD) Collections", cash_sales, "currency"),
    ]

    row_idx = 7
    ws_pnl.cell(row=row_idx, column=2, value="Financial Metric").font = font_header
    ws_pnl.cell(row=row_idx, column=2).fill = fill_emerald
    ws_pnl.cell(row=row_idx, column=3, value="Amount / Count").font = font_header
    ws_pnl.cell(row=row_idx, column=3).fill = fill_emerald
    ws_pnl.cell(row=row_idx, column=3).alignment = Alignment(horizontal="right")

    for label, val, val_type in metrics_rev:
        row_idx += 1
        c_label = ws_pnl.cell(row=row_idx, column=2, value=label)
        c_val = ws_pnl.cell(row=row_idx, column=3, value=val)
        c_label.font = font_regular
        c_label.border = border_box
        c_val.font = font_bold
        c_val.border = border_box
        c_val.alignment = Alignment(horizontal="right")
        if val_type == "currency":
            c_val.number_format = CURRENCY_FORMAT
        elif val_type == "number":
            c_val.number_format = INT_FORMAT

    # Section 2: Profit & Loss Statement (P&L)
    row_idx += 3
    ws_pnl.cell(row=row_idx, column=2, value="2. PROFIT AND LOSS STATEMENT (P&L)").font = font_section

    row_idx += 1
    ws_pnl.cell(row=row_idx, column=2, value="Accounting Line Item").font = font_header
    ws_pnl.cell(row=row_idx, column=2).fill = fill_navy
    ws_pnl.cell(row=row_idx, column=3, value="Amount ($)").font = font_header
    ws_pnl.cell(row=row_idx, column=3).fill = fill_navy
    ws_pnl.cell(row=row_idx, column=3).alignment = Alignment(horizontal="right")

    pnl_items = [
        ("Gross Sales Revenue", gross_revenue, "plus", fill_light_gray),
        (f"Less: Cost of Goods Sold / Farm Production ({int(cost_ratio*100)}%)", -estimated_cogs, "minus", None),
        ("Gross Farm Margin", gross_revenue - estimated_cogs, "subtotal", fill_light_gray),
        (f"Less: Operating Expenses ({int(expense_ratio*100)}% packaging and logistics)", -estimated_expenses, "minus", None),
    ]

    for item_name, amt, line_type, fill_color in pnl_items:
        row_idx += 1
        c_item = ws_pnl.cell(row=row_idx, column=2, value=item_name)
        c_amt = ws_pnl.cell(row=row_idx, column=3, value=amt)
        c_item.font = font_bold if line_type == "subtotal" else font_regular
        c_item.border = border_box
        c_amt.font = font_bold if line_type == "subtotal" else font_regular
        c_amt.border = border_box
        c_amt.alignment = Alignment(horizontal="right")
        c_amt.number_format = CURRENCY_FORMAT
        if fill_color:
            c_item.fill = fill_color
            c_amt.fill = fill_color

    # Net Profit / Loss Highlight Row
    row_idx += 1
    status_label = "NET PROFIT (Surplus)" if net_profit >= 0 else "NET LOSS (Deficit)"
    c_net_label = ws_pnl.cell(row=row_idx, column=2, value=f"{status_label} [{profit_margin_pct:.1f}% Margin]")
    c_net_val = ws_pnl.cell(row=row_idx, column=3, value=net_profit)
    c_net_label.font = font_profit if net_profit >= 0 else font_loss
    c_net_label.fill = fill_light_green if net_profit >= 0 else fill_light_red
    c_net_label.border = double_bottom
    c_net_val.font = font_profit if net_profit >= 0 else font_loss
    c_net_val.fill = fill_light_green if net_profit >= 0 else fill_light_red
    c_net_val.border = double_bottom
    c_net_val.alignment = Alignment(horizontal="right")
    c_net_val.number_format = CURRENCY_FORMAT

    # Section 3: Inventory Valuation & Asset Balance
    row_idx += 3
    ws_pnl.cell(row=row_idx, column=2, value="3. INVENTORY VALUATION AND ASSET BALANCE").font = font_section

    row_idx += 1
    ws_pnl.cell(row=row_idx, column=2, value="Asset / Balance Item").font = font_header
    ws_pnl.cell(row=row_idx, column=2).fill = fill_amber
    ws_pnl.cell(row=row_idx, column=3, value="Valuation ($)").font = font_header
    ws_pnl.cell(row=row_idx, column=3).fill = fill_amber
    ws_pnl.cell(row=row_idx, column=3).alignment = Alignment(horizontal="right")

    asset_items = [
        ("Current Farm Stock Remaining in Storage (Units)", total_stock_units, "number"),
        ("Retail Valuation of Current Unsold Inventory", total_stock_value, "currency"),
        ("Realized Liquid Cash / Bank Revenue", confirmed_revenue, "currency"),
        ("Total Farm Asset Balance (Cash + Inventory)", total_assets, "currency"),
    ]

    for a_name, a_val, a_type in asset_items:
        row_idx += 1
        c_aname = ws_pnl.cell(row=row_idx, column=2, value=a_name)
        c_aval = ws_pnl.cell(row=row_idx, column=3, value=a_val)
        c_aname.font = font_regular
        c_aname.border = border_box
        c_aval.font = font_bold
        c_aval.border = border_box
        c_aval.alignment = Alignment(horizontal="right")
        if a_type == "currency":
            c_aval.number_format = CURRENCY_FORMAT
        else:
            c_aval.number_format = INT_FORMAT

    # Auto-adjust column widths
    ws_pnl.column_dimensions["A"].width = 4
    ws_pnl.column_dimensions["B"].width = 52
    ws_pnl.column_dimensions["C"].width = 28

    # -------------------------------------------------------------
    # 2. Sheet 2: Order Transactions (Clean title)
    # -------------------------------------------------------------
    ws_orders = wb.create_sheet(title="Order Transactions")
    ws_orders.views.sheetView[0].showGridLines = True

    order_headers = [
        "Order Code", "Date and Time", "Customer Name", "Phone", "City", 
        "Delivery Address", "Items Ordered", "Total Units", "Order Total ($)", 
        "Payment Method", "Status", "Estimated Cost ($)", "Estimated Net Profit ($)"
    ]

    ws_orders.cell(row=1, column=1, value="GIFRIC FARM - ORDER FLOW AND TRANSACTION HISTORY").font = font_title
    ws_orders.cell(row=2, column=1, value=f"Generated: {gen_time_str} | Total Orders: {len(orders)}").font = font_subtitle

    # Header Row
    for col_num, h_text in enumerate(order_headers, 1):
        cell = ws_orders.cell(row=4, column=col_num, value=h_text)
        cell.font = font_header
        cell.fill = fill_emerald
        cell.alignment = Alignment(horizontal="center" if "Date" in h_text or "Status" in h_text or "Code" in h_text else "left")
        cell.border = border_box

    # Populate Orders
    current_row = 5
    tot_units_sum = 0
    tot_amount_sum = 0.0
    tot_cost_sum = 0.0
    tot_profit_sum = 0.0

    for o in orders:
        items_summary = "; ".join([f"{item.quantity}x {sanitize_excel_text(item.product_name)}" for item in o.items])
        units_count = sum(item.quantity for item in o.items)
        est_cost = o.total_amount * cost_ratio
        est_prof = o.total_amount - (est_cost + (o.total_amount * expense_ratio))

        tot_units_sum += units_count
        tot_amount_sum += o.total_amount
        tot_cost_sum += est_cost
        tot_profit_sum += est_prof

        ws_orders.cell(row=current_row, column=1, value=sanitize_excel_text(o.order_number)).font = font_bold
        ws_orders.cell(row=current_row, column=2, value=o.created_at.strftime('%Y-%m-%d %H:%M'))
        ws_orders.cell(row=current_row, column=3, value=sanitize_excel_text(o.customer_name))
        ws_orders.cell(row=current_row, column=4, value=sanitize_excel_text(o.phone))
        ws_orders.cell(row=current_row, column=5, value=sanitize_excel_text(o.city))
        ws_orders.cell(row=current_row, column=6, value=sanitize_excel_text(o.delivery_address))
        ws_orders.cell(row=current_row, column=7, value=items_summary)
        
        c_units = ws_orders.cell(row=current_row, column=8, value=units_count)
        c_units.alignment = Alignment(horizontal="center")
        c_units.number_format = INT_FORMAT
        
        c_tot = ws_orders.cell(row=current_row, column=9, value=o.total_amount)
        c_tot.number_format = CURRENCY_FORMAT
        c_tot.font = font_bold
        
        ws_orders.cell(row=current_row, column=10, value=sanitize_excel_text(o.payment_method.replace('_', ' ').upper()))
        
        c_stat = ws_orders.cell(row=current_row, column=11, value=sanitize_excel_text(o.status))
        c_stat.alignment = Alignment(horizontal="center")
        if o.status in ['Confirmed', 'Delivered']:
            c_stat.fill = fill_light_green
        elif o.status == 'Cancelled':
            c_stat.fill = fill_light_red

        c_cost = ws_orders.cell(row=current_row, column=12, value=est_cost)
        c_cost.number_format = CURRENCY_FORMAT

        c_prof = ws_orders.cell(row=current_row, column=13, value=est_prof)
        c_prof.number_format = CURRENCY_FORMAT
        c_prof.font = font_bold

        for col_i in range(1, 14):
            ws_orders.cell(row=current_row, column=col_i).border = border_box

        current_row += 1

    # Totals Row (Calculated values + formulas)
    ws_orders.cell(row=current_row, column=1, value="TOTALS").font = font_bold
    ws_orders.cell(row=current_row, column=8, value=tot_units_sum).font = font_bold
    ws_orders.cell(row=current_row, column=8).alignment = Alignment(horizontal="center")
    ws_orders.cell(row=current_row, column=8).number_format = INT_FORMAT
    
    ws_orders.cell(row=current_row, column=9, value=tot_amount_sum).font = font_bold
    ws_orders.cell(row=current_row, column=9).number_format = CURRENCY_FORMAT
    
    ws_orders.cell(row=current_row, column=12, value=tot_cost_sum).font = font_bold
    ws_orders.cell(row=current_row, column=12).number_format = CURRENCY_FORMAT
    
    ws_orders.cell(row=current_row, column=13, value=tot_profit_sum).font = font_bold
    ws_orders.cell(row=current_row, column=13).number_format = CURRENCY_FORMAT
    
    for col_i in range(1, 14):
        c = ws_orders.cell(row=current_row, column=col_i)
        c.border = double_bottom
        c.fill = fill_light_gray

    # Auto-adjust column widths
    for col in ws_orders.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws_orders.column_dimensions[col_letter].width = max(min(max_len + 3, 40), 12)

    # -------------------------------------------------------------
    # 3. Sheet 3: Stock Inventory (Clean title)
    # -------------------------------------------------------------
    ws_stock = wb.create_sheet(title="Stock Inventory")
    ws_stock.views.sheetView[0].showGridLines = True

    stock_headers = [
        "Product ID", "Product Name", "Category", "Selling Price ($)", 
        "Pricing Unit", "Stock Remaining", "Inventory Valuation ($)", "Stock Status"
    ]

    ws_stock.cell(row=1, column=1, value="GIFRIC FARM - LIVE STOCK AND INVENTORY VALUATION").font = font_title
    ws_stock.cell(row=2, column=1, value=f"Live Snapshot: {gen_time_str}").font = font_subtitle

    for col_num, h_text in enumerate(stock_headers, 1):
        cell = ws_stock.cell(row=4, column=col_num, value=h_text)
        cell.font = font_header
        cell.fill = fill_navy
        cell.alignment = Alignment(horizontal="center" if "ID" in h_text or "Status" in h_text else "left")
        cell.border = border_box

    curr_stock_row = 5
    tot_stock_qty_sum = 0
    tot_stock_val_sum = 0.0

    for p in products:
        val = p.stock_quantity * p.price
        tot_stock_qty_sum += p.stock_quantity
        tot_stock_val_sum += val

        ws_stock.cell(row=curr_stock_row, column=1, value=p.id).alignment = Alignment(horizontal="center")
        ws_stock.cell(row=curr_stock_row, column=2, value=sanitize_excel_text(p.name)).font = font_bold
        cat_name = p.category.name if p.category else 'Farm Produce'
        ws_stock.cell(row=curr_stock_row, column=3, value=sanitize_excel_text(cat_name))
        
        c_pr = ws_stock.cell(row=curr_stock_row, column=4, value=p.price)
        c_pr.number_format = CURRENCY_FORMAT
        
        ws_stock.cell(row=curr_stock_row, column=5, value=sanitize_excel_text(p.unit))
        
        c_qty = ws_stock.cell(row=curr_stock_row, column=6, value=p.stock_quantity)
        c_qty.alignment = Alignment(horizontal="center")
        c_qty.font = font_bold
        c_qty.number_format = INT_FORMAT
        
        c_val = ws_stock.cell(row=curr_stock_row, column=7, value=val)
        c_val.number_format = CURRENCY_FORMAT
        c_val.font = font_bold
        
        c_st = ws_stock.cell(row=curr_stock_row, column=8, value="In Stock" if p.stock_quantity > 10 else ("Low Stock" if p.stock_quantity > 0 else "Out of Stock"))
        c_st.alignment = Alignment(horizontal="center")
        if p.stock_quantity <= 0:
            c_st.fill = fill_light_red
        elif p.stock_quantity <= 10:
            c_st.fill = fill_amber

        for col_i in range(1, 9):
            ws_stock.cell(row=curr_stock_row, column=col_i).border = border_box

        curr_stock_row += 1

    # Totals
    ws_stock.cell(row=curr_stock_row, column=2, value="TOTAL INVENTORY VALUATION").font = font_bold
    ws_stock.cell(row=curr_stock_row, column=6, value=tot_stock_qty_sum).font = font_bold
    ws_stock.cell(row=curr_stock_row, column=6).alignment = Alignment(horizontal="center")
    ws_stock.cell(row=curr_stock_row, column=6).number_format = INT_FORMAT
    
    ws_stock.cell(row=curr_stock_row, column=7, value=tot_stock_val_sum).font = font_bold
    ws_stock.cell(row=curr_stock_row, column=7).number_format = CURRENCY_FORMAT
    
    for col_i in range(1, 9):
        c = ws_stock.cell(row=curr_stock_row, column=col_i)
        c.border = double_bottom
        c.fill = fill_light_gray

    for col in ws_stock.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws_stock.column_dimensions[col_letter].width = max(min(max_len + 3, 40), 12)

    # Remove default placeholder sheet
    if default_sheet in wb.worksheets:
        wb.remove(default_sheet)

    # Save to BytesIO
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output

def generate_financial_csv_report(orders, products, cost_ratio=0.55, expense_ratio=0.10):
    """
    Generates a clean UTF-8 BOM CSV representation with financial summary and order records.
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Title & Metadata
    writer.writerow(["GIFRIC FARM - ORDER FLOW, FINANCIAL BALANCE AND PROFIT/LOSS STATEMENT"])
    writer.writerow(["Generated At", datetime.now().strftime('%Y-%m-%d %H:%M')])
    writer.writerow(["Motto", "To carry on the trade or business of farmers, farm managers, agricultural producers"])
    writer.writerow([])

    # Financial Summary
    gross_revenue = sum(o.total_amount for o in orders if o.status != 'Cancelled')
    estimated_cogs = gross_revenue * cost_ratio
    estimated_expenses = gross_revenue * expense_ratio
    net_profit = gross_revenue - (estimated_cogs + estimated_expenses)
    
    writer.writerow(["--- FINANCIAL BALANCE AND P&L SUMMARY ---"])
    writer.writerow(["Total Orders", len(orders)])
    writer.writerow(["Gross Sales Revenue ($)", f"{gross_revenue:.2f}"])
    writer.writerow(["Cost of Goods Sold (COGS)", f"{estimated_cogs:.2f}"])
    writer.writerow(["Operating Expenses", f"{estimated_expenses:.2f}"])
    writer.writerow(["NET PROFIT / LOSS ($)", f"{net_profit:.2f}"])
    writer.writerow([])

    # Orders Header
    writer.writerow(["--- DETAILED ORDER FLOW TRANSACTIONS ---"])
    writer.writerow([
        "Order Code", "Date", "Customer Name", "Phone", "City", 
        "Delivery Address", "Items Ordered", "Total ($)", "Payment Method", "Status"
    ])

    for o in orders:
        items_summary = "; ".join([f"{item.quantity}x {sanitize_excel_text(item.product_name)}" for item in o.items])
        writer.writerow([
            sanitize_excel_text(o.order_number),
            o.created_at.strftime('%Y-%m-%d %H:%M'),
            sanitize_excel_text(o.customer_name),
            sanitize_excel_text(o.phone),
            sanitize_excel_text(o.city),
            sanitize_excel_text(o.delivery_address),
            items_summary,
            f"{o.total_amount:.2f}",
            sanitize_excel_text(o.payment_method.replace('_', ' ').upper()),
            sanitize_excel_text(o.status)
        ])

    return output.getvalue().encode('utf-8-sig')
