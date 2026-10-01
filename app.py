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


def sincronizar_google_sheet(url_sheet):
    try:
        if "/edit" in url_sheet:
            url_csv = url_sheet.split("/edit")[0] + "/export?format=csv"
        else:
            url_csv = url_sheet

        df_gs = pd.read_csv(url_csv)
        
        datos_sincronizados = []
        for index, row in df_gs.head(14).iterrows():
            partido_dict = {
                "#": index + 1,
                "Liga": str(row.get("Liga", "Liga MX")),
                "Local": str(row.get("Local", "")).strip().title(),
                "Visita": str(row.get("Visita", "")).strip().title(),
                "Momio Local": str(row.get("Momio Local", "")),
                "Momio Empate": str(row.get("Momio Empate", "")),
                "Momio Visitante": str(row.get("Momio Visitante", "")),
                "Apertura Local": str(row.get("Apertura Local", "")),
                "Apertura Empate": str(row.get("Apertura Empate", "")),
                "Apertura Visitante": str(row.get("Apertura Visitante", "")),
                "Over 2.5": str(row.get("Over 2.5", "")),
                "Under 2.5": str(row.get("Under 2.5", ""))
            }
            datos_sincronizados.append(partido_dict)
            
        return datos_sincronizados
    except Exception as e:
        st.error(f"Error al conectar con Google Sheets: {e}")
        return None
      

# ---------------------------------------------------------------------------
# 0. ESTILOS VISUALES RESPONSIBOS Y FORMATO DE IMPRESIÓN LIMPIO
# ---------------------------------------------------------------------------

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
# 1. ARCHIVOS DE DISCO Y LISTA COMPLETA DE LIGAS, COPAS Y AMISTOSOS
# ------------------------------------------------------------------------------
ARCHIVO_DISCO = "progol_captura_v7.json"
ARCHIVO_CACHE_API = "progol_bigdata_cache.json"

@st.cache_data(ttl=86400)
def cargar_catalogo_global_ligas():
    return {
        "Liga MX (Mexico)": 262,
        "Premier League (England)": 39,
        "La Liga (Spain)": 140,
        "Serie A (Italy)": 135,
        "Bundesliga (Germany)": 78,
        "Ligue 1 (France)": 61,
        "Champions League (World)": 2,
        "Copa Libertadores (South America)": 13,
        "MLS (USA)": 253,
        "Primeira Liga (Portugal)": 94,
        "Eredivisie (Netherlands)": 88,
        "Liga Profesional (Argentina)": 128,
        "Brasileirao (Brazil)": 71,
        "Primera División (Chile)": 265,
        "Copa Chile (Chile)": 266,
        "Supercopa de Chile (Chile)": 267,
        "Amistosos / Club Friendlies (World)": 667,
        "FA Cup (England)": 45,
        "EFL Cup (England)": 48,
        "Championship (England)": 40,
        "Copa del Rey (Spain)": 143,
        "Coppa Italia (Italy)": 137,
        "DFB Pokal (Germany)": 81,
        "Coupe de France (France)": 66,
        "Copa Argentina (Argentina)": 130,
        "Copa do Brasil (Brazil)": 73,
        "Copa Sudamericana (South America)": 11
    }

@st.cache_data(ttl=86400)
def obtener_equipos_api(league_id):
    url = "https://v3.football.api-sports.io/teams"
    headers = {
        "x-rapidapi-key": st.secrets.get("API_KEY", "TU_API_KEY_AQUI"),
        "x-rapidapi-host": "v3.football.api-sports.io"
    }
    params = {"league": league_id, "season": 2026}
    
    diccionario_equipos = {}
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json().get("response", [])
            for item in data:
                team_info = item.get("team", {})
                team_name = team_info.get("name")
                team_id = team_info.get("id")
                if team_name and team_id:
                    diccionario_equipos[team_name.lower().strip()] = team_id
    except Exception:
        pass
        
    return diccionario_equipos    

LIGAS_IDS_API = cargar_catalogo_global_ligas()
OPCIONES_LIGAS = sorted(list(LIGAS_IDS_API.keys()))
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
    "liga chilena (primera división)": 265,
    "liga chilena": 265,
    "primera division chile": 265,
    "chile": 265,
    "copa chile": 266,
    "supercopa de chile": 267,
    "amistoso / club friendlies": 667,
    "amistoso": 667,
    "amistosos": 667,
    "club friendlies": 667,
    "friendlies": 667,
    "amistoso internacional (selecciones)": 10,
    "amistoso internacional": 10,
    "premier league": 39,
    "premier": 39,
    "inglaterra": 39,
    "fa cup (inglaterra)": 45,
    "fa cup": 45,
    "efl cup / carabao cup (inglaterra)": 48,
    "efl cup": 48,
    "carabao cup": 48,
    "championship (inglaterra 2da)": 40,
    "championship": 40,
    "community shield (inglaterra)": 528,
    "community shield": 528,
    "liga mx": 262,
    "mexico": 262,
    "liga mx femenil": 264,
    "mls": 253,
    "major league soccer": 253,
    "nwsl (usa femenil)": 254,
    "nwsl": 254,
    "leagues cup": 848,
    "concacaf champions cup": 16,
    "concacaf": 16,
    "la liga (españa)": 140,
    "la liga": 140,
    "laliga": 140,
    "españa": 140,
    "copa del rey (españa)": 143,
    "copa del rey": 143,
    "liga f (españa femenil)": 142,
    "serie a (italia)": 135,
    "serie a": 135,
    "italia": 135,
    "coppa italia": 137,
    "bundesliga (alemania)": 78,
    "bundesliga": 78,
    "alemania": 78,
    "dfb pokal (alemania)": 81,
    "dfb pokal": 81,
    "ligue 1 (francia)": 61,
    "ligue 1": 61,
    "francia": 61,
    "coupe de france": 66,
    "liga argentina": 128,
    "argentina": 128,
    "copa argentina": 130,
    "brasileirão": 71,
    "brasil": 71,
    "copa do brasil": 73,
    "copa libertadores": 13,
    "libertadores": 13,
    "copa sudamericana": 11,
    "sudamericana": 11,
    "primeira liga (portugal)": 94,
    "primeira liga": 94,
    "portugal": 94,
    "taça de portugal": 96,
    "jupiler pro league (bélgica)": 144,
    "jupiler pro league": 144,
    "belgica": 144,
    "eredivisie (holanda)": 88,
    "eredivisie": 88,
    "champions league": 2,
    "champions": 2,
    "champions league femenil": 5,
    "europa league": 3
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
    "manchester united": "Manchester United",
    "man utd": "Manchester United",
    "milan": "AC Milan",
    "ac milan": "AC Milan",
    "dortmund": "Borussia Dortmund",
    "borussia dortmund": "Borussia Dortmund",
    "roma": "AS Roma",
    "as roma": "AS Roma",
    "arsenal": "Arsenal",
    "manchester city": "Manchester City",
    "man city": "Manchester City",
    "chelsea": "Chelsea",
    "liverpool": "Liverpool",
    "tottenham": "Tottenham",
    "alaves": "Alaves",
    "getafe": "Getafe",
    "sevilla": "Sevilla",
    "rayo vallecano": "Rayo Vallecano",
    "utrecht": "FC Utrecht",
    "az alkmaar": "AZ Alkmaar",
    "cd nacional": "Nacional",
    "estoril": "Estoril",
    "fluminense": "Fluminense",
    "palmeiras": "Palmeiras",
    "montreal": "CF Montreal",
    "cf montreal": "CF Montreal",
    "dc united": "DC United",
    "austin": "Austin FC",
    "austin fc": "Austin FC",
    "sarmiento": "Sarmiento Junin",
    "huracan": "Huracan",
    "kv mechelen": "Mechelen",
    "st lieja": "Standard Liege",
    "america": "Club America",
    "tigres": "Tigres UANL",
    "chivas": "Guadalajara",
    "pumas": "UNAM Pumas",
    "cruz azul": "Cruz Azul",
    "atlas": "Atlas",
    "tijuana": "Club Tijuana",
    "juarez": "FC Juarez",
    "fc juarez": "FC Juarez",
    "pachuca": "CF Pachuca",
    "cf pachuca": "CF Pachuca",
    "colo colo": "Colo Colo",
    "u de chile": "Universidad de Chile",
    "univ de chile": "Universidad de Chile",
    "u catolica": "Universidad Catolica",
    "univ catolica": "Universidad Catolica",
    "union espanola": "Union Espanola",
    "audax": "Audax Italiano",
    "audax italiano": "Audax Italiano",
    "cobreloa": "Cobreloa",
    "coquimbo": "Coquimbo Unido",
    "huachipato": "Huachipato",
    "palestino": "Palestino",
    "everton de vina": "Everton de Vina",
    "ohiggins": "O'Higgins",
    "cobresal": "Cobresal",
    "deportes iquique": "Deportes Iquique",
    "nublense": "Nublense"
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
        l_clean = str(liga_str).lower().strip()
        return MAPA_LIGAS_ID.get(l_clean, None)

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
        if not nombre_equipo or not nombre_equipo.strip():
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
                            if (t_name == raw_clean or 
                                t_name == query_search.lower() or 
                                raw_clean in t_name or 
                                query_search.lower() in t_name or
                                t_name in raw_clean):
                                return {
                                    "id": int(t.get("id")),
                                    "nombre": t.get("name"),
                                    "pais": str(liga_nombre).upper() if liga_nombre else t.get("country", "")
                                }
                except Exception:
                    pass

        search_terms = [query_search]
        if femenil_mode:
            search_terms = [f"{query_search} W", f"{query_search} Women", f"{query_search} Femenil", query_search]

        for q in search_terms:
            try:
                url = f"{cls.BASE_URL}/teams"
                res = requests.get(url, headers=cls._get_headers(), params={"search": q}, timeout=8)
                data = res.json().get("response", [])
                if not data: continue

                candidatos = []
                for item in data:
                    t = item.get("team", {})
                    pais = str(t.get("country", "")).lower()
                    t_name = str(t.get("name", "")).lower()
                    score = 0

                    if pais in ["mexico", "england", "spain", "italy", "germany", "france", "argentina", "brazil", "portugal", "netherlands", "belgium", "usa", "canada", "chile"]:
                        score += 300
                    elif "national" in pais or not pais: score += 50
                    else: score -= 100

                    if t_name == raw_clean or t_name == q.lower(): score += 250
                    elif raw_clean in t_name or q.lower() in t_name: score += 120
                    else: score += 20

                    es_equipo_w = any(kw in t_name for kw in ["women", "femenil", "feminino", "feminina", " w", "-w", "(w)"]) or t_name.endswith(" w")

                    if femenil_mode:
                        if es_equipo_w: score += 400
                        else: score -= 200
                    else:
                        if es_equipo_w: score -= 600

                    if any(w in t_name for w in ["bold", " ii", " b", "youth", "sub", "u23", "u21", "u20", "u19", "reserve", "academy"]):
                        score -= 400
                    if "-la-" in t_name or "-le-" in t_name or "-en-" in t_name:
                        score -= 350

                    candidatos.append((score, t))

                candidatos.sort(key=lambda x: x[0], reverse=True)
                if candidatos and candidatos[0][0] > -200:
                    best = candidatos[0][1]
                    pais_final = best.get("country", "")
                    if str(best.get("name", "")).lower() in ["cf montreal", "toronto fc", "vancouver whitecaps"]:
                        pais_final = "MLS"

                    return {
                        "id": int(best.get("id")),
                        "nombre": best.get("name"),
                        "pais": pais_final
                    }
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
                        
                        encontro_grupo = False
                        for group_list in standings_raw:
                            if not group_list: continue
                            team_ids_in_group = [pos.get("team", {}).get("id") for pos in group_list]
                            if team_id in team_ids_in_group:
                                group_title = group_list[0].get("group", "")
                                display_name = f"{base_league_name} ({group_title})" if group_title and group_title.lower() not in base_league_name.lower() else base_league_name
                                
                                df_list = []
                                for pos in group_list:
                                    df_list.append({
                                        "Pos": pos.get("rank"),
                                        "Equipo": pos.get("team", {}).get("name"),
                                        "PTS": pos.get("points"),
                                        "PJ": pos.get("all", {}).get("played"),
                                        "PG": pos.get("all", {}).get("win"),
                                        "PE": pos.get("all", {}).get("draw"),
                                        "PP": pos.get("all", {}).get("lose"),
                                        "GF": pos.get("all", {}).get("goals", {}).get("for"),
                                        "GC": pos.get("all", {}).get("goals", {}).get("against"),
                                        "DIF": pos.get("goalsDiff")
                                    })
                                tablas_equipo.append({
                                    "league_id": f"{lid}_{group_title}",
                                    "raw_league_id": lid,
                                    "league_name": display_name,
                                    "season": season,
                                    "df": pd.DataFrame(df_list)
                                })
                                encontro_grupo = True
                                break
                        
                        if not encontro_grupo and len(standings_raw) > 0 and len(standings_raw[0]) > 0:
                            first_group = standings_raw[0]
                            group_title = first_group[0].get("group", "")
                            display_name = f"{base_league_name} ({group_title})" if group_title and group_title.lower() not in base_league_name.lower() else base_league_name
                            
                            df_list = []
                            for pos in first_group:
                                df_list.append({
                                    "Pos": pos.get("rank"),
                                    "Equipo": pos.get("team", {}).get("name"),
                                    "PTS": pos.get("points"),
                                    "PJ": pos.get("all", {}).get("played"),
                                    "PG": pos.get("all", {}).get("win"),
                                    "PE": pos.get("all", {}).get("draw"),
                                    "PP": pos.get("all", {}).get("lose"),
                                    "GF": pos.get("all", {}).get("goals", {}).get("for"),
                                    "GC": pos.get("all", {}).get("goals", {}).get("against"),
                                    "DIF": pos.get("goalsDiff")
                                })
                            tablas_equipo.append({
                                "league_id": f"{lid}_{group_title}",
                                "raw_league_id": lid,
                                "league_name": display_name,
                                "season": season,
                                "df": pd.DataFrame(df_list)
                            })

                        if tablas_equipo: break
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
                    pj_l = fix.get("played", {}).get("home", 0)
                    pj_v = fix.get("played", {}).get("away", 0)
                    if pj_l > 0 or pj_v > 0:
                        goals = data.get("goals", {})
                        return {
                            "season": season,
                            "local": {
                                "pj": pj_l, "pg": fix.get("wins", {}).get("home", 0), "pe": fix.get("draws", {}).get("home", 0), "pp": fix.get("loses", {}).get("home", 0),
                                "gf": goals.get("for", {}).get("total", {}).get("home", 0), "gc": goals.get("against", {}).get("total", {}).get("home", 0),
                                "avg_gf": float(goals.get("for", {}).get("average", {}).get("home", 0.0) or 0.0),
                                "avg_gc": float(goals.get("against", {}).get("average", {}).get("home", 0.0) or 0.0)
                            },
                            "visita": {
                                "pj": pj_v, "pg": fix.get("wins", {}).get("away", 0), "pe": fix.get("draws", {}).get("away", 0), "pp": fix.get("loses", {}).get("away", 0),
                                "gf": goals.get("for", {}).get("total", {}).get("away", 0), "gc": goals.get("against", {}).get("total", {}).get("away", 0),
                                "avg_gf": float(goals.get("for", {}).get("average", {}).get("away", 0.0) or 0.0),
                                "avg_gc": float(goals.get("against", {}).get("average", {}).get("away", 0.0) or 0.0)
                            }
                        }
            except Exception:
                pass
        return {}

# ------------------------------------------------------------------------------
# 3. FUNCIONES DE RESALTADO Y COMPARACIÓN DE EQUIPOS
# ------------------------------------------------------------------------------
def limpiar_nombre_equipo(nom):
    if not nom: return ""
    s = str(nom).lower().replace(".", "").strip()
    stops = ["fc", "cf", "club", "cd", "ca", "sd", "ud", "kv", "as", "ac", "u.n.a.m.", "unam", "c.a.", "g.d.", "c.d.", "w", "women", "femenil"]
    w = [p for p in s.split() if p not in stops]
    return " ".join(w) if w else s

def es_mismo_equipo(nom1, nom2):
    if not nom1 or not nom2: return False
    c1 = limpiar_nombre_equipo(nom1)
    c2 = limpiar_nombre_equipo(nom2)
    if c1 == c2: return True
    if len(c1) >= 3 and len(c2) >= 3:
        if c1 in c2 or c2 in c1: return True
    return False

def resaltar_participantes(df_tab, eq_l_name, eq_v_name):
    def color_row(row):
        eq = row.get("Equipo", "")
        if es_mismo_equipo(eq, eq_l_name) or es_mismo_equipo(eq, eq_v_name):
            return ['background-color: #ffcccc; color: #990000; font-weight: bold'] * len(row)
        return [''] * len(row)
    return df_tab.style.apply(color_row, axis=1)

def calcular_xg_multitorneo_real(df_f1, df_f2):
    if not df_f1.empty and "gf" in df_f1.columns:
        gf_l = df_f1["gf"].mean()
        gc_l = df_f1["gc"].mean()
    else:
        gf_l, gc_l = 1.1, 1.2

    if not df_f2.empty and "gf" in df_f2.columns:
        gf_v = df_f2["gf"].mean()
        gc_v = df_f2["gc"].mean()
    else:
        gf_v, gc_v = 1.0, 1.1

    lambda_l = max(0.6, round((gf_l + gc_v) / 2.0, 2))
    mu_v = max(0.6, round((gf_v + gc_l) / 2.0, 2))

    return lambda_l, mu_v

def detectar_datos_duros(info_l, info_v, df_f1, df_f2, df_h2h):
    insights = []

    if not df_f1.empty and "Res" in df_f1.columns:
        res_l = df_f1["Res"].tolist()
        sin_ganar_l_cons = 0
        for r in res_l:
            if "G" not in r: sin_ganar_l_cons += 1
            else: break
        if sin_ganar_l_cons >= 3:
            insights.append(f"⚠️ **RACHA CONSECUTIVA ({info_l['nombre']})**: Lleva **{sin_ganar_l_cons} partidos seguidos sin ganar** actualmente.")

    if not df_f2.empty and "Res" in df_f2.columns:
        res_v = df_f2["Res"].tolist()
        sin_ganar_v_cons = 0
        for r in res_v:
            if "G" not in r: sin_ganar_v_cons += 1
            else: break
        if sin_ganar_v_cons >= 3:
            insights.append(f"⚠️ **RACHA CONSECUTIVA ({info_v['nombre']})**: Lleva **{sin_ganar_v_cons} partidos seguidos sin ganar** actualmente.")

    if not df_h2h.empty:
        partidos_h2h = df_h2h.to_dict('records')
        sin_ganar_h2h_l = 0
        for p in partidos_h2h:
            m_loc = p.get("Local", "")
            m_res = p.get("Resultado", "")
            try: gh, ga = map(int, m_res.split("-"))
            except: continue
            
            eq_l_was_home = (p.get("home_id") == info_l["id"]) or es_mismo_equipo(info_l['nombre'], m_loc)
            eq_l_won = (gh > ga) if eq_l_was_home else (ga > gh)
            if eq_l_won: break
            else: sin_ganar_h2h_l += 1

        if sin_ganar_h2h_l >= 4:
            insights.append(f"📊 **DATO DURO H2H**: **{info_l['nombre']}** suma **{sin_ganar_h2h_l} partidos sin ganarle a {info_v['nombre']}**.")

    return insights

# ------------------------------------------------------------------------------
# 4. FÓRMULAS DE PROBABILIDAD, SMART MONEY Y CORRECCIÓN DIXON-COLES
# ------------------------------------------------------------------------------
def limpiar_y_convertir_momio(val):
    if val is None: return None
    val_str = str(val).replace("+", "").replace("$", "").replace(",", "").strip()
    if not val_str or val_str == "0" or val_str == "-": return None
    try: return float(val_str)
    except Exception: return None

def calcular_probabilidad_excel(momio_clean):
    if momio_clean is None or momio_clean == 0: return 0.0
    if momio_clean > 0:
        return (100.0 / (momio_clean + 100.0)) * 100.0
    else:
        return (abs(momio_clean) / (abs(momio_clean) + 100.0)) * 100.0

def dixon_coles_tau(x: int, y: int, lambda_l: float, mu_v: float, rho: float = -0.13) -> float:
    if x == 0 and y == 0:
        return 1.0 - (lambda_l * mu_v * rho)
    elif x == 1 and y == 0:
        return 1.0 + (mu_v * rho)
    elif x == 0 and y == 1:
        return 1.0 + (lambda_l * rho)
    elif x == 1 and y == 1:
        return 1.0 - rho
    else:
        return 1.0

def calcular_poisson_dixon_coles(lambda_l: float, mu_v: float):
    prob_l, prob_e, prob_v = 0.0, 0.0, 0.0
    marcadores = []
    
    for x in range(6):
        for y in range(6):
            p_x = (math.pow(lambda_l, x) * math.exp(-lambda_l)) / math.factorial(x) if lambda_l > 0 else 0
            p_y = (math.pow(mu_v, y) * math.exp(-mu_v)) / math.factorial(y) if mu_v > 0 else 0
            
            tau = dixon_coles_tau(x, y, lambda_l, mu_v)
            p_final = max(0.0, p_x * p_y * tau)
            
            if x > y: prob_l += p_final
            elif x == y: prob_e += p_final
            else: prob_v += p_final
                
            marcadores.append({"Marcador": f"{x} - {y}", "Probabilidad (%)": round(p_final * 100.0, 1)})
            
    marcadores.sort(key=lambda k: k["Probabilidad (%)"], reverse=True)
    
    suma_total = prob_l + prob_e + prob_v
    if suma_total > 0:
        pl_pct = round((prob_l / suma_total) * 100.0, 2)
        pe_pct = round((prob_e / suma_total) * 100.0, 2)
        pv_pct = round((prob_v / suma_total) * 100.0, 2)
    else:
        pl_pct, pe_pct, pv_pct = 0.0, 0.0, 0.0
        
    return pl_pct, pe_pct, pv_pct, marcadores[:5]

def procesar_fila_independiente(row):
    num = row.get("#", 0)
    liga = str(row.get("Liga", "") or "").strip()
    loc = str(row.get("Local", "") or "").strip()
    vis = str(row.get("Visita", "") or "").strip()

    ml_raw = row.get("Momio Local")
    me_raw = row.get("Momio Empate")
    mv_raw = row.get("Momio Visitante")

    ov_raw = row.get("Over 2.5")
    un_raw = row.get("Under 2.5")

    o_l_raw = row.get("Apertura Local")
    o_e_raw = row.get("Apertura Empate")
    o_v_raw = row.get("Apertura Visitante")

    ml_clean = limpiar_y_convertir_momio(ml_raw)
    me_clean = limpiar_y_convertir_momio(me_raw)
    mv_clean = limpiar_y_convertir_momio(mv_raw)

    ov_clean = limpiar_y_convertir_momio(ov_raw)
    un_clean = limpiar_y_convertir_momio(un_raw)

    o_l_clean = limpiar_y_convertir_momio(o_l_raw)
    o_e_clean = limpiar_y_convertir_momio(o_e_raw)
    o_v_clean = limpiar_y_convertir_momio(o_v_raw)

    if not loc and not vis:
        return {
            "#": num, "Liga": liga, "Partido": f"Partido #{num}",
            "Momio Local": "", "Momio Empate": "", "Momio Visitante": "",
            "Over 2.5": "", "Under 2.5": "",
            "Prob. Local (%)": "-", "Prob. Empate (%)": "-", "Prob. Visitante (%)": "-",
            "Favorito": "-", "Dif. Probabilidad (%)": "-", "Smart Money": "-", "PRO Line Alert": "-", "Clasificación Partido": "EN ESPERA"
        }

    if ml_clean is None or me_clean is None or mv_clean is None:
        return {
            "#": num, "Liga": liga, "Partido": f"{loc} vs {vis}" if (loc and vis) else (loc if loc else vis),
            "Momio Local": ml_raw if ml_raw else "", "Momio Empate": me_raw if me_raw else "",
            "Momio Visitante": mv_raw if mv_raw else "",
            "Over 2.5": ov_raw if ov_raw else "", "Under 2.5": un_raw if un_raw else "",
            "Prob. Local (%)": "-", "Prob. Empate (%)": "-", "Prob. Visitante (%)": "-",
            "Favorito": "-", "Dif. Probabilidad (%)": "-", "Smart Money": "-", "PRO Line Alert": "-", "Clasificación Partido": "EN ESPERA"
        }

    pl = calcular_probabilidad_excel(ml_clean)
    pe = calcular_probabilidad_excel(me_clean)
    pv = calcular_probabilidad_excel(mv_clean)
    suma = pl + pe + pv

    if suma > 0:
        pl_n = round((pl / suma) * 100.0, 2)
        pe_n = round((pe / suma) * 100.0, 2)
        pv_n = round((pv / suma) * 100.0, 2)
        
        pl_str = f"{pl_n:.2f}%"
        pe_str = f"{pe_n:.2f}%"
        pv_str = f"{pv_n:.2f}%"
    else:
        return {
            "#": num, "Liga": liga, "Partido": f"{loc} vs {vis}",
            "Momio Local": ml_raw or "", "Momio Empate": me_raw or "", "Momio Visitante": mv_raw or "",
            "Over 2.5": ov_raw or "", "Under 2.5": un_raw or "",
            "Prob. Local (%)": "-", "Prob. Empate (%)": "-", "Prob. Visitante (%)": "-",
            "Favorito": "-", "Dif. Probabilidad (%)": "-", "Smart Money": "-", "PRO Line Alert": "-", "Clasificación Partido": "EN ESPERA"
        }

    smart_money_str = "Estable"
    if o_l_clean is not None and o_e_clean is not None and o_v_clean is not None:
        p_ol = calcular_probabilidad_excel(o_l_clean)
        p_oe = calcular_probabilidad_excel(o_e_clean)
        p_ov = calcular_probabilidad_excel(o_v_clean)
        sum_o = p_ol + p_oe + p_ov
        if sum_o > 0:
            p_ol_n = (p_ol / sum_o) * 100.0
            p_oe_n = (p_oe / sum_o) * 100.0
            p_ov_n = (p_ov / sum_o) * 100.0
            
            diff_l = pl_n - p_ol_n
            diff_e = pe_n - p_oe_n
            diff_v = pv_n - p_ov_n

            if diff_l >= 3.5:
                smart_money_str = f"🔥 Dinero al Local (+{diff_l:.1f}%)"
            elif diff_v >= 3.5:
                smart_money_str = f"🔥 Dinero a Visita (+{diff_v:.1f}%)"
            elif diff_e >= 3.0:
                smart_money_str = f"🟡 Dinero al Empate (+{diff_e:.1f}%)"

    pro_line_alert = "Estable"
    if o_l_clean is not None and ml_clean is not None:
        if o_l_clean > -140 and ml_clean <= -140:
            pro_line_alert = "🔥 ALERTA: Fijo Activado (Local <= -140)"
        elif o_l_clean <= -140 and ml_clean > -140:
            pro_line_alert = "⚠️ ALERTA: Fuga Institucional (Local > -140)"

    if o_v_clean is not None and mv_clean is not None:
        if o_v_clean > -140 and mv_clean <= -140:
            pro_line_alert = "🔥 ALERTA: Fijo Activado (Visita <= -140)"
        elif o_v_clean <= -140 and mv_clean > -140:
            pro_line_alert = "⚠️ ALERTA: Fuga Institucional (Visita > -140)"

    fav = "Local" if pl_n > pv_n else ("Visitante" if pv_n > pl_n else "Empate")
    dif = round(abs(pl_n - pv_n), 2)
    dif_str = f"{dif:.2f}%"

    if dif >= 35.0: clasif = "FAVORITO FUERTE"
    elif dif < 10.0 and pe_n >= 29.0: clasif = "ZONA DE EMPATE"
    elif 10.0 <= dif < 35.0: clasif = "FAVORITO MEDIO"
    else: clasif = "PARTIDO TRAMPA"

    return {
        "#": num, "Liga": liga, "Partido": f"{loc} vs {vis}",
        "Momio Local": str(ml_raw or ""), "Momio Empate": str(me_raw or ""), "Momio Visitante": str(mv_raw or ""),
        "Over 2.5": str(ov_raw or ""), "Under 2.5": str(un_raw or ""),
        "Prob. Local (%)": pl_str, "Prob. Empate (%)": pe_str, "Prob. Visitante (%)": pv_str,
        "Favorito": fav, "Dif. Probabilidad (%)": dif_str, "Smart Money": smart_money_str, 
        "PRO Line Alert": pro_line_alert, "Clasificación Partido": clasif
    }

# ------------------------------------------------------------------------------
# LÓGICA DE INTERFAZ Y MODULOS DE STREAMLIT
# ------------------------------------------------------------------------------

# (Aquí continúa la lógica principal de visualización de los módulos ya integrados)
