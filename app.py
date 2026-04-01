import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(page_title="Cash Dashboard", layout="wide")

st.markdown("""
<style>
p, div, h2, h3, h4, h5, h6, span {
  margin-top: 0 !important;
  margin-bottom: 0 !important;
  line-height: 1.2 !important;
}
h1 {
  margin-top: 0rem !important;
  margin-bottom: 0rem !important;
  font-size: 2rem !important;
}
.footer {
  text-align: center;
  font-size: 14px;
  margin-top: 0.3rem;
  color: #555;
}
body, .main {
  padding-top: 0.3rem !important;
  padding-bottom: 0.3rem !important;
  padding-left: 0.3rem !important;
  padding-right: 0.3rem !important;
}
.block-container {
  padding-top: 1rem !important;
  padding-bottom: 0.2rem !important;
  padding-left: 1rem !important;
  padding-right: 1rem !important;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# HELPERS
# =========================================================
def fmt_number(x):
    if pd.isna(x):
        return "-"
    return f"{x:,.0f}".replace(",", ".")

def get_bank_colors(banks):
    bank_color_map = {
        "BRI": "#0A3185",
        "BSI": "#00A39D",
        "BTN": "#0057B8",
        "BNI": "#F37021",
        "MANDIRI": "#002F6C",
        "CIMB": "#990000",
        "BJB": "#AB9B56",
        "BCA": "#00529B",
        "RAYA": "#00549A",
        "BTN SYARIAH": "#FFC20E",
        "BRI USD": "#0A3185",
        "BCA SYARIAH": "#00529B",
    }
    fallback_colors = ["#999999", "#BBBBBB", "#CCCCCC"]
    return [
        bank_color_map.get(str(bank).upper(), fallback_colors[i % len(fallback_colors)])
        for i, bank in enumerate(banks)
    ]

@st.cache_data(ttl=300)
def load_data(sheet_id):
    url_saldo = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=SALDO"
    url_cf = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=CASHFLOW"

    df_saldo = pd.read_csv(url_saldo)
    df_cf = pd.read_csv(url_cf)

    df_saldo.columns = [str(c).strip().upper() for c in df_saldo.columns]
    df_cf.columns = [str(c).strip().upper() for c in df_cf.columns]

    return df_saldo, df_cf

# =========================================================
# LOAD DATA
# =========================================================
sheet_id = "1vTzm9o_m2wwiiS4jWPbP-nMmelIwJCSonBx-pmiN2Q0"

try:
    df_saldo, df_cf = load_data(sheet_id)
except Exception as e:
    st.error(f"Gagal memuat data Google Sheets: {e}")
    st.stop()

required_saldo_cols = ["TANGGAL", "BANK", "JENIS SALDO", "SALDO", "RATE (%)", "KETERANGAN"]
required_cf_cols = ["TANGGAL", "CASH IN", "CASH OUT", "NET"]

missing_saldo = [c for c in required_saldo_cols if c not in df_saldo.columns]
missing_cf = [c for c in required_cf_cols if c not in df_cf.columns]

if missing_saldo:
    st.error(f"Kolom sheet SALDO tidak lengkap. Kolom yang belum ada: {', '.join(missing_saldo)}")
    st.stop()

if missing_cf:
    st.error(f"Kolom sheet CASHFLOW tidak lengkap. Kolom yang belum ada: {', '.join(missing_cf)}")
    st.stop()

# =========================================================
# PREPARE DATA
# =========================================================
df_saldo["TANGGAL"] = pd.to_datetime(df_saldo["TANGGAL"], dayfirst=True, errors="coerce")
df_cf["TANGGAL"] = pd.to_datetime(df_cf["TANGGAL"], dayfirst=True, errors="coerce")

df_saldo["SALDO"] = pd.to_numeric(df_saldo["SALDO"], errors="coerce").fillna(0)
df_saldo["RATE (%)"] = pd.to_numeric(df_saldo["RATE (%)"], errors="coerce")

for col in ["CASH IN", "CASH OUT", "NET"]:
    df_cf[col] = pd.to_numeric(df_cf[col], errors="coerce").fillna(0)

df_saldo["JENIS SALDO"] = df_saldo["JENIS SALDO"].astype(str).str.upper().str.strip()
df_saldo["BANK"] = df_saldo["BANK"].astype(str).str.upper().str.strip()
df_saldo["KETERANGAN"] = df_saldo["KETERANGAN"].astype(str).str.upper().str.strip()

latest_date = df_saldo["TANGGAL"].max()
if pd.isna(latest_date):
    st.error("Kolom TANGGAL pada sheet SALDO tidak dapat dibaca.")
    st.stop()

saldo_latest = df_saldo[df_saldo["TANGGAL"] == latest_date].copy()
update_info = latest_date.strftime("%d %B %Y")
custom_colors = px.colors.qualitative.Dark2

# =========================================================
# HEADER
# =========================================================
col_logo, col_title = st.columns([1, 6])

with col_logo:
    if os.path.exists("asdp-logo.png"):
        st.image("asdp-logo.png", width=80)
    else:
        st.caption("Logo tidak ditemukan")

with col_title:
    st.markdown(
        "<h1 style='text-align:center; margin-bottom:0;'>Cash and Cash Equivalents Ending Balance Dashboard</h1>",
        unsafe_allow_html=True
    )

st.markdown(
    f"<p style='text-align:left; font-size:14px; margin-top:0.2rem;'><i>Data per {update_info}</i></p>",
    unsafe_allow_html=True
)
st.markdown(
    "<p style='text-align:left; font-size:13px; margin-top:-0.3rem;'><i>(Dalam Miliar Rupiah)</i></p>",
    unsafe_allow_html=True
)

# =========================================================
# PIVOT TABLE SALDO
# =========================================================
pivot = (
    saldo_latest.pivot_table(
        index="BANK",
        columns="JENIS SALDO",
        values="SALDO",
        aggfunc="sum",
        fill_value=0
    )
    .reset_index()
)

for col in ["GIRO", "DEPOSITO"]:
    if col not in pivot.columns:
        pivot[col] = 0

pivot["TOTAL SALDO"] = pivot["GIRO"] + pivot["DEPOSITO"]
pivot = pivot[["BANK", "GIRO", "DEPOSITO", "TOTAL SALDO"]]
pivot = pivot.sort_values(by="TOTAL SALDO", ascending=False).reset_index(drop=True)

grand_total = pd.DataFrame({
    "BANK": ["GRAND TOTAL"],
    "GIRO": [pivot["GIRO"].sum()],
    "DEPOSITO": [pivot["DEPOSITO"].sum()],
    "TOTAL SALDO": [pivot["TOTAL SALDO"].sum()]
})

pivot_display = pd.concat([pivot, grand_total], ignore_index=True)
pivot_display[["GIRO", "DEPOSITO", "TOTAL SALDO"]] = (
    pivot_display[["GIRO", "DEPOSITO", "TOTAL SALDO"]]
    .fillna(0)
    .round(0)
    .astype(int)
)

def highlight_grand_total(row):
    style = "font-weight: bold; background-color: #f0f0f0" if row.name == len(pivot_display) - 1 else ""
    return [style] * len(row)

styled_table = (
    pivot_display.style
    .format({
        "GIRO": lambda x: fmt_number(x),
        "DEPOSITO": lambda x: fmt_number(x),
        "TOTAL SALDO": lambda x: fmt_number(x),
    })
    .apply(highlight_grand_total, axis=1)
)

# =========================================================
# LAYOUT
# =========================================================
col1, col2, col3 = st.columns([1.2, 1.2, 1.6])

with col1:
    st.markdown("#### Saldo per Bank")
    st.dataframe(styled_table, use_container_width=True, hide_index=True, height=490)

    st.markdown("#### Restricted Cash and Cash Equivalents")

    summary = (
        saldo_latest.groupby(["JENIS SALDO", "KETERANGAN"])["SALDO"]
        .sum()
        .unstack(fill_value=0)
    )

    summary = summary.reindex(columns=["RESTRICTED", "NON RESTRICTED"], fill_value=0)
    summary["TOTAL"] = summary.sum(axis=1)
    summary = summary[["RESTRICTED", "NON RESTRICTED", "TOTAL"]]

    summary_formatted = summary.apply(lambda col: col.map(fmt_number))

    st.dataframe(summary_formatted, use_container_width=True, height=140)

with col2:
    st.markdown("### Persentase GIRO per Bank")
    giro_data = pivot[pivot["GIRO"] > 0].copy()

    if not giro_data.empty:
        giro_colors = get_bank_colors(giro_data["BANK"].tolist())
        fig_giro = px.pie(giro_data, names="BANK", values="GIRO", hole=0.4)
        fig_giro.update_traces(marker=dict(colors=giro_colors), textinfo="percent+label")
        fig_giro.update_layout(showlegend=False)
        st.plotly_chart(fig_giro, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Data GIRO tidak tersedia untuk tanggal terbaru.")

    st.markdown("### Persentase DEPOSITO per Bank")
    deposito_data = saldo_latest[saldo_latest["JENIS SALDO"] == "DEPOSITO"].copy()
    deposito_data = deposito_data.dropna(subset=["RATE (%)"])

    if not deposito_data.empty:
        min_rate = float(deposito_data["RATE (%)"].min())
        max_rate = float(deposito_data["RATE (%)"].max())

        rate_range = st.slider(
            "Filter berdasarkan Rate (%)",
            min_value=min_rate,
            max_value=max_rate,
            value=(min_rate, max_rate)
        )

        deposito_filtered = deposito_data[
            deposito_data["RATE (%)"].between(rate_range[0], rate_range[1])
        ]
        deposito_grouped = deposito_filtered.groupby("BANK", as_index=False)["SALDO"].sum()

        if not deposito_grouped.empty:
            depo_colors = get_bank_colors(deposito_grouped["BANK"].tolist())
            fig_depo = px.pie(deposito_grouped, names="BANK", values="SALDO", hole=0.4)
            fig_depo.update_traces(marker=dict(colors=depo_colors), textinfo="percent+label")
            fig_depo.update_layout(showlegend=False)
            st.plotly_chart(fig_depo, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Tidak ada data deposito pada rentang rate yang dipilih.")
    else:
        st.info("Data deposito atau RATE (%) tidak tersedia.")

with col3:
    st.markdown("### Grafik Tren Cash and Cash Equivalents (12 Bulan Terakhir)")
    df_saldo["BULAN"] = df_saldo["TANGGAL"].dt.to_period("M").dt.to_timestamp()

    monthly = (
        df_saldo.groupby(["BULAN", "JENIS SALDO"])["SALDO"]
        .sum()
        .unstack(fill_value=0)
        .sort_index()
    )
    monthly["TOTAL"] = monthly.sum(axis=1)

    last_12 = monthly.tail(12).reset_index()
    last_12["BULAN_LABEL"] = last_12["BULAN"].dt.strftime("%b %Y")

    fig_line = go.Figure()
    fig_line.add_trace(
        go.Scatter(
            x=last_12["BULAN_LABEL"],
            y=last_12["TOTAL"],
            mode="lines+markers+text",
            name="TOTAL SALDO",
            text=last_12["TOTAL"].apply(fmt_number),
            textposition="top center",
            line=dict(color=custom_colors[0])
        )
    )
    fig_line.update_layout(yaxis_title="Saldo", xaxis_title="BULAN")
    st.plotly_chart(fig_line, use_container_width=True, config={"displayModeBar": False})

    st.markdown("### Grafik CASH IN / OUT (12 Bulan Terakhir)")
    df_cf["BULAN"] = df_cf["TANGGAL"].dt.to_period("M").dt.to_timestamp()

    cash_pivot = (
        df_cf.groupby("BULAN")[["CASH IN", "CASH OUT", "NET"]]
        .sum()
        .sort_index()
        .tail(12)
        .reset_index()
    )
    cash_pivot["BULAN_LABEL"] = cash_pivot["BULAN"].dt.strftime("%b %Y")

    fig_combo = go.Figure()
    fig_combo.add_trace(go.Bar(
        x=cash_pivot["BULAN_LABEL"],
        y=cash_pivot["CASH IN"],
        name="CASH IN",
        marker_color=custom_colors[1]
    ))
    fig_combo.add_trace(go.Bar(
        x=cash_pivot["BULAN_LABEL"],
        y=cash_pivot["CASH OUT"],
        name="CASH OUT",
        marker_color=custom_colors[2]
    ))
    fig_combo.add_trace(go.Scatter(
        x=cash_pivot["BULAN_LABEL"],
        y=cash_pivot["NET"],
        name="NET",
        mode="lines+markers+text",
        text=cash_pivot["NET"].apply(fmt_number),
        textposition="top center",
        line=dict(color="black"),
        textfont=dict(color="black")
    ))
    fig_combo.update_layout(barmode="group", xaxis_title="BULAN", yaxis_title="Cash in/Out")
    st.plotly_chart(fig_combo, use_container_width=True, config={"displayModeBar": False})

# =========================================================
# FOOTER
# =========================================================
st.markdown(
    """<div class="footer">Created by Nur Vita Anjaningrum</div>""",
    unsafe_allow_html=True
)
