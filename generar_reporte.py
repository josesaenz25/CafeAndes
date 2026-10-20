import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer,
                                PageBreak, Table, TableStyle, Image, NextPageTemplate)
import modelo as m

res, ev = m.comparativa()
E = m.ESCENARIOS
COL = {"Pesimista": "#B5483A", "Realista": "#4A6FA5", "Optimista": "#3E8E5B"}
MARRON = colors.HexColor("#4B2E1E")

# ---- sensibilidades para el texto ----
def be_demanda(base):
    lo, hi = 1000.0, 200000.0
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if m.evaluar({**base, "demanda": mid})["VAN"] < 0 else (lo, mid)
    return hi
be = be_demanda(E["Realista"])
van_fx = m.evaluar({**E["Realista"], "tc": 20.5})["VAN"]
van_fx_cond = m.evaluar({**E["Realista"], "tc": 20.5, "demanda": 40000})["VAN"]
van_pes_cond = m.evaluar({**E["Pesimista"], "demanda": 42000, "tc": 19.0, "costo_usd": 4.6})["VAN"]
p_neg = sum(E[n]["prob"] for n in res if res[n]["VAN"] < 0)
sd = (sum(E[n]["prob"] * (res[n]["VAN"] - ev) ** 2 for n in res)) ** 0.5

def f(x): return f"-${abs(x):,.0f}" if x < 0 else f"${x:,.0f}"
def pct(x): return "n/d" if x != x else f"{x:.1%}"
def pb(x): return "No recupera" if x != x else f"{x:.2f} años"

# ---- gráficas ----
fig, ax = plt.subplots(1, 2, figsize=(9, 3.2))
names = list(res)
vals = [res[n]["VAN"] / 1e6 for n in names]
b = ax[0].bar(names, vals, color=[COL[n] for n in names])
ax[0].axhline(0, color="black", lw=0.8)
ax[0].axhline(ev / 1e6, color="#4B2E1E", ls="--", lw=1.2, label=f"E[VAN] = {ev/1e6:.2f} M")
ax[0].set_title("VAN por escenario (millones de MXN)", fontsize=10)
ax[0].legend(fontsize=8)
for r, v in zip(b, vals):
    ax[0].text(r.get_x() + r.get_width() / 2, v + (0.3 if v >= 0 else -0.9), f"{v:.2f}", ha="center", fontsize=8)
for n in names:
    import numpy as np
    ax[1].plot(range(0, 6), np.cumsum(res[n]["cf"]) / 1e6, marker="o", color=COL[n], label=n)
ax[1].axhline(0, color="black", lw=0.8)
ax[1].set_title("Flujo de efectivo acumulado (millones de MXN)", fontsize=10)
ax[1].set_xlabel("Año", fontsize=8); ax[1].legend(fontsize=8)
for a in ax:
    a.spines[["top", "right"]].set_visible(False); a.tick_params(labelsize=8)
plt.tight_layout(); plt.savefig("graficas.png", dpi=200); plt.close()

# ---- estilos ----
ss = getSampleStyleSheet()
body = ParagraphStyle("body", parent=ss["Normal"], fontName="Helvetica", fontSize=10.5, leading=15, alignment=TA_JUSTIFY, spaceAfter=7)
h1 = ParagraphStyle("h1", parent=ss["Heading1"], fontName="Helvetica-Bold", fontSize=15, textColor=MARRON, spaceBefore=4, spaceAfter=8)
h2 = ParagraphStyle("h2", parent=ss["Heading2"], fontName="Helvetica-Bold", fontSize=11.5, textColor=MARRON, spaceBefore=6, spaceAfter=4)
small = ParagraphStyle("small", parent=body, fontSize=8.5, leading=11, alignment=0, textColor=colors.HexColor("#555555"))
cell = ParagraphStyle("cell", parent=body, fontSize=8.8, leading=11, alignment=0, spaceAfter=0)
cellb = ParagraphStyle("cellb", parent=cell, fontName="Helvetica-Bold")

def tabla(data, widths, header=True, zebra=True):
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    st = [("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#BBBBBB")),
          ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
          ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]
    if header:
        st += [("BACKGROUND", (0, 0), (-1, 0), MARRON), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white)]
    if zebra:
        for i in range(1, len(data)):
            if i % 2 == 0: st.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#F5EFE8")))
    t.setStyle(TableStyle(st)); return t

def hdr(txt): return Paragraph(f'<font color="white"><b>{txt}</b></font>', cell)

# ---- portada y encabezado ----
def portada(c, d):
    w, h = letter
    c.setFillColor(MARRON); c.rect(0, 0, w, h, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#C99A6B")); c.rect(2 * cm, h - 9.2 * cm, 3 * cm, 0.25 * cm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 28)
    c.drawString(2 * cm, h - 11 * cm, "Planeación por escenarios")
    c.drawString(2 * cm, h - 12.3 * cm, "para una decisión de inversión")
    c.setFont("Helvetica", 14)
    c.drawString(2 * cm, h - 14 * cm, "Caso CaféAndes S.A. de C.V. — Metodología de Peter Schwartz")
    c.drawString(2 * cm, h - 14.8 * cm, "VAN, TIR y Payback con Python y Streamlit")
    c.setFont("Helvetica-Bold", 12); y = 8.2 * cm
    for lbl, val in [("Alumno", "Granados Saenz José de Jesús"), ("Carrera", "LCDN"),
                     ("Materia", "Analítica para negocios"), ("Fecha", "19 de octubre de 2026")]:
        c.setFillColor(colors.HexColor("#C99A6B")); c.setFont("Helvetica-Bold", 11); c.drawString(2 * cm, y, lbl.upper())
        c.setFillColor(colors.white); c.setFont("Helvetica", 13); c.drawString(5 * cm, y, val); y -= 0.9 * cm

def pie(c, d):
    c.setFont("Helvetica", 8); c.setFillColor(colors.grey)
    c.drawString(2.2 * cm, 1.3 * cm, "Granados Saenz José de Jesús · LCDN · Analítica para negocios")
    c.drawRightString(letter[0] - 2.2 * cm, 1.3 * cm, f"{d.page - 1}")

doc = BaseDocTemplate("Reporte_Escenarios_Schwartz_CafeAndes.pdf", pagesize=letter,
                      leftMargin=2.2 * cm, rightMargin=2.2 * cm, topMargin=2.2 * cm, bottomMargin=2.2 * cm,
                      title="Planeación por escenarios — CaféAndes", author="Granados Saenz José de Jesús")
fr = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")
doc.addPageTemplates([PageTemplate("portada", [fr], onPage=portada), PageTemplate("normal", [fr], onPage=pie)])

S = [NextPageTemplate("normal"), PageBreak()]

# ============ 1. Organización y objetivo ============
S += [Paragraph("1. Descripción de la organización y objetivo económico", h1),
 Paragraph("<b>CaféAndes S.A. de C.V.</b> es una empresa <i>simulada</i> con sede en la Ciudad de México que tuesta y vende café de especialidad. "
  "Atiende a cafeterías independientes, oficinas y una tienda en línea, con ventas actuales cercanas a 45 mil kg de café tostado al año. "
  "Hoy terceriza buena parte del tostado, lo que limita su margen y su control de calidad. La dirección evalúa comprar una <b>línea de tostado industrial</b> "
  f"con una inversión inicial de <b>{f(m.INVERSION)} MXN</b> (equipo, empaque y capital de trabajo) y un horizonte de evaluación de {m.HORIZONTE} años.", body),
 Paragraph("<b>Objetivo económico.</b> Obtener un <b>VAN mayor a MXN 3 millones</b> con una tasa de descuento (TMAR) de "
  f"{m.TMAR:.0%}, una <b>TIR superior a 25%</b> y recuperar la inversión en <b>menos de 3 años</b>. La pregunta central es si conviene invertir "
  "dado que cuatro variables externas son inciertas.", body),
 Paragraph("Supuestos comunes a todos los escenarios", h2),
 Paragraph(f"Costos fijos anuales de {f(m.COSTO_FIJO)} (nómina, renta, servicios y marketing); otros costos variables de ${m.OTROS_VAR:.0f}/kg (empaque, merma y logística); "
  f"depreciación en línea recta a {m.HORIZONTE} años sin valor de rescate; ISR de {m.TASA_ISR:.0%}; flujos de fin de año. "
  "El flujo de efectivo libre se calcula como utilidad operativa menos ISR más depreciación.", body),
 Paragraph("Metodología de Peter Schwartz", h2),
 Paragraph("En <i>El arte de la visión a largo plazo</i>, Schwartz propone construir escenarios como <b>historias plausibles</b> del futuro, no como pronósticos. "
  "El proceso aplicado aquí fue: (1) definir la decisión focal (invertir o no en la línea de tostado); (2) identificar las fuerzas que la afectan; "
  "(3) ordenarlas por impacto e incertidumbre y quedarse con las cuatro principales; (4) construir tres mundos coherentes, donde las variables se mueven en conjunto; "
  "(5) cuantificarlos en el modelo financiero; y (6) definir señales de alerta que indiquen hacia qué escenario se avanza. "
  "El propósito es tomar una decisión que resista varios futuros, no adivinar el correcto.", body),
 PageBreak()]

# ============ 2. Variables clave ============
S += [Paragraph("2. Variables clave y sus rangos", h1),
 Paragraph("Se eligieron cuatro variables con alto impacto en el VAN y alta incertidumbre. El tipo de cambio y el precio del café verde "
  "actúan juntos sobre el costo unitario, porque el grano se compra en dólares.", body)]
vd = [[hdr("Variable"), hdr("Pesimista"), hdr("Realista"), hdr("Optimista"), hdr("Por qué importa")]]
vd += [
 [Paragraph("<b>1. Demanda</b> año 1 (kg) y crecimiento anual", cell)] + [Paragraph(f"{E[n]['demanda']:,} kg; {E[n]['crecimiento']:.0%}", cell) for n in res] + [Paragraph("Define el volumen que absorbe los costos fijos.", cell)],
 [Paragraph("<b>2. Precio</b> promedio (MXN/kg)", cell)] + [Paragraph(f"${E[n]['precio']:.0f}", cell) for n in res] + [Paragraph("Depende de la competencia y del poder de marca.", cell)],
 [Paragraph("<b>3. Costo del café verde</b> (USD/kg)", cell)] + [Paragraph(f"${E[n]['costo_usd']:.1f}", cell) for n in res] + [Paragraph("Precio internacional, clima y cosechas.", cell)],
 [Paragraph("<b>4. Tipo de cambio</b> (MXN/USD)", cell)] + [Paragraph(f"${E[n]['tc']:.1f}", cell) for n in res] + [Paragraph("Encarece o abarata el insumo importado.", cell)],
 [Paragraph("<b>Costo variable unitario resultante</b> (MXN/kg)", cellb)] + [Paragraph(f"<b>${res[n]['costo_unit']:.1f}</b>", cell) for n in res] + [Paragraph("USD/kg × tipo de cambio + $45 de otros costos.", cell)],
 [Paragraph("<b>Margen de contribución</b> (MXN/kg)", cellb)] + [Paragraph(f"<b>${E[n]['precio'] - res[n]['costo_unit']:.1f}</b>", cell) for n in res] + [Paragraph("Precio menos costo variable unitario.", cell)],
]
S += [Spacer(1, 4), tabla(vd, [3.9*cm, 2.5*cm, 2.5*cm, 2.5*cm, 4.9*cm]), Spacer(1, 4),
 Paragraph("Los rangos son supuestos del ejercicio, razonados a partir del comportamiento histórico reciente del peso, del grano arábica y de los precios de café de especialidad en México.", small),
 Paragraph("Probabilidades asignadas", h2),
 Paragraph(f"Se asignó una probabilidad de <b>{E['Pesimista']['prob']:.0%}</b> al escenario pesimista, <b>{E['Realista']['prob']:.0%}</b> al realista y "
  f"<b>{E['Optimista']['prob']:.0%}</b> al optimista. La mayor probabilidad pesimista que optimista refleja que los tres riesgos externos (tipo de cambio, café verde y competencia) "
  "pueden coincidir, mientras que un mundo con todas las variables favorables es menos frecuente. Estas probabilidades son juicios de la dirección y pueden modificarse en la app de Streamlit.", body),
 Paragraph("Herramienta tecnológica", h2),
 Paragraph("El modelo se programó en Python (<font face='Courier'>modelo.py</font>) y se explora con una app de Streamlit (<font face='Courier'>app.py</font>). "
  "La app permite cambiar cada variable, las probabilidades, la inversión y la TMAR; recalcula los flujos de efectivo, el VAN, la TIR y el Payback de cada escenario, "
  "muestra la tabla comparativa y calcula el valor esperado del VAN. Todas las cifras de este reporte provienen de ese modelo.", body),
 PageBreak()]

# ============ 3. Escenarios como historias ============
r = res
S += [Paragraph("3. Los tres escenarios como historias", h1),
 Paragraph("Escenario pesimista: «La tormenta perfecta»", h2),
 Paragraph(f"En 2027 el peso se deprecia hasta ${E['Pesimista']['tc']:.1f} por dólar y una mala cosecha en Brasil y Colombia lleva el café verde a USD {E['Pesimista']['costo_usd']:.1f}/kg. "
  f"El costo unitario sube a ${r['Pesimista']['costo_unit']:.0f}/kg. Al mismo tiempo, dos cadenas grandes lanzan sus propias líneas de café de especialidad con precios agresivos; "
  f"CaféAndes debe bajar su precio a ${E['Pesimista']['precio']:.0f}/kg y apenas retiene {E['Pesimista']['demanda']:,} kg al año, sin crecimiento. "
  f"El margen se reduce a ${E['Pesimista']['precio'] - r['Pesimista']['costo_unit']:.0f}/kg y el flujo libre se queda en {f(r['Pesimista']['cf'][1])} anuales. "
  f"La línea de tostado se vuelve una carga: el VAN es de {f(r['Pesimista']['VAN'])} y la inversión no se recupera en el horizonte.", body),
 Paragraph("Escenario realista: «Crecimiento con disciplina»", h2),
 Paragraph(f"El tipo de cambio se mantiene alrededor de ${E['Realista']['tc']:.1f} y el café verde en USD {E['Realista']['costo_usd']:.1f}/kg, con un costo unitario de ${r['Realista']['costo_unit']:.0f}/kg. "
  f"CaféAndes conserva su base de {E['Realista']['demanda']:,} kg, sube su precio a ${E['Realista']['precio']:.0f}/kg gracias a la mejora de calidad por tostar en casa y crece {E['Realista']['crecimiento']:.0%} anual "
  f"con nuevas cafeterías y suscripciones. El margen es de ${E['Realista']['precio'] - r['Realista']['costo_unit']:.0f}/kg y el flujo libre pasa de {f(r['Realista']['cf'][1])} en el año 1 a {f(r['Realista']['cf'][5])} en el año 5. "
  f"El VAN es de {f(r['Realista']['VAN'])}, la TIR de {pct(r['Realista']['TIR'])} y el Payback de {pb(r['Realista']['Payback'])}: se cumple el objetivo.", body),
 Paragraph("Escenario optimista: «El café mexicano de moda»", h2),
 Paragraph(f"El peso se fortalece a ${E['Optimista']['tc']:.0f} por dólar y la cosecha es abundante, de modo que el café verde baja a USD {E['Optimista']['costo_usd']:.1f}/kg (costo unitario de ${r['Optimista']['costo_unit']:.0f}/kg). "
  f"El consumo de café de especialidad crece y la marca se posiciona entre oficinas y restaurantes; CaféAndes vende {E['Optimista']['demanda']:,} kg el primer año a ${E['Optimista']['precio']:.0f}/kg y crece {E['Optimista']['crecimiento']:.0%} anual. "
  f"El margen llega a ${E['Optimista']['precio'] - r['Optimista']['costo_unit']:.0f}/kg y el flujo libre supera {f(r['Optimista']['cf'][1])} desde el primer año. "
  f"El VAN es de {f(r['Optimista']['VAN'])}, la TIR de {pct(r['Optimista']['TIR'])} y el Payback de {pb(r['Optimista']['Payback'])}.", body),
 Paragraph("Señales de alerta (indicadores adelantados)", h2),
 Paragraph("Si el tipo de cambio supera $20 por dólar durante tres meses, si el café verde pasa de USD 4.8/kg en contratos futuros o si los clientes ancla se niegan a firmar contratos de volumen, "
  "el mundo avanza hacia el escenario pesimista. Lo contrario indica una trayectoria realista u optimista.", body),
 PageBreak()]

# ============ 4. Resultados ============
cd = [[hdr("Indicador"), hdr("Pesimista"), hdr("Realista"), hdr("Optimista")]]
cd += [
 ["Probabilidad"] + [f"{E[n]['prob']:.0%}" for n in res],
 ["Costo unitario (MXN/kg)"] + [f"${r[n]['costo_unit']:.1f}" for n in res],
 ["FCE año 1 (MXN)"] + [f(r[n]['cf'][1]) for n in res],
 ["FCE año 5 (MXN)"] + [f(r[n]['cf'][5]) for n in res],
 [Paragraph("<b>VAN al 12% (MXN)</b>", cell)] + [Paragraph(f"<b>{f(r[n]['VAN'])}</b>", cell) for n in res],
 ["TIR"] + [pct(r[n]['TIR']) for n in res],
 ["Payback"] + [pb(r[n]['Payback']) for n in res],
 ["¿Cumple el objetivo (VAN > $3 M, TIR > 25%, Payback < 3 años)?"] + ["No" if r[n]['VAN'] < 3e6 or not (r[n]['TIR'] > .25) or not (r[n]['Payback'] < 3) else "Sí" for n in res],
]
cd[-1][0] = Paragraph(cd[-1][0], cell)
S += [Paragraph("4. Tabla comparativa de resultados", h1),
 tabla(cd, [6.2*cm, 3.4*cm, 3.4*cm, 3.4*cm]), Spacer(1, 8),
 Image("graficas.png", width=16.5*cm, height=16.5*cm*3.2/9), Spacer(1, 6),
 Paragraph("Valor esperado del VAN", h2),
 Paragraph(f"E[VAN] = {E['Pesimista']['prob']:.2f} × ({f(r['Pesimista']['VAN'])}) + {E['Realista']['prob']:.2f} × ({f(r['Realista']['VAN'])}) + {E['Optimista']['prob']:.2f} × ({f(r['Optimista']['VAN'])}) = <b>{f(ev)} MXN</b>.", body),
 Paragraph(f"El valor esperado es positivo y cercano a la meta de $3 millones, pero la dispersión es alta (desviación estándar de {f(sd)}) y existe una probabilidad de {p_neg:.0%} de perder dinero. "
  f"Además, el escenario realista es la única historia que se acerca de forma estable al objetivo: en el pesimista se pierde más de la mitad de la inversión en términos de valor presente. "
  f"Con precio, costo y tipo de cambio realistas, el proyecto alcanza VAN = 0 con una demanda de apenas <b>{be:,.0f} kg</b> en el año 1, es decir, un margen de seguridad de {(1 - be/E['Realista']['demanda']):.0%} frente al volumen realista.", body),
 PageBreak()]

# ============ 5. Recomendación ============
S += [Paragraph("5. Recomendación de decisión", h1),
 Paragraph("<b>Recomendación: invertir de forma condicionada.</b>", ParagraphStyle("rec", parent=body, fontSize=12.5, textColor=colors.HexColor("#3E8E5B"), spaceAfter=8)),
 Paragraph(f"Se recomienda invertir porque el valor esperado del VAN ({f(ev)}) es positivo, la TIR realista ({pct(r['Realista']['TIR'])}) supera con amplitud la TMAR de {m.TMAR:.0%} "
  f"y el punto de equilibrio de demanda ({be:,.0f} kg) está muy por debajo del volumen actual. No se recomienda invertir sin condiciones, porque el escenario pesimista destruye valor "
  f"({f(r['Pesimista']['VAN'])}) y tiene {E['Pesimista']['prob']:.0%} de probabilidad; tampoco rechazar el proyecto, porque haría perder un VAN esperado atractivo.", body),
 Paragraph("Condiciones para ejecutar la inversión", h2),
 Paragraph(f"<b>1. Demanda asegurada.</b> Firmar contratos o cartas de intención con clientes ancla por al menos 40 mil kg anuales antes de comprar el equipo. "
  f"Con 40 mil kg y el tipo de cambio pesimista de $20.5, el VAN realista sigue en {f(van_fx_cond)}, frente a {f(van_fx)} con 45 mil kg.", body),
 Paragraph(f"<b>2. Cobertura cambiaria y de insumos.</b> Contratar coberturas o contratos de compra a plazo para al menos 50% del café verde, con un tipo de cambio máximo de $19. "
  f"Con 42 mil kg, tipo de cambio de $19 y café verde en USD 4.6/kg (un pesimista parcialmente cubierto), el VAN es de {f(van_pes_cond)}, por lo que la cobertura convierte pérdidas en un resultado cercano al equilibrio.", body),
 Paragraph("<b>3. Inversión escalonada.</b> Pagar el equipo en dos etapas, la segunda sujeta a que el volumen de los primeros 6 meses sea al menos 90% del plan. Esto reduce el monto en riesgo si aparecen las señales del escenario pesimista.", body),
 Paragraph("<b>4. Monitoreo trimestral.</b> Revisar el tipo de cambio, el precio del café verde, la competencia y el volumen de ventas. Si dos de las señales de alerta se activan, congelar la segunda etapa y renegociar precios.", body),
 Paragraph("Conclusión y limitaciones", h2),
 Paragraph("La planeación por escenarios muestra que la decisión no depende de adivinar el futuro, sino de elegir condiciones que mejoren el resultado en los futuros desfavorables. "
  "El análisis es un modelo simplificado: las variables se mueven en bloque dentro de cada escenario, las probabilidades son subjetivas, la empresa es simulada, "
  "no se modelan financiamiento externo, inflación ni valor de rescate, y el capital de trabajo se agrupó con la inversión inicial. "
  "Un siguiente paso sería una simulación Monte Carlo para ampliar la gama de combinaciones entre las variables.", body)]

doc.build(S)
print("ok")
