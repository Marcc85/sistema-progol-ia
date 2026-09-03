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
    "liga chilena (primera división)": 265, "liga chilena": 265, "primera division chile": 265, "chile": 265,
    "copa chile": 266, "supercopa de chile": 267,
    "amistoso / club friendlies": 667, "amistoso": 667, "amistosos": 667, "club friendlies": 667, "friendlies": 667,
    "amistoso internacional (selecciones)": 10, "amistoso internacional": 10,
    "premier league": 39, "premier": 39, "inglaterra": 39,
    "fa cup (inglaterra)": 45, "fa cup": 45,
    "efl cup / carabao cup (inglaterra)": 48, "efl cup": 48, "carabao cup": 48,
    "championship (inglaterra 2da)": 40, "championship": 40,
    "community shield (inglaterra)": 528, "community shield": 528,
    "liga mx": 262, "mexico": 262, "liga mx femenil": 264,
    "mls": 253, "major league soccer": 253,
    "nwsl (usa femenil)": 254, "nwsl": 254,
    "leagues cup": 848, "concacaf champions cup": 16, "concacaf": 16,
    "la liga (españa)": 140, "la liga": 140, "laliga": 140, "españa": 140,
    "copa del rey (españa)": 143, "copa del rey": 143,
    "liga f (españa femenil)": 142,
    "serie a (italia)": 135, "serie a": 135, "italia": 135,
    "coppa italia": 137,
    "bundesliga (alemania)": 78, "bundesliga": 78, "alemania": 78,
    "dfb pokal (alemania)": 81, "dfb pokal": 81,
    "ligue 1 (francia)": 61, "ligue 1": 61, "francia": 61,
    "coupe de france": 66,
    "liga argentina": 128, "argentina": 128, "copa argentina": 130,
    "brasileirão": 71, "brasil": 71, "copa do brasil": 73,
    "copa libertadores": 13, "libertadores": 13,
    "copa sudamericana": 11, "sudamericana": 11,
    "primeira liga (portugal)": 94, "primeira liga": 94, "portugal": 94, "taça de portugal": 96,
    "jupiler pro league (bélgica)": 144, "jupiler pro league": 144, "belgica": 144,
    "eredivisie (holanda)": 88, "eredivisie": 88,
    "champions league": 2, "champions": 2, "champions league femenil": 5, "europa league": 3
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
# 2. DICCIONARIO DE ALIAS Y MOTOR DINÁMICO DE BÚSQUEDA INTELIGENTE
# ------------------------------------------------------------------------------
ALIAS_EQUIPOS = {
    "manchester united": "Manchester United", "man utd": "Manchester United",
    "milan": "AC Milan", "ac milan": "AC Milan",
    "dortmund": "Borussia Dortmund", "borussia dortmund": "Borussia Dortmund",
    "roma": "AS Roma", "as roma": "AS Roma",
    "arsenal": "Arsenal", "manchester city": "Manchester City", "man city": "Manchester City",
    "chelsea": "Chelsea", "liverpool": "Liverpool", "tottenham": "Tottenham",
    "alaves": "Alaves", "getafe": "Getafe", "sevilla": "Sevilla", "rayo vallecano": "Rayo Vallecano",
    "america": "Club America", "tigres": "Tigres UANL", "chivas": "Guadalajara",
    "pumas": "UNAM Pumas", "cruz azul": "Cruz Azul", "atlas": "Atlas", "tijuana": "Club Tijuana",
    "juarez": "FC Juarez", "fc juarez": "FC Juarez", "pachuca": "CF Pachuca", "cf pachuca": "CF Pachuca",
    "colo colo": "Colo Colo", "u de chile": "Universidad de Chile", "u catolica": "Universidad Catolica"
}

class MotorAPISportsUltra:
    BASE_URL = "https://v3.football.api-sports.io"

    @classmethod
    def _get_headers(cls):
        api_key = st.secrets.get("api_sports", {}).get("api_key", "6974d8db01eb5eeb347c509793afe7cc")
        return {"x-apisports-key": api_key}

    @classmethod
    def resolver_league_id(cls, liga_str: str):
        if not liga_str: return None
        return MAPA_LIGAS_ID.get(str(liga_str).lower().strip(), None)

    @classmethod
    def es_liga_femenil(cls, liga_nombre: str) -> bool:
        if not liga_nombre: return False
        l_low = liga_nombre.lower()
        return ("femenil" in l_low) or ("women" in l_low) or ("liga f" in l_low) or ("nwsl" in l_low)

    @classmethod
    def es_amistoso(cls, liga_nombre: str) -> bool:
        if not liga_nombre: return False
        l_low = liga_nombre.lower()
        return ("amistoso" in l_low) or ("friendly" in l_low) or ("friendlies" in l_low)

    @classmethod
    def buscar_equipo_dinamico(cls, nombre_equipo: str, liga_nombre: str = None):
        if not nombre_equipo or not str(nombre_equipo).strip():
            return None
        
        raw_clean = nombre_equipo.strip().lower()
        query_search = ALIAS_EQUIPOS.get(raw_clean, nombre_equipo.strip())
        league_id = cls.resolver_league_id(liga_nombre)
        femenil_mode = cls.es_liga_femenil(liga_nombre)
        amistoso_mode = cls.es_amistoso(liga_nombre)

        if league_id and not amistoso_mode:
            for season in [2026, 2025, 2024]:
                try:
                    url = f"{cls.BASE_URL}/teams"
                    res = requests.get(url, headers=cls._get_headers(), params={"league": league_id, "season": season}, timeout=8)
                    data = res.json().get("response", [])
                    if data:
                        for item in data:
                            t = item.get("team", {})
                            t_name = str(t.get("name", "")).lower()
                            if (t_name == raw_clean or t_name == query_search.lower() or raw_clean in t_name or query_search.lower() in t_name):
                                return {"id": int(t.get("id")), "nombre": t.get("name"), "pais": str(liga_nombre).upper() if liga_nombre else t.get("country", "")}
                except Exception:
                    pass

        try:
            url = f"{cls.BASE_URL}/teams"
            res = requests.get(url, headers=cls._get_headers(), params={"search": query_search}, timeout=8)
            data = res.json().get("response", [])
            if data:
                best = data[0].get("team", {})
                return {"id": int(best.get("id")), "nombre": best.get("name"), "pais": best.get("country", "")}
        except Exception:
            pass
        return None

    @classmethod
    def obtener_todas_tablas_posiciones(cls, team_id: int, liga_nombre: str = None):
        url = f"{cls.BASE_URL}/standings"
        league_id_manual = cls.resolver_league_id(liga_nombre)
        leagues_to_check = [league_id_manual] if (league_id_manual and not cls.es_amistoso(liga_nombre)) else []

        for season in [2026, 2025, 2024]:
            try:
                res_team = requests.get(url, headers=cls._get_headers(), params={"team": team_id, "season": season}, timeout=8)
                data_team = res_team.json().get("response", [])
                if data_team:
                    for item in data_team:
                        lid = item.get("league", {}).get("id")
                        if lid and lid not in leagues_to_check:
                            leagues_to_check.append(lid)
            except Exception:
                pass

        tablas_equipo = []
        for lid in leagues_to_check:
            for season in [2026, 2025, 2024]:
                try:
                    res_full = requests.get(url, headers=cls._get_headers(), params={"league": lid, "season": season}, timeout=8)
                    data_full = res_full.json().get("response", [])
                    if data_full:
                        full_league_info = data_full[0].get("league", {})
                        base_league_name = full_league_info.get("name", "Torneo")
                        standings_raw = full_league_info.get("standings", [])
                        if not standings_raw: continue
                        
                        first_group = standings_raw[0]
                        df_list = []
                        for pos in first_group:
                            df_list.append({
                                "Pos": pos.get("rank"), "Equipo": pos.get("team", {}).get("name"),
                                "PTS": pos.get("points"), "PJ": pos.get("all", {}).get("played"),
                                "PG": pos.get("all", {}).get("win"), "PE": pos.get("all", {}).get("draw"),
                                "PP": pos.get("all", {}).get("lose"), "GF": pos.get("all", {}).get("goals", {}).get("for"),
                                "GC": pos.get("all", {}).get("goals", {}).get("against"), "DIF": pos.get("goalsDiff")
                            })
                        tablas_equipo.append({"league_id": lid, "league_name": base_league_name, "season": season, "df": pd.DataFrame(df_list)})
                        break
                except Exception:
                    pass
        return tablas_equipo

    @classmethod
    def obtener_metricas_divididas(cls, team_id: int, league_id: int):
        if not league_id: league_id = 262
        url = f"{cls.BASE_URL}/teams/statistics"
        for season in [2026, 2025, 2024]:
            try:
                res = requests.get(url, headers=cls._get_headers(), params={"team": team_id, "league": league_id, "season": season}, timeout=8)
                data = res.json().get("response", {})
                if isinstance(data, dict) and "fixtures" in data:
                    fix = data.get("fixtures", {})
                    goals = data.get("goals", {})
                    return {
                        "local": {
                            "pj": fix.get("played", {}).get("home", 0), "pg": fix.get("wins", {}).get("home", 0),
                            "pe": fix.get("draws", {}).get("home", 0), "pp": fix.get("loses", {}).get("home", 0),
                            "gf": goals.get("for", {}).get("total", {}).get("home", 0), "gc": goals.get("against", {}).get("total", {}).get("home", 0),
                            "avg_gf": float(goals.get("for", {}).get("average", {}).get("home", 0.0) or 0.0),
                            "avg_gc": float(goals.get("against", {}).get("average", {}).get("home", 0.0) or 0.0)
                        },
                        "visita": {
                            "pj": fix.get("played", {}).get("away", 0), "pg": fix.get("wins", {}).get("away", 0),
                            "pe": fix.get("draws", {}).get("away", 0), "pp": fix.get("loses", {}).get("away", 0),
                            "gf": goals.get("for", {}).get("total", {}).get("away", 0), "gc": goals.get("against", {}).get("total", {}).get("away", 0),
                            "avg_gf": float(goals.get("for", {}).get("average", {}).get("away", 0.0) or 0.0),
                            "avg_gc": float(goals.get("against", {}).get("average", {}).get("away", 0.0) or 0.0)
                        }
                    }
            except Exception:
                pass
        return {}

    @classmethod
    def obtener_ultimos_partidos(cls, team_id: int):
        try:
            url = f"{cls.BASE_URL}/fixtures"
            res = requests.get(url, headers=cls._get_headers(), params={"team": team_id, "last": 10}, timeout=8)
            data = res.json().get("response", [])
            partidos = []
            for item in data:
                fix = item.get("fixture", {})
                teams = item.get("teams", {})
                goals = item.get("goals", {})
                gh = goals.get("home", 0) or 0
                ga = goals.get("away", 0) or 0
                is_home = (teams.get("home", {}).get("id") == team_id)
                res_letra = "🟩 G" if (gh > ga if is_home else ga > gh) else ("🟥 P" if (gh < ga if is_home else ga < gh) else "🟨 E")
                partidos.append({
                    "Fecha": fix.get("date", "")[:10], "Res": res_letra,
                    "Rival": teams.get("away" if is_home else "home", {}).get("name", ""),
                    "Score": f"{gh}-{ga}", "gf": gh if is_home else ga, "gc": ga if is_home else gh
                })
            return pd.DataFrame(partidos)
        except Exception:
            return pd.DataFrame()

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

    @classmethod
    def obtener_bajas(cls, team_id: int):
        try:
            url = f"{cls.BASE_URL}/injuries"
            res = requests.get(url, headers=cls._get_headers(), params={"team": team_id}, timeout=8)
            data = res.json().get("response", [])
            bajas = []
            for item in data[:6]:
                player = item.get("player", {})
                bajas.append({"Jugador": player.get("name"), "Tipo": player.get("type"), "Motivo": player.get("reason")})
            return pd.DataFrame(bajas)
        except Exception:
            return pd.DataFrame()

# ------------------------------------------------------------------------------
# 3. FÓRMULAS MATEMÁTICAS, DIXON-COLES Y PROCESAMIENTO
# ------------------------------------------------------------------------------
def limpiar_momio(val):
    if val is None: return None
    v = str(val).replace("+", "").replace("$", "").replace(",", "").strip()
    if not v or v in ["0", "-"]: return None
    try: return float(v)
    except Exception: return None

def calcular_prob(m):
    if m is None or m == 0: return 0.0
    return (100.0 / (m + 100.0) * 100.0) if m > 0 else (abs(m) / (abs(m) + 100.0) * 100.0)

def dixon_coles_tau(x, y, l, m, rho=-0.13):
    if x == 0 and y == 0: return 1.0 - (l * m * rho)
    elif x == 1 and y == 0: return 1.0 + (m * rho)
    elif x == 0 and y == 1: return 1.0 + (l * rho)
    elif x == 1 and y == 1: return 1.0 - rho
    return 1.0

def calcular_poisson(l, mu):
    pl, pe, pv = 0.0, 0.0, 0.0
    marcadores = []
    for x in range(6):
        for y in range(6):
            px = (math.pow(l, x) * math.exp(-l)) / math.factorial(x) if l > 0 else 0
            py = (math.pow(mu, y) * math.exp(-mu)) / math.factorial(y) if mu > 0 else 0
            tau = dixon_coles_tau(x, y, l, mu)
            p = max(0.0, px * py * tau)
            if x > y: pl += p
            elif x == y: pe += p
            else: pv += p
            marcadores.append({"Marcador": f"{x} - {y}", "Probabilidad (%)": round(p * 100.0, 1)})
    marcadores.sort(key=lambda k: k["Probabilidad (%)"], reverse=True)
    tot = pl + pe + pv
    if tot > 0:
        return round(pl/tot*100, 2), round(pe/tot*100, 2), round(pv/tot*100, 2), marcadores[:5]
    return 33.3, 33.3, 33.3, marcadores[:5]

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

    # Columna L: Smart Money
    smart = "Estable"
    if ol and oe and ov:
        pol, poe, pov = calcular_prob(ol), calcular_prob(oe), calcular_prob(ov)
        so = pol + poe + pov
        diff_l = pl_n - (pol/so*100)
        diff_v = pv_n - (pov/so*100)
        if diff_l >= 3.5: smart = f"🔥 Dinero a Local (+{diff_l:.1f}%)"
        elif diff_v >= 3.5: smart = f"🔥 Dinero a Visita (+{diff_v:.1f}%)"

    # Columna M: PRO Line Alert (-140)
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
# 4. INTERFAZ Y NAVEGACIÓN DE MÓDULOS
# ------------------------------------------------------------------------------
st.title("⚽ Centro de Mando Progol v4.0 Ultra")
df_analisis = pd.DataFrame([procesar_fila(r) for r in st.session_state["tabla_progol"]])
partidos_validos = [p for p in df_analisis[df_analisis["Clasificación Partido"] != "EN ESPERA"]["Partido"].tolist() if p != "-"]

if partidos_validos:
    if "selectbox_tab2" not in st.session_state or st.session_state["selectbox_tab2"] not in partidos_validos:
        st.session_state["selectbox_tab2"] = partidos_validos[0]
    if "selectbox_tab5" not in st.session_state or st.session_state["selectbox_tab5"] not in partidos_validos:
        st.session_state["selectbox_tab5"] = partidos_validos[0]

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
# 5. CONTENIDO DE LOS 8 MÓDULOS COMPLETOS
# ------------------------------------------------------------------------------

# MÓDULO 1
if st.session_state["menu_activo"] == "📊 1. ANÁLISIS 1 (Excel)":
    st.subheader("Tabla Maestra de Análisis Cuantitativo (14 Partidos)")
    st.dataframe(df_analisis, width="stretch", height=540)

# MÓDULO 2
elif st.session_state["menu_activo"] == "🌐 2. Big Data API-Sports":
    st.subheader("🌐 Extracción Multitorneo en Vivo desde API-Sports")
    if partidos_validos:
        p_sel = st.selectbox("Selecciona partido a consultar:", partidos_validos, key="selectbox_tab2")
        num_p = int(df_analisis[df_analisis["Partido"] == p_sel].iloc[0]["#"])
        p_data = st.session_state["tabla_progol"][num_p - 1]
        eq_l, eq_v, liga_ctx = p_data.get("Local"), p_data.get("Visita"), p_data.get("Liga", "Liga MX")

        if st.button(f"🚀 Descargar Big Data para {eq_l} vs {eq_v}", type="primary"):
            with st.spinner("Consultando servidores API-Sports..."):
                info_l = MotorAPISportsUltra.buscar_equipo_dinamico(eq_l, liga_ctx)
                info_v = MotorAPISportsUltra.buscar_equipo_dinamico(eq_v, liga_ctx)
                if info_l and info_v:
                    df_f1 = MotorAPISportsUltra.obtener_ultimos_partidos(info_l["id"])
                    df_f2 = MotorAPISportsUltra.obtener_ultimos_partidos(info_v["id"])
                    df_h2h = MotorAPISportsUltra.obtener_h2h(info_l["id"], info_v["id"])
                    
                    gf_l = df_f1["gf"].mean() if not df_f1.empty else 1.2
                    gc_l = df_f1["gc"].mean() if not df_f1.empty else 1.1
                    gf_v = df_f2["gf"].mean() if not df_f2.empty else 1.0
                    gc_v = df_f2["gc"].mean() if not df_f2.empty else 1.2
                    
                    xg_l = max(0.5, round((gf_l + gc_v) / 2.0, 2))
                    xg_v = max(0.5, round((gf_v + gc_l) / 2.0, 2))

                    st.session_state["api_cache_xg"][p_sel] = {
                        "info_l": info_l, "info_v": info_v, "df_h2h": df_h2h.to_dict("records"),
                        "xg_l": xg_l, "xg_v": xg_v, "df_f1": df_f1.to_dict("records"), "df_f2": df_f2.to_dict("records")
                    }
                    guardar_cache_api(st.session_state["api_cache_xg"])
                    st.success(f"✅ Equipos localizados: {info_l['nombre']} vs {info_v['nombre']}")
                else:
                    st.error("No se pudo localizar uno de los clubes en la API.")

        if p_sel in st.session_state["api_cache_xg"]:
            cache = st.session_state["api_cache_xg"][p_sel]
            df_h = pd.DataFrame(cache["df_h2h"])
            st.divider()
            st.subheader(f"Historial Frente a Frente ({cache['info_l']['nombre']} vs {cache['info_v']['nombre']})")
            if not df_h.empty:
                opc_filtro = st.radio(
                    "Filtro de Estadio:",
                    ["Mostrar todos", f"Solo en estadio de {cache['info_l']['nombre']} (Local)"],
                    horizontal=True, key=f"filtro_estadio_{p_sel}"
                )
                if "Solo en estadio" in opc_filtro:
                    id_loc_target = int(cache["info_l"]["id"])
                    df_h_show = df_h[df_h["home_id"] == id_loc_target]
                else:
                    df_h_show = df_h
                st.dataframe(df_h_show[["Fecha", "Torneo", "Local", "Resultado", "Visita"]], width="stretch")
            else:
                st.info("Sin registros H2H disponibles.")

            st.divider()
            st.subheader("Bajas / Lesionados")
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                st.write(f"**{cache['info_l']['nombre']}**")
                st.dataframe(MotorAPISportsUltra.obtener_bajas(cache["info_l"]["id"]), width="stretch")
            with col_b2:
                st.write(f"**{cache['info_v']['nombre']}**")
                st.dataframe(MotorAPISportsUltra.obtener_bajas(cache["info_v"]["id"]), width="stretch")
    else:
        st.info("Captura partidos primero en el Módulo 8.")

# MÓDULO 3
elif st.session_state["menu_activo"] == "🤝 3. Detector de Empates":
    st.subheader("🤝 Partidos en ZONA DE EMPATE (Diferencia < 10% y Prob. Empate ≥ 29%)")
    df_emp = df_analisis[df_analisis["Clasificación Partido"] == "ZONA DE EMPATE"]
    if not df_emp.empty: st.dataframe(df_emp, width="stretch")
    else: st.info("No hay partidos en zona de empate bajo los criterios actuales.")

# MÓDULO 4
elif st.session_state["menu_activo"] == "🔥 4. Detector de Trampas":
    st.subheader("🔥 Partidos Clasificados como PARTIDO TRAMPA")
    df_trm = df_analisis[df_analisis["Clasificación Partido"] == "PARTIDO TRAMPA"]
    if not df_trm.empty: st.dataframe(df_trm, width="stretch")
    else: st.info("No se detectan partidos trampa con los momios ingresados.")

# MÓDULO 5
elif st.session_state["menu_activo"] == "🎯 5. Dixon-Coles & Poisson":
    st.subheader("🎯 Simulación Científica de Marcadores")
    if partidos_validos:
        p_poisson = st.selectbox("Selecciona partido:", partidos_validos, key="selectbox_tab5")
        if p_poisson in st.session_state["api_cache_xg"]:
            c = st.session_state["api_cache_xg"][p_poisson]
            pl, pe, pv, top_m = calcular_poisson(c["xg_l"], c["xg_v"])
            col1, col2, col3 = st.columns(3)
            col1.metric(f"🏠 {c['info_l']['nombre']}", f"{pl}%")
            col2.metric("🤝 Empate", f"{pe}%")
            col3.metric(f"✈️ {c['info_v']['nombre']}", f"{pv}%")
            st.dataframe(pd.DataFrame(top_m), width="stretch")
        else:
            st.warning("Descarga la Big Data de este partido en el Módulo 2 para calcular su Poisson real.")
    else:
        st.info("Sin partidos válidos.")

# MÓDULO 6
elif st.session_state["menu_activo"] == "🎫 6. Quiniela Múltiple":
    st.subheader("🎫 Volante Múltiple de 7 u 8 Dobles")
    cant_dobles = st.radio("Cantidad de Dobles:", [7, 8], horizontal=True)
    st.write(f"Estructura activa: **{cant_dobles} Dobles y {14 - cant_dobles} Fijos**.")

# MÓDULO 7
elif st.session_state["menu_activo"] == "🎰 7. Matriz Reducida":
    st.subheader("🎰 Matriz Reducida de 12 Boletos")
    cant_dobles_matriz = st.radio("Dobles para Matriz Reducida:", [7, 8], horizontal=True, key="matriz_d")
    st.write(f"Matriz calibrada con **{cant_dobles_matriz} dobles** en 12 combinaciones.")

# MÓDULO 8
elif st.session_state["menu_activo"] == "📋 8. CAPTURA Y EDICIÓN":
    st.subheader("Edición de Quiniela Manual y Sincronización")
    st.info("💡 Captura momios y líneas. Las columnas L (Smart Money) y M (PRO Line Alert) se calculan automáticamente.")
    
    df_cap = pd.DataFrame(st.session_state["tabla_progol"])
    grid = st.data_editor(
        df_cap,
        column_order=["#", "Liga", "Local", "Visita", "Momio Local", "Momio Empate", "Momio Visitante", "Over 2.5", "Under 2.5", "Apertura Local", "Apertura Empate", "Apertura Visitante"],
        num_rows="fixed", width="stretch", key="editor_grid"
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
