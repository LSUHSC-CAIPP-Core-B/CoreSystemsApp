from flask import render_template, request
from flask_login import login_required
import matplotlib
from app.CoreB.graphs.invoice_dashboard import bp

import os
from datetime import datetime
import base64
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
matplotlib.use('agg')
from app.utils.db_utils import db_utils

@bp.route('/invoice_dashboard', methods=['GET'])
@login_required
def invoice_dashboard():
    if request.method == 'GET':
        df = db_utils.toDataframe("SELECT * FROM Invoice", 'app/Credentials/CoreB.json')
        build_dashboard(df, 'app/templates/CoreB/graphs/InvoiceDashboard.html')
        return render_template('CoreB/graphs/InvoiceDashboard.html')
    
def find_col(candidates, cols):
    cols_l = [c.lower() for c in cols]
    for cand in candidates:
        if cand.lower() in cols_l:
            return cols[cols_l.index(cand.lower())]
    for c in cols:
        cl = c.lower()
        for cand in candidates:
            if cand.lower() in cl:
                return c
    return None

def ensure_numeric(series):
    return pd.to_numeric(series, errors="coerce")

def save_fig(path):
    plt.tight_layout()
    plt.savefig(path, dpi=160, bbox_inches="tight")
    plt.close()

def to_base64_img(path):
    with open(path, "rb") as f:
        b = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/png;base64,{b}"

def df_to_html_table(df, classes="table"):
    headers = "".join(f"<th>{h}</th>" for h in df.columns)
    rows = []
    for _, r in df.iterrows():
        rows.append("<tr>" + "".join(f"<td>{r[c]}</td>" for c in df.columns) + "</tr>")
    return f"""
    <table class="{classes}">
      <thead><tr>{headers}</tr></thead>
      <tbody>
        {''.join(rows)}
      </tbody>
    </table>
    """

def to_bool_counts_yes_no(series):
    """Return counts (yes, no) from a free-form 'Yes/No-ish' column."""
    s = series.astype(str).str.strip().str.lower()
    yes_set = {"yes","y","true","1","paid","billed","bill"}
    no_set  = {"no","n","false","0","unpaid","not paid","not billed","unbilled"}
    yes = s.isin(yes_set).sum()
    no  = s.isin(no_set).sum()
    # Treat other non-empty values as No
    ambiguous = (s.notna() & (s != "") & ~s.isin(yes_set | no_set)).sum()
    no += int(ambiguous)
    return int(yes), int(no)

def build_dashboard(df_raw, html_out):
    # Exclude BioRender anywhere
    mask_bio = df_raw.astype(str).apply(lambda col: col.str.contains("biorender", case=False, na=False))
    df = df_raw.loc[~mask_bio.any(axis=1)].copy()
    bio_df = df_raw.loc[mask_bio.any(axis=1)].copy()

    cols = list(df.columns)

    # Key columns (explicit first, then fuzzy)
    date_col = "Invoice Date" if "Invoice Date" in df.columns else find_col(["invoice date","date","issued","created","invoice_date"], cols)
    amount_col = "Amount" if "Amount" in df.columns else find_col(["amount","total","invoice amount","grand total","subtotal","balance"], cols)
    paid_col = "Paid" if "Paid" in df.columns else find_col(["paid"], cols)
    bill_col = "Bill" if "Bill" in df.columns else find_col(["bill","billed"], cols)
    service_col = "Service Type" if "Service Type" in df.columns else find_col(["service type","service","category"], cols)

    # Normalize
    dfw = df.copy()
    if date_col:
        dfw[date_col] = pd.to_datetime(dfw[date_col], errors="coerce")
        dfw["_inv_month"] = dfw[date_col].dt.to_period("M").dt.to_timestamp()

    if amount_col:
        dfw["_amount"] = ensure_numeric(dfw[amount_col])
    else:
        dfw["_amount"] = np.nan

    # KPIs
    total_invoices = len(dfw)
    total_amount = float(dfw["_amount"].sum(skipna=True)) if amount_col else 0.0
    excluded_count = len(df_raw) - len(df)
    bio_amount = float(pd.to_numeric(bio_df[amount_col], errors="coerce").sum()) if amount_col and amount_col in bio_df.columns else 0.0

    summary_rows = [
        ("Total Invoices", f"{total_invoices:,}"),
        ("Revenue", f"{total_amount:,.2f}"),
        ("BioRender", f"{excluded_count:,}"),
        ("BioRender Fee ", f"{bio_amount:,.2f}")
    ]
    summary_df = pd.DataFrame(summary_rows, columns=["Metric","Value"])
    summary_html = df_to_html_table(summary_df, classes="table kpi")

    # Figures — dict to avoid duplicates
    out_dir = os.path.dirname(html_out) or "."
    images = {}
    def add_card(title, data_uri): images[title] = data_uri
    
    # Invoices over Time
    if date_col and dfw["_inv_month"].notna().any():
        ts = dfw.dropna(subset=["_inv_month"]).groupby("_inv_month").size().reset_index(name="invoices")
        plt.figure()
        plt.plot(ts["_inv_month"], ts["invoices"])
        plt.title("Invoices over Time"); plt.xlabel("Month"); plt.ylabel("Invoices")
        p = os.path.join(out_dir, "inv_over_time.png"); save_fig(p); add_card("Invoices over Time", to_base64_img(p))

    # Billed Amount over Time
    if date_col and amount_col and dfw["_inv_month"].notna().any():
        ts_amt = dfw.dropna(subset=["_inv_month"]).groupby("_inv_month")["_amount"].sum().reset_index()
        plt.figure()
        plt.plot(ts_amt["_inv_month"], ts_amt["_amount"])
        plt.title("Billed Amount over Time"); plt.xlabel("Month"); plt.ylabel("Amount")
        p = os.path.join(out_dir, "billed_over_time.png"); save_fig(p); add_card("Billed Amount over Time", to_base64_img(p))

    # Invoices by Service Type
    if service_col:
        sc = dfw[service_col].astype(str).value_counts()
        if len(sc) > 0:
            plt.figure(figsize=(6, max(3, 0.3*len(sc))))
            sc.sort_values().plot(kind="barh")
            plt.title("Invoices by Service Type"); plt.xlabel("Invoices")
            p = os.path.join(out_dir, "invoices_by_service.png"); save_fig(p); add_card("Invoices by Service Type", to_base64_img(p))

    # Billed pie
    if bill_col:
        y, n = to_bool_counts_yes_no(dfw[bill_col])
        plt.figure()
        plt.pie([y, n], labels=["Billed (Yes)", "Not Billed"], autopct="%1.1f%%", startangle=90)
        plt.title("Billed (Yes) vs Not Billed")
        p = os.path.join(out_dir, "billed_yes_not.png"); save_fig(p); add_card("Billed (Yes) vs Not Billed", to_base64_img(p))

    # Paid pie
    if paid_col:
        y, n = to_bool_counts_yes_no(dfw[paid_col])
        plt.figure()
        plt.pie([y, n], labels=["Paid (Yes)", "Not Paid"], autopct="%1.1f%%", startangle=90)
        plt.title("Paid (Yes) vs Not Paid")
        p = os.path.join(out_dir, "paid_yes_not.png"); save_fig(p); add_card("Paid (Yes) vs Not Paid", to_base64_img(p))

    # Cards HTML
    cards_html = "".join(
        f"""
        <div class="card">
          <div class="card-header">{title}</div>
          <img src="{data_uri}" alt="{title}" class="card-img" />
        </div>
        """
        for title, data_uri in images.items()
    )

    # Full HTML
    html = f"""
    {{% extends 'base.html' %}}
    {{% block content %}}
    <style>
    :root {{ --bg:#f7f7f8; --panel:#fff; --text:#111; --muted:#666; --border:#e6e6e8; --shadow:0 2px 10px rgba(0,0,0,0.06);}}
    .container {{ display: grid; grid-template-columns: 280px 1fr; gap: 24px; align-items: start; }}
    .grid {{ display:grid; gap:16px; grid-template-columns:repeat(auto-fill, minmax(640px, 1fr)); }}
    .card {{ background:var(--panel); border:1px solid var(--border); border-radius:14px; overflow:hidden; box-shadow:var(--shadow);}}
    .card-header {{ padding:12px 14px; font-weight:600; border-bottom:1px solid var(--border); background:#fafafb;}}
    .card-img {{ width:100%; display:block; height:auto;}}
    .panel {{
      background: var(--panel); border: 1px solid var(--border); border-radius: 14px; padding: 16px; box-shadow: var(--shadow);
    }}
    .section-title {{ font-size: 16px; font-weight: 700; margin: 0 0 12px; }}
    p.lead {{ margin: 0 0 20px; color: var(--muted); }}
    .kpi td:first-child {{ width:60%; }}
    </style>
    <body>
      <div class="header" id="gradheader">
        <h1 class="header_text">Invoice Analysis Dashboard</h1>
        <h2 class="header_text">BioRender invoices excluded. KPIs and charts derived from your Invoices.csv</h2>
      </div>
      <div class="container">
        <div class="sidebar">
          <div class="panel" style="margin-bottom:16px;">
            <div class="section-title">Summary</div>
            {summary_html}
          </div>
        </div>
        <div class="main">
          <div class="grid">
            {cards_html if cards_html.strip() else '<div class="panel"><div class="section-title">No charts available</div><p>Could not infer required columns.</p></div>'}
          </div>
        </div>
      </div>
      <div class="footer">Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div>
    </body>
    </html>
    {{% endblock %}}
    """
    with open(html_out, "w", encoding="utf-8") as f:
        f.write(html)
    return html_out