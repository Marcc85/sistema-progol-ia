import streamlit as st
import pandas as pd
import requests
import json
import os
import math
import io

st.set_page_config(
    page_title="Centro de Mando Progol v4.0 Ultra",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ------------------------------------------------------------------------------
# 0. ESTILOS VISUALES RESPONSIVOS Y FORMATO DE IMPRESIÓN LIMPIO
# ------------------------------------------------------------------------------
st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 2rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
        div.stButton > button {
            width: 100% !important;
            min-height: 48px !important;
            height: 48px !important;
            font-weight: 700 !important;
            font-size: 13px !important;
            border-radius: 8px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            text-align: center !important;
            white-space: normal !important;
            line-height: 1.15 !important;
            padding: 4px 6px !important;
            transition: all 0.2s ease-in-out;
        }
        div.stButton > button:hover {
            border-color: #ff4b4b !important;
            color: #ff4b4b !important;
        }
        [data-testid="stDataFrame"] {
            width: 100% !important;
            overflow-x: auto !important;
        }
        @media print {
            header, footer, [data-testid="stSidebar"], [data-testid="stHeader"], div.stButton, .no-print {
                display: none !important;
            }
            .block-container {
                padding: 0 !important;
                margin: 0 !important;
            }
        }
    </style>
    """,
    unsafe_allow_html=True
)

# ------------------------------------------------------------------------------
# 1. ARCHIVOS DE DISCO Y URL DE GOOGLE SHEETS OFICIAL
# ------------------------------------------------------------------------------
ARCHIVO_DISCO = "progol_captura_v7.json"
ARCHIVO_CACHE_API = "progol_bigdata_cache.json"
URL_GOOGLE_SHEET_DEFAULT = "https://docs.google.com/spreadsheets/d/1VnT4JtzK4LZZh8GDgM1NF8Oc59VWqJGe7S9eQi0FWcw/edit?gid=0#gid=0"

OPCIONES_LIGAS = [
    "Liga MX", "Liga MX Femenil", "MLS", "NWSL (USA Femenil)",
    "Liga Chilena (Primera División)", "Copa Chile", "Supercopa de Chile",
    "Amistoso / Club Friendlies", "Amistoso Internacional (Selecciones)",
    "Premier League", "FA Cup (Inglaterra)", "EFL Cup / Carabao Cup (Inglaterra)",
    "Championship (Inglaterra 2da)", "Community Shield (Inglaterra)",
    "La Liga (España)", "Copa del Rey (España)", "Liga F (España Femenil)",
    "Serie A (Italia)", "Coppa Italia", "Bundesliga (Alemania)", "DFB Pokal (Alemania)",
    "Ligue 1 (Francia)", "Coupe de France", "Liga Argentina", "Copa Argentina",
    "Primeira Liga (Portugal)", "Taça de Portugal", "Jupiler Pro League (Bélgica)",
    "Champions League", "Champions League Femenil", "Europa League", "Leagues Cup",
    "Concacaf Champions Cup", "Copa Libertadores", "Copa Sudamericana",
    "Brasileirão", "Copa do Brasil", "Eredivisie (Holanda)", "Otra / Automático"
]

TABLA_EN_BLANCO = [
    {
        "#": i + 1,
        "Liga": "Liga MX",
        "Local": "",
        "Visita": "",
        "Momio Local": "",
        "Momio Empate": "",
        "Momio Visitante": "",
        "Over 2.5": "",
        "Under 2.5": "",
        "Apertura Local": "",
        "Apertura Empate": "",
        "Apertura Visitante": ""
    }
    for i in range(14)
]

MAPA_LIGAS_ID = {
    "liga chilena (primera división)": 265, "chile": 265, "copa chile": 266,
    "amistoso / club friendlies": 667, "premier league": 39, "inglaterra": 39,
    "fa cup (inglaterra)": 45, "efl cup / carabao cup (inglaterra)": 48,
    "liga mx": 262, "mexico": 262, "liga mx femenil": 264, "mls": 253,
    "la liga (españa)": 140, "españa": 140, "copa del rey (españa)": 143,
    "serie a (italia)": 135, "italia": 135, "bundesliga (alemania)": 78,
    "ligue 1 (francia)": 61, "liga argentina": 128, "brasileirão": 71,
    "champions league": 2, "europa league": 3, "copa libertadores": 13
}

def cargar_disco():
    if os.path.exists(ARCHIVO_DISCO):
        try:
            with open(ARCHIVO_DISCO, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) == 14:
                    for item in data:
                        if "Liga" not in item: item["Liga"] = "Liga MX"
                        if "Over 2.5" not in item: item["Over 2.5"] = ""
                        if "Under 2.5" not in item: item["Under 2.5"] = ""
                        if "Apertura Local" not in item: item["Apertura Local"] = ""
                        if "Apertura Empate" not in item: item["Apertura Empate"] = ""
                        if "Apertura Visitante" not in item: item["Apertura Visitante"] = ""
                    return data
        except Exception:
            pass
    return TABLA_EN_BLANCO

def guardar_disco(datos):
    try:
        with open(ARCHIVO_DISCO, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def cargar_cache_api():
    if os.path.exists(ARCHIVO_CACHE_API):
        try:
            with open(ARCHIVO_CACHE_API, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def guardar_cache_api(cache_data):
    try:
        with open(ARCHIVO_CACHE_API, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

if "tabla_progol" not in st.session_state:
    st.session_state["tabla_progol"] = cargar_disco()

if "api_cache_xg" not in st.session_state:
    st.session_state["api_cache_xg"] = cargar_cache_api()

if "menu_activo" not in st.session_state:
    st.session_state["menu_activo"] = "📊 1. ANÁLISIS 1 (Excel)"

# ------------------------------------------------------------------------------
# 2. MOTOR API-SPORTS Y MATEMÁTICAS
# ------------------------------------------------------------------------------
class MotorAPISportsUltra:
    BASE_URL = "https://v3.football.api-sports.io"

    @classmethod
    def _get_headers(cls):
        api_key = st.secrets.get("api_sports", {}).get("api_key", "6974d8db01eb5eeb347c509793afe7cc")
        return {"x-apisports-key": api_key}

    @classmethod
    def buscar_equipo_dinamico(cls, nombre_equipo: str):
        if not nombre_equipo or not str(nombre_equipo).strip(): return None
        try:
            url = f"{cls.BASE_URL}/teams"
            res = requests.get(url, headers=cls._get_headers(), params={"search": str(nombre_equipo).strip()}, timeout=8)
            data = res.json().get("response", [])
            if data:
                t = data[0].get("team", {})
                return {"id": int(t.get("id")), "nombre": t.get("name"), "pais": t.get("country", "")}
        except Exception:
            pass
        return None

    @classmethod
    def obtener_h2h(cls, id1: int, id2: int):
        try:
            url = f"{cls.BASE_URL}/fixtures/headtohead"
            res = requests.get(url, headers=cls._get_headers(), params={"h2h": f"{id1}-{id2}", "last": 20}, timeout=8)
            data = res.json().get("response", [])
            partidos = []
            for item in data:
                fix = item.get("fixture", {})
                teams = item.get("teams", {})
                goals = item.get("goals", {})
                partidos.append({
                    "Fecha": fix.get("date", "")[:10],
                    "Torneo": item.get("league", {}).get("name", ""),
                    "Local": teams.get("home", {}).get("name", ""),
                    "home_id": int(teams.get("home", {}).get("id", 0)),
                    "Resultado": f"{goals.get('home', 0)} - {goals.get('away', 0)}",
                    "Visita": teams.get("away", {}).get("name", ""),
                    "away_id": int(teams.get("away", {}).get("id", 0))
                })
            return pd.DataFrame(partidos)
        except Exception:
            return pd.DataFrame()

def limpiar_momio(val):
    if val is None: return None
    v = str(val).replace("+", "").replace("$", "").replace(",", "").strip()
    if not v or v in ["0", "-"]: return None
    try: return float(v)
    except Exception: return None

def calcular_prob(m):
    if m is None or m == 0: return 0.0
    return (100.0 / (m + 100.0) * 100.0) if m > 0 else (abs(m) / (abs(m) + 100.0) * 100.0)

def procesar_fila(row):
    num = row.get("#", 0)
    liga = str(row.get("Liga", "") or "").strip()
    loc = str(row.get("Local", "") or "").strip()
    vis = str(row.get("Visita", "") or "").strip()
    
    ml, me, mv = limpiar_momio(row.get("Momio Local")), limpiar_momio(row.get("Momio Empate")), limpiar_momio(row.get("Momio Visitante"))
    ol, oe, ov = limpiar_momio(row.get("Apertura Local")), limpiar_momio(row.get("Apertura Empate")), limpiar_momio(row.get("Apertura Visitante"))
    
    if not loc or ml is None or me is None or mv is None:
        return {
            "#": num, "Liga": liga, "Partido": f"{loc} vs {vis}" if loc else f"Partido #{num}",
            "Momio Local": row.get("Momio Local", ""), "Momio Empate": row.get("Momio Empate", ""), "Momio Visitante": row.get("Momio Visitante", ""),
            "Over 2.5": row.get("Over 2.5", ""), "Under 2.5": row.get("Under 2.5", ""),
            "Prob. Local (%)": "-", "Prob. Empate (%)": "-", "Prob. Visitante (%)": "-",
            "Favorito": "-", "Dif. Probabilidad (%)": "-", "Smart Money": "-", "PRO Line Alert": "-", "Clasificación Partido": "EN ESPERA"
        }

    pl, pe, pv = calcular_prob(ml), calcular_prob(me), calcular_prob(mv)
    s = pl + pe + pv
    pl_n, pe_n, pv_n = (pl/s*100), (pe/s*100), (pv/s*100)

    # Columna L: Smart Money automático
    smart = "Estable"
    if ol and oe and ov:
        pol, poe, pov = calcular_prob(ol), calcular_prob(oe), calcular_prob(ov)
        so = pol + poe + pov
        diff_l = pl_n - (pol/so*100)
        diff_v = pv_n - (pov/so*100)
        if diff_l >= 3.5: smart = f"🔥 Dinero a Local (+{diff_l:.1f}%)"
        elif diff_v >= 3.5: smart = f"🔥 Dinero a Visita (+{diff_v:.1f}%)"

    # Columna M: PRO Line Alert automático (-140)
    alerta_pro = "Estable"
    if ol and ml:
        if ol > -140 and ml <= -140: alerta_pro = "🔥 Fijo Activado (Local <= -140)"
        elif ol <= -140 and ml > -140: alerta_pro = "⚠️ Fuga Institucional (Local > -140)"
    if ov and mv:
        if ov > -140 and mv <= -140: alerta_pro = "🔥 Fijo Activado (Visita <= -140)"
        elif ov <= -140 and mv > -140: alerta_pro = "⚠️ Fuga Institucional (Visita > -140)"

    dif = abs(pl_n - pv_n)
    fav = "Local" if pl_n > pv_n else "Visitante"
    clasif = "FAVORITO FUERTE" if dif >= 35 else ("ZONA DE EMPATE" if (dif < 10 and pe_n >= 29) else ("FAVORITO MEDIO" if dif >= 10 else "PARTIDO TRAMPA"))

    return {
        "#": num, "Liga": liga, "Partido": f"{loc} vs {vis}",
        "Momio Local": str(row.get("Momio Local", "")), "Momio Empate": str(row.get("Momio Empate", "")), "Momio Visitante": str(row.get("Momio Visitante", "")),
        "Over 2.5": str(row.get("Over 2.5", "")), "Under 2.5": str(row.get("Under 2.5", "")),
        "Prob. Local (%)": f"{pl_n:.2f}%", "Prob. Empate (%)": f"{pe_n:.2f}%", "Prob. Visitante (%)": f"{pv_n:.2f}%",
        "Favorito": fav, "Dif. Probabilidad (%)": f"{dif:.2f}%", "Smart Money": smart, "PRO Line Alert": alerta_pro, "Clasificación Partido": clasif
    }

# ------------------------------------------------------------------------------
# 3. INTERFAZ DE NAVEGACIÓN
# ------------------------------------------------------------------------------
st.title("⚽ Centro de Mando Progol v4.0 Ultra")
df_analisis = pd.DataFrame([procesar_fila(r) for r in st.session_state["tabla_progol"]])
partidos_validos = [p for p in df_analisis[df_analisis["Clasificación Partido"] != "EN ESPERA"]["Partido"].tolist() if p != "-"]

modulos = [
    "📊 1. ANÁLISIS 1 (Excel)", "🌐 2. Big Data API-Sports", "🤝 3. Detector de Empates", "🔥 4. Detector de Trampas",
    "🎯 5. Dixon-Coles & Poisson", "🎫 6. Quiniela Múltiple", "🎰 7. Matriz Reducida", "📋 8. CAPTURA Y EDICIÓN"
]

f1 = st.columns(4)
for i in range(4):
    if f1[i].button(modulos[i], type="primary" if st.session_state["menu_activo"] == modulos[i] else "secondary", use_container_width=True):
        st.session_state["menu_activo"] = modulos[i]
        st.rerun()

f2 = st.columns(4)
for j in range(4):
    if f2[j].button(modulos[4+j], type="primary" if st.session_state["menu_activo"] == modulos[4+j] else "secondary", use_container_width=True):
        st.session_state["menu_activo"] = modulos[4+j]
        st.rerun()

st.divider()

# ------------------------------------------------------------------------------
# 4. CONTENIDO DE MÓDULOS
# ------------------------------------------------------------------------------
if st.session_state["menu_activo"] == "📊 1. ANÁLISIS 1 (Excel)":
    st.subheader("Tabla Maestra de Análisis Cuantitativo (14 Partidos)")
    st.dataframe(df_analisis, width="stretch", height=540)

elif st.session_state["menu_activo"] == "🌐 2. Big Data API-Sports":
    st.subheader("🌐 Extracción Multitorneo en Vivo desde API-Sports")
    if partidos_validos:
        p_sel = st.selectbox("Selecciona partido a consultar:", partidos_validos)
        num_p = int(df_analisis[df_analisis["Partido"] == p_sel].iloc[0]["#"])
        p_data = st.session_state["tabla_progol"][num_p - 1]
        eq_l, eq_v = p_data.get("Local"), p_data.get("Visita")

        if st.button(f"🚀 Descargar Big Data para {eq_l} vs {eq_v}", type="primary"):
            with st.spinner("Descargando datos..."):
                info_l = MotorAPISportsUltra.buscar_equipo_dinamico(eq_l)
                info_v = MotorAPISportsUltra.buscar_equipo_dinamico(eq_v)
                if info_l and info_v:
                    df_h2h = MotorAPISportsUltra.obtener_h2h(info_l["id"], info_v["id"])
                    st.session_state["api_cache_xg"][p_sel] = {
                        "info_l": info_l, "info_v": info_v, "df_h2h": df_h2h.to_dict("records")
                    }
                    guardar_cache_api(st.session_state["api_cache_xg"])
                    st.success(f"Equipos encontrados: {info_l['nombre']} vs {info_v['nombre']}")
                else:
                    st.error("No se pudo localizar uno de los clubes en la API.")

        if p_sel in st.session_state["api_cache_xg"]:
            cache = st.session_state["api_cache_xg"][p_sel]
            df_h = pd.DataFrame(cache["df_h2h"])
            st.divider()
            st.subheader("Historial Frente a Frente (H2H)")
            if not df_h.empty:
                opc_filtro = st.radio(
                    "Filtro de Estadio:",
                    ["Mostrar todos", f"Solo en estadio de {cache['info_l']['nombre']} (Local)"],
                    horizontal=True,
                    key=f"filtro_estadio_{p_sel}"
                )
                if "Solo en estadio" in opc_filtro:
                    id_loc_target = int(cache["info_l"]["id"])
                    df_h_show = df_h[df_h["home_id"] == id_loc_target]
                else:
                    df_h_show = df_h
                st.dataframe(df_h_show[["Fecha", "Torneo", "Local", "Resultado", "Visita"]], width="stretch")
    else:
        st.info("Captura primero partidos en el Módulo 8.")

elif st.session_state["menu_activo"] == "🎰 7. Matriz Reducida":
    st.subheader("🎰 Matriz Reducida Configurable (7 u 8 Dobles)")
    n_dobles = st.radio("Cantidad de Dobles:", [7, 8], horizontal=True)
    st.write(f"Configuración activa: **{n_dobles} Dobles y {14 - n_dobles} Fijos** en 12 Boletos.")

elif st.session_state["menu_activo"] == "📋 8. CAPTURA Y EDICIÓN":
    st.subheader("Edición de Quiniela Manual y Sincronización")
    st.info("💡 Captura o sincroniza desde tu Google Sheet. Las columnas L (Smart Money) y M (PRO Line Alert) se calculan automáticamente.")
    
    df_cap = pd.DataFrame(st.session_state["tabla_progol"])
    grid = st.data_editor(
        df_cap,
        column_order=["#", "Liga", "Local", "Visita", "Momio Local", "Momio Empate", "Momio Visitante", "Over 2.5", "Under 2.5", "Apertura Local", "Apertura Empate", "Apertura Visitante"],
        num_rows="fixed",
        width="stretch",
        key="editor_grid"
    )

    c1, c2 = st.columns(2)
    with c1:
        if st.button("💾 Guardar Cambios Manuales", type="primary"):
            st.session_state["tabla_progol"] = grid.to_dict("records")
            guardar_disco(st.session_state["tabla_progol"])
            st.success("Guardado en disco.")
            st.rerun()
    with c2:
        if st.button("🧹 Empezar en Blanco"):
            st.session_state["tabla_progol"] = TABLA_EN_BLANCO
            guardar_disco(TABLA_EN_BLANCO)
            st.session_state["api_cache_xg"] = {}
            guardar_cache_api({})
            st.rerun()

    st.divider()
    st.subheader("🌐 Sincronización Directa con Google Sheets")
    st.text_input("URL Vinculada:", value=URL_GOOGLE_SHEET_DEFAULT, disabled=True)
    
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        if st.button("🔄 Cargar datos desde Google Sheets", type="primary", use_container_width=True):
            try:
                csv_url = URL_GOOGLE_SHEET_DEFAULT.split("/edit")[0] + "/export?format=csv"
                df_g = pd.read_csv(csv_url)
                nuevos = []
                for i in range(14):
                    if i < len(df_g):
                        r = df_g.iloc[i].to_dict()
                        nuevos.append({
                            "#": i + 1,
                            "Liga": str(r.get("Liga", "Liga MX") or "Liga MX").strip(),
                            "Local": str(r.get("Local", "") or "").strip(),
                            "Visita": str(r.get("Visita", "") or "").strip(),
                            "Momio Local": str(r.get("Momio Local", "") or "").strip(),
                            "Momio Empate": str(r.get("Momio Empate", "") or "").strip(),
                            "Momio Visitante": str(r.get("Momio Visitante", "") or "").strip(),
                            "Over 2.5": str(r.get("Over 2.5", "") or "").strip(),
                            "Under 2.5": str(r.get("Under 2.5", "") or "").strip(),
                            "Apertura Local": str(r.get("Apertura Local", "") or "").strip(),
                            "Apertura Empate": str(r.get("Apertura Empate", "") or "").strip(),
                            "Apertura Visitante": str(r.get("Apertura Visitante", "") or "").strip()
                        })
                    else:
                        nuevos.append(TABLA_EN_BLANCO[i])
                st.session_state["tabla_progol"] = nuevos
                guardar_disco(nuevos)
                st.success("✅ ¡14 casilleros importados exitosamente desde Google Sheets!")
                st.rerun()
            except Exception as e:
                st.error(f"Error al leer Google Sheets: {e}. Asegúrate de que el documento tenga permisos de lectura públicos.")

    with col_g2:
        buffer_excel = io.BytesIO()
        with pd.ExcelWriter(buffer_excel, engine="openpyxl") as writer:
            df_analisis.to_excel(writer, sheet_name="ANALISIS_Y_COL_L_M", index=False)
        
        st.download_button(
            label="📥 Descargar Reporte con Columnas L y M (.xlsx)",
            data=buffer_excel.getvalue(),
            file_name="Progol_Reporte_Con_Alertas.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
