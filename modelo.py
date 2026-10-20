"""Modelo financiero de CaféAndes (organización simulada).
Calcula flujos de efectivo, VAN, TIR y Payback por escenario."""
import numpy as np
import pandas as pd

# ---- Parámetros fijos del proyecto (MXN) ----
INVERSION = 6_000_000      # tostadora industrial + empaque + capital de trabajo inicial
HORIZONTE = 5              # años
COSTO_FIJO = 3_000_000     # nómina fija, renta, servicios, marketing (por año)
OTROS_VAR = 45.0           # empaque, merma, logística y comisiones por kg
TASA_ISR = 0.30
TMAR = 0.12                # tasa de descuento
DEPRECIACION = INVERSION / HORIZONTE

# ---- Variables clave por escenario ----
ESCENARIOS = {
    "Pesimista": dict(demanda=38_000, crecimiento=0.00, precio=245.0, costo_usd=4.9, tc=20.5, prob=0.30),
    "Realista":  dict(demanda=45_000, crecimiento=0.05, precio=260.0, costo_usd=4.5, tc=18.5, prob=0.50),
    "Optimista": dict(demanda=52_000, crecimiento=0.07, precio=275.0, costo_usd=4.2, tc=18.0, prob=0.20),
}

def flujos(demanda, crecimiento, precio, costo_usd, tc, inversion=INVERSION,
           costo_fijo=COSTO_FIJO, tasa_isr=TASA_ISR, horizonte=HORIZONTE, **_):
    costo_unit = costo_usd * tc + OTROS_VAR
    dep = inversion / horizonte
    filas = []
    for t in range(1, horizonte + 1):
        kg = demanda * (1 + crecimiento) ** (t - 1)
        ingresos = kg * precio
        costos_var = kg * costo_unit
        ebitda = ingresos - costos_var - costo_fijo
        ebit = ebitda - dep
        isr = max(ebit, 0) * tasa_isr
        fce = ebit - isr + dep
        filas.append(dict(Año=t, Kg=kg, Ingresos=ingresos, Costos_variables=costos_var,
                          Costos_fijos=costo_fijo, EBITDA=ebitda, Depreciación=dep,
                          ISR=isr, FCE=fce))
    df = pd.DataFrame(filas)
    return df, costo_unit

def van(tasa, cf):
    return sum(c / (1 + tasa) ** t for t, c in enumerate(cf))

def tir(cf):
    lo, hi = -0.99, 10.0
    if van(lo, cf) * van(hi, cf) > 0:
        return float("nan")
    for _ in range(200):
        mid = (lo + hi) / 2
        if van(lo, cf) * van(mid, cf) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2

def payback(cf):
    acum = 0.0
    for t, c in enumerate(cf):
        previo = acum
        acum += c
        if t > 0 and acum >= 0 and c > 0:
            return (t - 1) + (-previo) / c
    return float("nan")

def evaluar(params, tmar=TMAR, inversion=INVERSION):
    df, cu = flujos(**{**params, "inversion": inversion})
    cf = [-inversion] + df["FCE"].tolist()
    return dict(df=df, cf=cf, costo_unit=cu, VAN=van(tmar, cf), TIR=tir(cf), Payback=payback(cf))

def comparativa(esc=ESCENARIOS, tmar=TMAR, inversion=INVERSION):
    res = {n: evaluar(p, tmar, inversion) for n, p in esc.items()}
    ev = sum(esc[n]["prob"] * res[n]["VAN"] for n in esc)
    return res, ev

if __name__ == "__main__":
    res, ev = comparativa()
    for n, r in res.items():
        print(n, round(r["VAN"]), round(r["TIR"]*100, 1), round(r["Payback"], 2), round(r["costo_unit"], 1))
        print(r["df"][["Año","Kg","EBITDA","FCE"]].round(0).to_string(index=False))
    print("E[VAN]", round(ev))
