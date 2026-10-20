import pandas as pd
import streamlit as st
import modelo as m

st.set_page_config(page_title="CaféAndes · Escenarios Schwartz", layout="wide")
st.title("☕ CaféAndes S.A. de C.V. — Planeación por escenarios (Peter Schwartz)")
st.caption("Decisión: invertir MXN 6 millones en una línea de tostado industrial. Organización simulada.")

# ---------------- Barra lateral ----------------
st.sidebar.header("Parámetros generales")
inversion = st.sidebar.number_input("Inversión inicial (MXN)", 1_000_000, 20_000_000, m.INVERSION, 100_000)
tmar = st.sidebar.slider("Tasa de descuento (TMAR)", 0.05, 0.25, m.TMAR, 0.01, format="%.2f")

esc = {}
tabs_side = st.sidebar.tabs(list(m.ESCENARIOS))
for tab, (nombre, p) in zip(tabs_side, m.ESCENARIOS.items()):
    with tab:
        esc[nombre] = dict(
            demanda=st.number_input("Demanda año 1 (kg)", 10_000, 120_000, int(p["demanda"]), 1_000, key=f"d{nombre}"),
            crecimiento=st.slider("Crecimiento anual demanda", -0.05, 0.15, p["crecimiento"], 0.01, key=f"g{nombre}"),
            precio=st.number_input("Precio (MXN/kg)", 150.0, 400.0, p["precio"], 5.0, key=f"p{nombre}"),
            costo_usd=st.number_input("Café verde (USD/kg)", 2.0, 8.0, p["costo_usd"], 0.1, key=f"c{nombre}"),
            tc=st.number_input("Tipo de cambio (MXN/USD)", 15.0, 26.0, p["tc"], 0.5, key=f"t{nombre}"),
            prob=p["prob"],
        )

st.sidebar.subheader("Probabilidades")
pp = st.sidebar.slider("Pesimista", 0.0, 1.0, 0.30, 0.05)
po = st.sidebar.slider("Optimista", 0.0, 1.0 - pp, min(0.20, 1.0 - pp), 0.05)
esc["Pesimista"]["prob"], esc["Optimista"]["prob"] = pp, po
esc["Realista"]["prob"] = round(1 - pp - po, 4)
st.sidebar.write(f"Realista: **{esc['Realista']['prob']:.0%}**")

res, ev = m.comparativa(esc, tmar, inversion)

# ---------------- Tabla comparativa ----------------
st.subheader("Tabla comparativa de escenarios")
comp = pd.DataFrame({
    n: {
        "Probabilidad": f"{esc[n]['prob']:.0%}",
        "Costo unitario (MXN/kg)": f"{r['costo_unit']:,.1f}",
        "FCE año 1 (MXN)": f"{r['cf'][1]:,.0f}",
        "VAN (MXN)": f"{r['VAN']:,.0f}",
        "TIR": "n/d" if pd.isna(r["TIR"]) else f"{r['TIR']:.1%}",
        "Payback (años)": "No recupera" if pd.isna(r["Payback"]) else f"{r['Payback']:.2f}",
    } for n, r in res.items()
})
st.dataframe(comp)

c1, c2, c3 = st.columns(3)
c1.metric("Valor esperado del VAN", f"${ev:,.0f}")
c2.metric("Probabilidad de VAN < 0", f"{sum(esc[n]['prob'] for n in res if res[n]['VAN'] < 0):.0%}")
c3.metric("Decisión sugerida", "Invertir" if ev > 0 and res["Pesimista"]["VAN"] >= 0
          else ("Invertir condicionado" if ev > 0 else "No invertir"))

# ---------------- Gráficas ----------------
g1, g2 = st.columns(2)
with g1:
    st.markdown("**VAN por escenario (MXN)**")
    st.bar_chart(pd.Series({n: r["VAN"] for n, r in res.items()}))
with g2:
    st.markdown("**Flujo acumulado (MXN)**")
    acum = pd.DataFrame({n: pd.Series(r["cf"]).cumsum() for n, r in res.items()})
    acum.index.name = "Año"
    st.line_chart(acum)

# ---------------- Flujos por escenario ----------------
st.subheader("Flujos de efectivo por escenario")
for n, r in res.items():
    with st.expander(f"{n} — VAN ${r['VAN']:,.0f}", expanded=(n == "Realista")):
        st.dataframe(r["df"].set_index("Año").style.format("{:,.0f}"))

# ---------------- Sensibilidad ----------------
st.subheader("Demanda mínima para VAN = 0 (escenario realista)")
base = esc["Realista"]
lo, hi = 1_000.0, 200_000.0
for _ in range(60):
    mid = (lo + hi) / 2
    v = m.evaluar({**base, "demanda": mid}, tmar, inversion)["VAN"]
    lo, hi = (mid, hi) if v < 0 else (lo, mid)
st.info(f"Con precio, costo y tipo de cambio realistas, el proyecto necesita ≈ **{hi:,.0f} kg** en el año 1 para VAN = 0.")
