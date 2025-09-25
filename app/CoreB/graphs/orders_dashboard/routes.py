from flask import render_template, request
from flask_login import login_required
import matplotlib
from app.CoreB.graphs.orders_dashboard import bp

import os
from datetime import datetime
import base64
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
matplotlib.use('agg')
from app.utils.db_utils import db_utils

@bp.route('/orders_dashboard', methods=['GET'])
@login_required
def orders_dashboard():
    if request.method == 'GET':
        df = db_utils.toDataframe("SELECT * FROM CoreB_Order", 'db_config/CoreB.json')
        build_dashboard(df, 'app/templates/CoreB/graphs/OrdersDashboard.html')
        return render_template('CoreB/graphs/OrdersDashboard.html')

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

def build_dashboard(df, html_out_path):
    cols = list(df.columns)

    # Detect columns
    date_col = find_col(["order date","date","order_date","created","timestamp","datetime"], cols)
    product_col = find_col(["product","item","sku","product name","product_name"], cols)
    category_col = find_col(["category","type","segment","class"], cols)
    region_col = find_col(["region","country","state","city","zone","market","area"], cols)
    status_col = find_col(["status","order status","fulfillment","shipment status"], cols)
    qty_col = find_col(["quantity","qty","units","count"], cols)
    price_col = find_col(["price","unit price","unit_price","amount per unit","unitcost","unit cost"], cols)
    total_col = find_col(["total","sales","revenue","amount","order total","subtotal","grand total"], cols)
    pi_col = find_col(["pi name","principal investigator","pi"], cols)
    funding_col = find_col(["funding source","funding","sponsor"], cols)
    service_col = find_col(["service type","service","type of service"], cols)

    # Exclude "biorender" anywhere
    mask_biorender = df.astype(str).apply(lambda col: col.str.contains("biorender", case=False, na=False))
    df = df.loc[~mask_biorender.any(axis=1)].copy()

    # Normalize
    if date_col:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df["_order_day"] = df[date_col].dt.date

    df["_qty"] = ensure_numeric(df[qty_col]) if qty_col else np.nan
    df["_price"] = ensure_numeric(df[price_col]) if price_col else np.nan
    df["_total"] = ensure_numeric(df[total_col]) if total_col else np.nan

    if df["_total"].notna().any():
        df["_revenue"] = df["_total"]
    elif df[["_qty","_price"]].notna().all(axis=1).any():
        df["_revenue"] = df["_qty"] * df["_price"]
    else:
        df["_revenue"] = 1.0  # fallback count

    # KPIs
    n_orders = len(df)
    summary_rows = [("Total Orders", f"{n_orders:,}")]
    if pi_col:
        n_pis = df[pi_col].nunique()
        summary_rows.append(("Unique PIs", f"{n_pis:,}"))
    summary_df = pd.DataFrame(summary_rows, columns=["Metric","Value"])
    summary_html = df_to_html_table(summary_df, classes="table kpi")

    # Figures
    out_dir = os.path.dirname(html_out_path) or "."
    images = {}
    def add_card(title, data_uri):
        images[title] = data_uri

    # Orders over time
    if date_col and df["_order_day"].notna().any():
        ts = df.dropna(subset=["_order_day"]).groupby("_order_day").size().reset_index(name="orders")
        plt.figure()
        plt.plot(ts["_order_day"], ts["orders"])
        plt.title("Orders over Time")
        plt.xlabel("Date"); plt.ylabel("Orders")
        path = os.path.join(out_dir, "orders_over_time.png"); save_fig(path)
        add_card("Orders over Time", to_base64_img(path))

    # Orders by Category
    if category_col:
        cat_counts = df[category_col].astype(str).value_counts().head(20)
        if len(cat_counts)>0:
            plt.figure(figsize=(6,max(3,0.3*len(cat_counts))))
            cat_counts.sort_values().plot(kind="barh")
            plt.title(f"Orders by {category_col}"); plt.xlabel("Orders")
            path=os.path.join(out_dir,"orders_by_category.png"); save_fig(path)
            add_card(f"Orders by {category_col}", to_base64_img(path))

    # Top Products by Revenue
    if product_col:
        prod = df.groupby(product_col)["_revenue"].sum().sort_values(ascending=False).head(15)
        if len(prod)>0:
            plt.figure(figsize=(6,max(3,0.3*len(prod))))
            prod.sort_values().plot(kind="barh")
            plt.title("Top Products by Revenue"); plt.xlabel("Revenue")
            path=os.path.join(out_dir,"top_products.png"); save_fig(path)
            add_card("Top Products by Revenue", to_base64_img(path))

    # Orders by Region
    if region_col:
        reg = df[region_col].astype(str).value_counts().head(20)
        if len(reg)>0:
            plt.figure(figsize=(6,max(3,0.3*len(reg))))
            reg.sort_values().plot(kind="barh")
            plt.title(f"Orders by {region_col}"); plt.xlabel("Orders")
            path=os.path.join(out_dir,"orders_by_region.png"); save_fig(path)
            add_card(f"Orders by {region_col}", to_base64_img(path))

    # Status breakdown
    if status_col:
        st = df[status_col].astype(str).value_counts().head(10)
        if len(st)>0:
            plt.figure()
            plt.pie(st.values, labels=st.index, autopct="%1.1f%%", startangle=90)
            plt.title(f"{status_col} Breakdown")
            path=os.path.join(out_dir,"status_breakdown.png"); save_fig(path)
            add_card(f"{status_col} Breakdown", to_base64_img(path))

    # Top PIs by Orders
    if pi_col:
        top_pis = df[pi_col].astype(str).value_counts().head(15)
        if len(top_pis)>0:
            plt.figure(figsize=(6,max(3,0.3*len(top_pis))))
            top_pis.sort_values().plot(kind="barh")
            plt.title("Top PIs by Number of Orders"); plt.xlabel("Orders")
            path=os.path.join(out_dir,"top_pis_by_orders.png"); save_fig(path)
            add_card("Top PIs by Number of Orders", to_base64_img(path))

    # Funding breakdown (NIH incl NIGMS, R01/RO1, COBRE; NSF; DoD incl DARPA; NASA; Other)
    if funding_col:
        F = df[funding_col].astype(str).str.upper()
        def classify_funding(x):
            if any(tag in x for tag in ["NIH","NIGMS","R01","RO1","COBRE"]):
                return "NIH"
            elif "NSF" in x:
                return "NSF"
            elif ("DOD" in x) or ("DEPARTMENT OF DEFENSE" in x) or ("DARPA" in x):
                return "DoD"
            elif "NASA" in x:
                return "NASA"
            else:
                return "Other"
        funding_cat = F.apply(classify_funding)
        funding_counts = funding_cat.value_counts()
        if len(funding_counts)>0:
            plt.figure()
            plt.pie(funding_counts.values, labels=funding_counts.index, autopct="%1.1f%%", startangle=90)
            plt.title("Funding Source Breakdown (NIH, NSF, DoD, NASA, Other)")
            path=os.path.join(out_dir,"funding_breakdown.png"); save_fig(path)
            add_card("Funding Source Breakdown (NIH, NSF, DoD, NASA, Other)", to_base64_img(path))

        # COBRE vs Non-COBRE
        cobre = F.apply(lambda x: "COBRE" if "COBRE" in x else "Non-COBRE")
        cobre_counts = cobre.value_counts()
        if len(cobre_counts)>0:
            plt.figure()
            plt.pie(cobre_counts.values, labels=cobre_counts.index, autopct="%1.1f%%", startangle=90)
            plt.title("Grant Sources: COBRE vs Non-COBRE")
            path=os.path.join(out_dir,"grant_cobre_breakdown.png"); save_fig(path)
            add_card("Grant Sources: COBRE vs Non-COBRE", to_base64_img(path))

    # Orders by Service Type (barh)
    if service_col:
        service_counts = df[service_col].astype(str).value_counts()
        if len(service_counts)>0:
            plt.figure(figsize=(6,max(3,0.3*len(service_counts))))
            service_counts.sort_values().plot(kind="barh")
            plt.title("Orders by Service Type"); plt.xlabel("Orders")
            path=os.path.join(out_dir,"orders_by_service_type_bar.png"); save_fig(path)
            add_card("Orders by Service Type", to_base64_img(path))

    # HTML (model panel style; no Detected Columns block)
    cards_html = "".join(
        f"""
        <div class="card">
          <div class="card-header">{title}</div>
          <img src="{data_uri}" alt="{title}" class="card-img" />
        </div>
        """
        for title, data_uri in images.items()
    )

    sidebar_html = f"""
          <div class="panel" style="margin-bottom:16px;">
            <div class="section-title">Summary</div>
            {summary_html}
          </div>
    """

    html = f"""
    {{% extends 'base.html' %}}
    {{% block content %}}
    <style>
    :root {{
      --bg: #f7f7f8;
      --panel: #ffffff;
      --text: #111;
      --muted: #666;
      --border: #e6e6e8;
      --shadow: 0 2px 10px rgba(0,0,0,0.06);
    }}
    .container {{ display: grid; grid-template-columns: 280px 1fr; gap: 24px; align-items: start; }}
    .grid {{
      display: grid; gap: 16px;
      grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    }}
    .card {{
      background: var(--panel); border: 1px solid var(--border); border-radius: 14px; overflow: hidden; box-shadow: var(--shadow);
    }}
    .card-header {{
      padding: 12px 14px; font-weight: 600; border-bottom: 1px solid var(--border); background: #fafafb;
    }}
    .card-img {{
      width: 100%; display: block; height: auto;
    }}
    .panel {{
      background: var(--panel); border: 1px solid var(--border); border-radius: 14px; padding: 16px; box-shadow: var(--shadow);
    }}
    .section-title {{ font-size: 16px; font-weight: 700; margin: 0 0 12px; }}
    p.lead {{ margin: 0 0 20px; color: var(--muted); }}
    
    </style>
    <body>
    <div class="header" id="gradheader">
      <h1 class="header_text">Orders Dashboard (Excluding Biorender)</h1>
      <h2 class="header_text">Summary and visualizations for order data, excluding Biorender orders.</p>
    </div>
      <div class="container">
        <div class="sidebar">
          {sidebar_html}
        </div>
        <div class="main">
          <div class="grid">
            {cards_html if cards_html.strip() else '<div class="panel"><div class="section-title">No charts available</div><p>Could not infer suitable columns for plotting. Please check the CSV headers.</p></div>'}
          </div>
        </div>
      </div>
      <div class="footer">
        Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
      </div>
    </body>
    </html>
    {{% endblock %}}
    """
    with open(html_out_path, "w", encoding="utf-8") as f:
        f.write(html)
    return html_out_path