import streamlit as st
import pandas as pd
import numpy as np

# Configuración básica de página
st.set_page_config(
    page_title="Centro de Mando Progol v4.0 Ultra",
    page_icon="⚽",
    layout="wide"
)

# Inyección de estilos CSS para visualización e impresión limpia
st.markdown("""
<style>
@media print {
    /* Ocultar barra lateral, botones y elementos no imprimibles */
    header, footer, .stButton, [data-testid="stSidebar"], [data-testid="stHeader"] {
        display: none !important;
    }
    .print-ticket {
        display: block !important;
        width: 100% !important;
        font-family: Arial, sans-serif !important;
        color: #000 !important;
    }
    .print-ticket table {
        width: 100%;
        border-collapse: collapse;
    }
    .print-ticket th, .print-ticket td {
        border: 1px solid #333 !important;
        padding: 6px !important;
        text-align: center;
    }
}
.ticket-card {
    background-color: #1e293b;
    border-radius: 10px;
    padding: 20px;
    border: 1px solid #334155;
    margin-bottom: 20px;
}
.badge-sharp {
    background-color: #059669;
    color: white;
    padding: 3px 8px;
    border-radius: 4px;
    font-weight: bold;
    font-size: 0.85em;
}
.badge-trap {
    background-color: #dc2626;
    color: white;
    padding: 3px 8px;
    border-radius: 4px;
    font-weight: bold;
    font-size: 0.85em;
}
</style>
""", unsafe_allow_html=True)

st.title("⚽ Centro de Mando Progol v4.0 Ultra")
st.caption("Sistema Cuantitativo • Análisis de Smart Money • Filtro de Sedes H2H • Exportación a Boleto")

# -------------------------------------------------------------
# ESTRUCTURA DE DATOS (MUESTRA DE TRABAJO)
# -------------------------------------------------------------
if "datos_progol" not in st.session_state:
    st.session_state["datos_progol"] = [
        {"#": 1, "Liga": "Liga MX", "Local": "Santos Laguna", "Visita": "Guadalajara Chivas", "O_L": 2.80, "O_E": 3.20, "O_V": 2.45, "C_L": 3.10, "C_E": 3.30, "C_V": 2.20, "H2H_L_wins": 3, "H2H_E_wins": 2, "H2H_V_wins": 1},
        {"#": 2, "Liga": "Liga MX", "Local": "Tigres UANL", "Visita": "América", "O_L": 2.30, "O_E": 3.30, "O_V": 3.00, "C_L": 2.15, "C_E": 3.40, "C_V": 3.25, "H2H_L_wins": 4, "H2H_E_wins": 2, "H2H_V_wins": 0},
        {"#": 3, "Liga": "Premier League", "Local": "Arsenal", "Visita": "Chelsea", "O_L": 1.95, "O_E": 3.50, "O_V": 3.80, "C_L": 1.90, "C_E": 3.60, "C_V": 4.00, "H2H_L_wins": 3, "H2H_E_wins": 1, "H2H_V_wins": 2},
        {"#": 4, "Liga": "La Liga", "Local": "Real Sociedad", "Visita": "Athletic Bilbao", "O_L": 2.50, "O_E": 3.00, "O_V": 2.90, "C_L": 2.40, "C_E": 3.10, "C_V": 3.10, "H2H_L_wins": 2, "H2H_E_wins": 3, "H2H_V_wins": 1},
        {"#": 5, "Liga": "Serie A", "Local": "AS Roma", "Visita": "Lazio", "O_L": 2.40, "O_E": 3.10, "O_V": 3.00, "C_L": 2.45, "C_E": 3.00, "C_V": 3.05, "H2H_L_wins": 2, "H2H_E_wins": 2, "H2H_V_wins": 2},
        {"#": 6, "Liga": "Bundesliga", "Local": "Eintracht Frankfurt", "Visita": "Leverkusen", "O_L": 3.40, "O_E": 3.60, "O_V": 2.05, "C_L": 3.60, "C_E": 3.70, "C_V": 1.95, "H2H_L_wins": 2, "H2H_E_wins": 0, "H2H_V_wins": 4},
        {"#": 7, "Liga": "Liga MX", "Local": "Monterrey", "Visita": "Toluca", "O_L": 2.05, "O_E": 3.40, "O_V": 3.50, "C_L": 1.95, "C_E": 3.50, "C_V": 3.80, "H2H_L_wins": 4, "H2H_E_wins": 1, "H2H_V_wins": 1},
        {"#": 8, "Liga": "MLS", "Local": "LAFC", "Visita": "Seattle Sounders", "O_L": 1.85, "O_E": 3.60, "O_V": 4.10, "C_L": 1.80, "C_E": 3.70, "C_V": 4.30, "H2H_L_wins": 3, "H2H_E_wins": 2, "H2H_V_wins": 1},
        {"#": 9, "Liga": "Eredivisie", "Local": "AZ Alkmaar", "Visita": "Feyenoord", "O_L": 3.00, "O_E": 3.40, "O_V": 2.25, "C_L": 3.10, "C_E": 3.40, "C_V": 2.20, "H2H_L_wins": 1, "H2H_E_wins": 2, "H2H_V_wins": 3},
        {"#": 10, "Liga": "Primeira Liga", "Local": "Braga", "Visita": "Porto", "O_L": 3.20, "O_E": 3.30, "O_V": 2.20, "C_L": 3.30, "C_E": 3.30, "C_V": 2.15, "H2H_L_wins": 1, "H2H_E_wins": 1, "H2H_V_wins": 4},
        {"#": 11, "Liga": "Liga MX", "Local": "Pumas UNAM", "Visita": "Cruz Azul", "O_L": 2.70, "O_E": 3.20, "O_V": 2.60, "C_L": 2.80, "C_E": 3.20, "C_V": 2.50, "H2H_L_wins": 2, "H2H_E_wins": 2, "H2H_V_wins": 2},
        {"#": 12, "Liga": "Brasileirao", "Local": "Palmeiras", "Visita": "Flamengo", "O_L": 2.35, "O_E": 3.10, "O_V": 3.10, "C_L": 2.30, "C_E": 3.15, "C_V": 3.20, "H2H_L_wins": 2, "H2H_E_wins": 3, "H2H_V_wins": 1},
        {"#": 13, "Liga": "Liga BetPlay", "Local": "Millonarios", "Visita": "Atlético Nacional", "O_L": 2.20, "O_E": 3.00, "O_V": 3.40, "C_L": 2.10, "C_E": 3.10, "C_V": 3.60, "H2H_L_wins": 3, "H2H_E_wins": 2, "H2H_V_wins": 1},
        {"#": 14, "Liga": "Liga MX", "Local": "Atlas", "Visita": "Pachuca", "O_L": 2.60, "O_E": 3.20, "O_V": 2.70, "C_L": 2.50, "C_E": 3.25, "C_V": 2.80, "H2H_L_wins": 2, "H2H_E_wins": 1, "H2H_V_wins": 3},
    ]

# Muestra de historial frente a frente para el filtro
H2H_SAMPLE_DATA = [
    {"Fecha": "2024-02-10", "Torneo": "Liga MX", "Local": "Santos Laguna", "Goles_L": 1, "Goles_V": 0, "Visita": "Guadalajara Chivas"},
    {"Fecha": "2023-08-26", "Torneo": "Liga MX", "Local": "Santos Laguna", "Goles_L": 2, "Goles_V": 1, "Visita": "Guadalajara Chivas"},
    {"Fecha": "2023-03-04", "Torneo": "Liga MX", "Local": "Guadalajara Chivas", "Goles_L": 2, "Goles_V": 0, "Visita": "Santos Laguna"},
    {"Fecha": "2022-07-16", "Torneo": "Liga MX", "Local": "Santos Laguna", "Goles_L": 1, "Goles_V": 1, "Visita": "Guadalajara Chivas"},
    {"Fecha": "2022-03-05", "Torneo": "Liga MX", "Local": "Guadalajara Chivas", "Goles_L": 1, "Goles_V": 0, "Visita": "Santos Laguna"},
    {"Fecha": "2021-08-15", "Torneo": "Liga MX", "Local": "Santos Laguna", "Goles_L": 0, "Goles_V": 0, "Visita": "Guadalajara Chivas"},
]

# -------------------------------------------------------------
# MENÚ DE PESTAÑAS
# -------------------------------------------------------------
tabs = st.tabs([
    "📊 1. ANÁLISIS & SMART MONEY",
    "🔎 2. HISTORIAL H2H CON FILTRO",
    "🎟️ 3. QUINIELA 7/8 DOBLES (IMPRIMIR)",
    "📝 4. CAPTURA Y RE-CAPTURA"
])

# -------------------------------------------------------------
# PESTAÑA 1: ANÁLISIS CUANTITATIVO Y MOVIMIENTO DE LÍNEAS
# -------------------------------------------------------------
with tabs[0]:
    st.header("📈 Análisis Cuantitativo y Detección de Smart Money")
    st.caption("Compara los momios de apertura (Lunes) vs cierre (Viernes) para identificar hacia dónde se movió el dinero profesional.")
    
    filas_analisis = []
    for p in st.session_state["datos_progol"]:
        inv_o_l, inv_o_e, inv_o_v = 1/p["O_L"], 1/p["O_E"], 1/p["O_V"]
        sum_o = inv_o_l + inv_o_e + inv_o_v
        p_o_l, p_o_e, p_o_v = (inv_o_l/sum_o)*100, (inv_o_e/sum_o)*100, (inv_o_v/sum_o)*100
        
        inv_c_l, inv_c_e, inv_c_v = 1/p["C_L"], 1/p["C_E"], 1/p["C_V"]
        sum_c = inv_c_l + inv_c_e + inv_c_v
        p_c_l, p_c_e, p_c_v = (inv_c_l/sum_c)*100, (inv_c_e/sum_c)*100, (inv_c_v/sum_c)*100
        
        diff_l = p_c_l - p_o_l
        diff_e = p_c_e - p_o_e
        diff_v = p_c_v - p_o_v
        
        movimiento = "Estable / Normal"
        if diff_l >= 3.5:
            movimiento = "🔥 DINERO FUERTE AL LOCAL"
        elif diff_v >= 3.5:
            movimiento = "🔥 DINERO FUERTE A LA VISITA"
        elif diff_e >= 3.0:
            movimiento = "🟡 DINERO ENTRANDO AL EMPATE"
            
        filas_analisis.append({
            "#": p["#"],
            "Partido": f"{p['Local']} vs {p['Visita']}",
            "P. Local (Vie)": f"{p_c_l:.1f}%",
            "P. Empate (Vie)": f"{p_c_e:.1f}%",
            "P. Visita (Vie)": f"{p_c_v:.1f}%",
            "Δ Local": f"{diff_l:+.1f}%",
            "Δ Visita": f"{diff_v:+.1f}%",
            "Diagnóstico de Mercado": movimiento
        })
        
    df_analisis = pd.DataFrame(filas_analisis)
    st.dataframe(df_analisis, use_container_width=True, hide_index=True)

# -------------------------------------------------------------
# PESTAÑA 2: HISTORIAL FRENTE A FRENTE CON FILTRO DE CANCHA
# -------------------------------------------------------------
with tabs[1]:
    st.header("🔎 Historial Frente a Frente (H2H)")
    
    partido_sel = st.selectbox(
        "Selecciona el partido para ver su historial directo:",
        [f"#{p['#']} {p['Local']} vs {p['Visita']}" for p in st.session_state["datos_progol"]]
    )
    
    p_num = int(partido_sel.split()[0].replace("#", ""))
    p_info = next(item for item in st.session_state["datos_progol"] if item["#"] == p_num)
    local_actual, visita_actual = p_info["Local"], p_info["Visita"]
    
    filtro_sede = st.radio(
        "Filtrar enfrentamientos por condición de sede:",
        ["🌐 Todos los enfrentamientos directos (Cualquier cancha)", f"🏟️ Solo en el estadio de {local_actual} ({local_actual} como Local)"],
        horizontal=True
    )
    
    df_h2h = pd.DataFrame(H2H_SAMPLE_DATA)
    
    if "Solo en el estadio" in filtro_sede:
        df_filtrado = df_h2h[df_h2h["Local"] == local_actual]
        st.info(f"Mostrando únicamente los juegos donde **{local_actual}** recibió a **{visita_actual}** en casa.")
    else:
        df_filtrado = df_h2h
        st.info("Mostrando todos los juegos históricos globales.")
        
    st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

# -------------------------------------------------------------
# PESTAÑA 3: QUINIELA 7/8 DOBLES CON OPCIÓN DE IMPRESIÓN
# -------------------------------------------------------------
with tabs[2]:
    st.header("🎟️ Sugerencia Óptima de Quiniela Múltiple")
    
    modo_dobles = st.segmented_control("Selecciona la estructura de cobertura:", ["7 Dobles (128 Quinielas)", "8 Dobles (256 Quinielas)"], default="7 Dobles (128 Quinielas)")
    num_dobles = 7 if "7" in modo_dobles else 8
    
    boletos_sugeridos = []
    for i, p in enumerate(st.session_state["datos_progol"]):
        if i < num_dobles:
            signo = "L - E" if p["C_L"] <= p["C_V"] else "E - V"
            tipo = "DOBLE"
        else:
            signo = "L" if p["C_L"] < p["C_V"] else "V"
            tipo = "FIJO"
            
        boletos_sugeridos.append({
            "#": p["#"],
            "Partido": f"{p['Local']} vs {p['Visita']}",
            "Pronóstico": signo,
            "Tipo": tipo
        })
        
    df_boleto = pd.DataFrame(boletos_sugeridos)
    
    col_izq, col_der = st.columns([2, 1])
    with col_izq:
        st.dataframe(df_boleto, use_container_width=True, hide_index=True)
        
    with col_der:
        st.markdown(f"""
        <div class="ticket-card">
            <h3>📋 Resumen Operativo</h3>
            <p><strong>Estructura:</strong> {num_dobles} Dobles y {14 - num_dobles} Fijos</p>
            <p><strong>Combinaciones:</strong> {2**num_dobles} quinielas</p>
            <p><strong>Inversión estimada:</strong> ${2**num_dobles * 15:,.2f} MXN</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.button("🖨️ Imprimir / Guardar en PDF", on_click=None, help="Abre el cuadro de diálogo de impresión de tu navegador")
        st.caption("💡 *Tip: Puedes presionar **Ctrl + P** en cualquier momento para imprimir el formato limpio.*")

    st.subheader("📲 Formato de Texto para WhatsApp / Bloc de Notas")
    texto_whatsapp = f"*QUINIELA PROGOL ({num_dobles} DOBLES)*\n"
    for b in boletos_sugeridos:
        texto_whatsapp += f"{b['#']}. {b['Partido']} -> [{b['Pronóstico']}]\n"
    texto_whatsapp += f"\nTotal combinaciones: {2**num_dobles} | Costo: ${2**num_dobles * 15:,} MXN"
    
    st.code(texto_whatsapp, language="text")

# -------------------------------------------------------------
# PESTAÑA 4: CAPTURA DE MOMIOS (LUNES VS VIERNES)
# -------------------------------------------------------------
with tabs[3]:
    st.header("📝 Captura de Momios (Apertura vs Cierre)")
    st.markdown("Actualiza aquí los valores para recalcular el Smart Money y las probabilidades en tiempo real.")
    
    with st.expander("✏️ Editar Momios del Juego #1 (Santos vs Chivas)", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("**Momios de Apertura (Lunes)**")
            n_ol = st.number_input("Apertura Local", value=2.80, step=0.05)
            n_oe = st.number_input("Apertura Empate", value=3.20, step=0.05)
            n_ov = st.number_input("Apertura Visita", value=2.45, step=0.05)
        with c2:
            st.markdown("**Momios de Cierre (Viernes)**")
            n_cl = st.number_input("Cierre Local", value=3.10, step=0.05)
            n_ce = st.number_input("Cierre Empate", value=3.30, step=0.05)
            n_cv = st.number_input("Cierre Visita", value=2.20, step=0.05)
        with c3:
            st.markdown("**Acciones**")
            if st.button("💾 Guardar y Actualizar"):
                st.session_state["datos_progol"][0]["O_L"] = n_ol
                st.session_state["datos_progol"][0]["O_E"] = n_oe
                st.session_state["datos_progol"][0]["O_V"] = n_ov
                st.session_state["datos_progol"][0]["C_L"] = n_cl
                st.session_state["datos_progol"][0]["C_E"] = n_ce
                st.session_state["datos_progol"][0]["C_V"] = n_cv
                st.success("Momios del partido #1 actualizados correctamente.")
                st.rerun()
