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
# 1. ARCHIVOS DE DISCO Y LISTA COMPLETA DE LIGAS, COPAS Y AMISTOSOS
# ------------------------------------------------------------------------------
ARCHIVO_DISCO = "progol_captura_v7.json"
ARCHIVO_CACHE_API = "progol_bigdata_cache.json"

OPCIONES_LIGAS = [
    "Liga MX",
    "Liga MX Femenil",
    "MLS",
    "NWSL (USA Femenil)",
    "Liga Chilena (Primera División)",
    "Copa Chile",
    "Supercopa de Chile",
    "Amistoso / Club Friendlies",
    "Amistoso Internacional (Selecciones)",
    "Premier League",
    "FA Cup (Inglaterra)",
    "EFL Cup / Carabao Cup (Inglaterra)",
    "Championship (Inglaterra 2da)",
    "Community Shield (Inglaterra)",
    "La Liga (España)",
    "Copa del Rey (España)",
    "Liga F (España Femenil)",
    "Serie A (Italia)",
    "Coppa Italia",
    "Bundesliga (Alemania)",
    "DFB Pokal (Alemania)",
    "Ligue 1 (Francia)",
    "Coupe de France",
    "Liga Argentina",
    "Copa Argentina",
    "Primeira Liga (Portugal)",
    "Taça de Portugal",
    "Jupiler Pro League (Bélgica)",
    "Champions League",
    "Champions League Femenil",
    "Europa League",
    "Leagues Cup",
    "Concacaf Champions Cup",
    "Copa Libertadores",
    "Copa Sudamericana",
    "Brasileirão",
    "Copa do Brasil",
    "Eredivisie (Holanda)",
    "Otra / Automático"
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

    @classmethod
    def obtener_ultimos_partidos_reales_multitorneo(cls, team_id: int):
        try:
            url = f"{cls.BASE_URL}/fixtures"
            res = requests.get(url, headers=cls._get_headers(), params={"team": team_id, "last": 15}, timeout=8)
            data = res.json().get("response", [])
            partidos = []
            for item in data:
                fix = item.get("fixture", {})
                status_short = fix.get("status", {}).get("short", "")
                if status_short not in ["FT", "AET", "PEN"]: continue

                league = item.get("league", {})
                teams = item.get("teams", {})
                goals = item.get("goals", {})
                
                home_id = teams.get("home", {}).get("id")
                home_name = teams.get("home", {}).get("name")
                away_name = teams.get("away", {}).get("name")
                
                gh = goals.get("home", 0) if goals.get("home") is not None else 0
                ga = goals.get("away", 0) if goals.get("away") is not None else 0
                
                is_home = (home_id == team_id)
                if is_home:
                    res_letra = "🟩 G" if gh > ga else ("🟥 P" if gh < ga else "🟨 E")
                    rival = away_name
                    gf_team, gc_team = gh, ga
                else:
                    res_letra = "🟩 G" if ga > gh else ("🟥 P" if ga < gh else "🟨 E")
                    rival = home_name
                    gf_team, gc_team = ga, gh

                nota_pen = " (P)" if status_short == "PEN" else ""
                t_raw = league.get("name", "Oficial")
                t_clean = t_raw.replace("CONCACAF Champions Cup", "CONCACAF").replace("Friendlies Clubs", "Amistoso")
                rival_short = (rival[:11] + "…") if len(rival) > 12 else rival

                partidos.append({
                    "Fecha": fix.get("date", "").split("T")[0][5:],
                    "Res": res_letra,
                    "Rival": rival_short,
                    "Score": f"{gh}-{ga}{nota_pen}",
                    "Torneo": t_clean,
                    "gf": gf_team,
                    "gc": gc_team
                })
                if len(partidos) == 10: break

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
                
                h_id = teams.get("home", {}).get("id")
                a_id = teams.get("away", {}).get("id")

                partidos.append({
                    "Fecha": fix.get("date", "").split("T")[0],
                    "Torneo": item.get("league", {}).get("name", ""),
                    "Local": teams.get("home", {}).get("name", ""),
                    "home_id": int(h_id) if h_id is not None else None,
                    "Resultado": f"{goals.get('home', 0)} - {goals.get('away', 0)}",
                    "Visita": teams.get("away", {}).get("name", ""),
                    "away_id": int(a_id) if a_id is not None else None
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
                bajas.append({
                    "Jugador": player.get("name"),
                    "Tipo": player.get("type"),
                    "Motivo": player.get("reason")
                })
            return pd.DataFrame(bajas)
        except Exception:
            return pd.DataFrame()

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

def procesar_tabla_completa(datos_raw):
    return pd.DataFrame([procesar_fila_independiente(r) for r in datos_raw])

# ------------------------------------------------------------------------------
# 5. ENCABEZADO Y BOTONERA
# ------------------------------------------------------------------------------
st.title("⚽ Centro de Mando Progol v4.0 Ultra")
st.caption("Fórmulas Unificadas + Búsqueda Blindada por Liga/Copas/Amistosos + Interfaz Adaptable.")

df_analisis = procesar_tabla_completa(st.session_state["tabla_progol"])
partidos_validos = [p for p in df_analisis[df_analisis["Clasificación Partido"] != "EN ESPERA"]["Partido"].tolist() if p != "-"]

if partidos_validos:
    if "selectbox_tab2" not in st.session_state or st.session_state["selectbox_tab2"] not in partidos_validos:
        st.session_state["selectbox_tab2"] = partidos_validos[0]
    if "selectbox_tab5" not in st.session_state or st.session_state["selectbox_tab5"] not in partidos_validos:
        st.session_state["selectbox_tab5"] = partidos_validos[0]

def sync_tab2_to_tab5():
    st.session_state["selectbox_tab5"] = st.session_state["selectbox_tab2"]

def sync_tab5_to_tab2():
    st.session_state["selectbox_tab2"] = st.session_state["selectbox_tab5"]

modulos = [
    ("📊 1. ANÁLISIS 1 (Excel)", "📊 1. ANÁLISIS 1 (Excel)"),
    ("🌐 2. Big Data API-Sports (Live)", "🌐 2. Big Data API-Sports (Live)"),
    ("🤝 3. Detector de Empates", "🤝 3. Detector de Empates"),
    ("🔥 4. Detector de Trampas", "🔥 4. Detector de Trampas"),
    ("🎯 5. Método Poisson & Dixon-Coles", "🎯 5. Método Poisson & Dixon-Coles"),
    ("🎫 6. Quiniela Múltiple (7/8 Dobles)", "🎫 6. Quiniela Múltiple (7/8 Dobles)"),
    ("🎰 7. Matriz Reducida", "🎰 7. Matriz Reducida"),
    ("📋 8. CAPTURA Y EDICIÓN", "📋 8. CAPTURA Y EDICIÓN"),
    ("🔥 9. Generador Bolsa Grande (Acumulado)", "🔥 9. Generador Bolsa Grande (Acumulado)"),
]

fila1 = st.columns(4)
for i in range(4):
    label, val = modulos[i]
    is_active = (st.session_state["menu_activo"] == val)
    if fila1[i].button(label, type="primary" if is_active else "secondary", key=f"btn_nav_{i}", use_container_width=True):
        st.session_state["menu_activo"] = val
        st.rerun()

fila2 = st.columns(4)
for j in range(4):
    label, val = modulos[4 + j]
    is_active = (st.session_state["menu_activo"] == val)
    if fila2[j].button(label, type="primary" if is_active else "secondary", key=f"btn_nav_{4+j}", use_container_width=True):
        st.session_state["menu_activo"] = val
        st.rerun()
col_bolsa = st.columns(1)
if col_bolsa[0].button(modulos[8][0], type="primary" if st.session_state["menu_activo"] == modulos[8][1] else "secondary", key="btn_nav_8", use_container_width=True):
    st.session_state["menu_activo"] = modulos[8][1]
    st.rerun()

st.divider()

# ------------------------------------------------------------------------------
# 6. CONTENIDO MODULAR CONDICIONAL
# ------------------------------------------------------------------------------

# MÓDULO 1: ANÁLISIS 1 (EXCEL)
if st.session_state["menu_activo"] == "📊 1. ANÁLISIS 1 (Excel)":
    st.subheader("Tabla Maestra de Análisis Cuantitativo (14 Partidos)")
    st.dataframe(df_analisis, width="stretch", height=540)

# MÓDULO 2: BIG DATA API-SPORTS LIVE
elif st.session_state["menu_activo"] == "🌐 2. Big Data API-Sports (Live)":
    st.subheader("🌐 Extracción Multitorneo en Vivo desde API-Sports Ultra")
    
    if partidos_validos:
        partido_sel = st.selectbox(
            "Selecciona partido a consultar en la API:",
            partidos_validos,
            key="selectbox_tab2",
            on_change=sync_tab2_to_tab5
        )

        if partido_sel:
            row_p = df_analisis[df_analisis["Partido"] == partido_sel].iloc[0]
            num_p = int(row_p["#"])
            p_orig = st.session_state["tabla_progol"][num_p - 1]
            eq_l, eq_v = p_orig.get("Local"), p_orig.get("Visita")
            liga_contexto = p_orig.get("Liga", "Liga MX")

            if st.button(f"🚀 Descargar Big Data ({liga_contexto}) para {eq_l} vs {eq_v}", type="primary"):
                with st.spinner(f"Consultando servidores oficiales de API-Sports para {liga_contexto}..."):
                    info_l = MotorAPISportsUltra.buscar_equipo_dinamico(eq_l, liga_contexto)
                    info_v = MotorAPISportsUltra.buscar_equipo_dinamico(eq_v, liga_contexto)

                    if info_l and info_v:
                        st.success(f"✅ Equipos Localizados en API-Sports: **{info_l['nombre']} ({info_l['pais']} / ID: {info_l['id']})** vs **{info_v['nombre']} ({info_v['pais']} / ID: {info_v['id']})**")
                        
                        df_f1 = MotorAPISportsUltra.obtener_ultimos_partidos_reales_multitorneo(info_l["id"])
                        df_f2 = MotorAPISportsUltra.obtener_ultimos_partidos_reales_multitorneo(info_v["id"])
                        df_h2h = MotorAPISportsUltra.obtener_h2h(info_l["id"], info_v["id"])

                        lambda_l, mu_v = calcular_xg_multitorneo_real(df_f1, df_f2)

                        st.session_state["api_cache_xg"][partido_sel] = {
                            "xg_l": lambda_l, "xg_v": mu_v,
                            "name_l": info_l['nombre'], "name_v": info_v['nombre'],
                            "id_l": info_l["id"], "id_v": info_v["id"]
                        }
                        guardar_cache_api(st.session_state["api_cache_xg"])

                        st.divider()
                        st.subheader("📌 Datos Duros y Rachas Clave Detectadas")
                        datos_duros = detectar_datos_duros(info_l, info_v, df_f1, df_f2, df_h2h)
                        if datos_duros:
                            for dd in datos_duros: st.warning(dd)
                        else:
                            st.info("🟢 **RANGOS NORMALES:** No se detectan rachas consecutivas activas o anomalías históricas destacables.")

                        # 1. TABLAS DE POSICIONES
                        st.divider()
                        tablas_l = MotorAPISportsUltra.obtener_todas_tablas_posiciones(info_l["id"], liga_contexto)
                        tablas_v = MotorAPISportsUltra.obtener_todas_tablas_posiciones(info_v["id"], liga_contexto)

                        ids_l = {t["league_id"]: t for t in tablas_l}
                        ids_v = {t["league_id"]: t for t in tablas_v}
                        shared_leagues = set(ids_l.keys()).intersection(set(ids_v.keys()))

                        first_league_id_l = tablas_l[0].get("raw_league_id", 262) if tablas_l else None
                        first_league_id_v = tablas_v[0].get("raw_league_id", 262) if tablas_v else None

                        if MotorAPISportsUltra.es_amistoso(liga_contexto):
                            st.subheader("🏆 1. Tablas Oficiales de Ligas de Origen (Formato de Partido Amistoso)")
                            col_t1, col_t2 = st.columns(2)
                            with col_t1:
                                if tablas_l:
                                    for t in tablas_l:
                                        st.write(f"**🏠 {info_l['nombre']} - {t['league_name']} ({t['season']})**")
                                        styled_df_l = resaltar_participantes(t["df"], info_l["nombre"], info_v["nombre"])
                                        st.dataframe(styled_df_l, width="stretch")
                                else: st.caption("Sin tabla oficial de liga.")
                            with col_t2:
                                if tablas_v:
                                    for t in tablas_v:
                                        st.write(f"**✈️ {info_v['nombre']} - {t['league_name']} ({t['season']})**")
                                        styled_df_v = resaltar_participantes(t["df"], info_l["nombre"], info_v["nombre"])
                                        st.dataframe(styled_df_v, width="stretch")
                                else: st.caption("Sin tabla oficial de liga.")
                        elif shared_leagues:
                            st.subheader("🏆 1. Tabla Oficial de la Conferencia / Torneo Compartido")
                            for s_id in shared_leagues:
                                t_info = ids_l[s_id]
                                st.write(f"**Competencia:** {t_info['league_name']} (Temporada {t_info['season']})")
                                styled_df = resaltar_participantes(t_info["df"], info_l["nombre"], info_v["nombre"])
                                st.dataframe(styled_df, width="stretch")
                        else:
                            st.subheader("🏆 1. Tablas Generales de Posiciones por Conferencia o Torneo")
                            col_t1, col_t2 = st.columns(2)
                            with col_t1:
                                if tablas_l:
                                    for t in tablas_l:
                                        st.write(f"**🏠 {info_l['nombre']} - {t['league_name']} ({t['season']})**")
                                        styled_df_l = resaltar_participantes(t["df"], info_l["nombre"], info_v["nombre"])
                                        st.dataframe(styled_df_l, width="stretch")
                                else: st.caption(f"Sin tabla oficial registrada para {info_l['nombre']}.")
                            with col_t2:
                                if tablas_v:
                                    for t in tablas_v:
                                        st.write(f"**✈️ {info_v['nombre']} - {t['league_name']} ({t['season']})**")
                                        styled_df_v = resaltar_participantes(t["df"], info_l["nombre"], info_v["nombre"])
                                        st.dataframe(styled_df_v, width="stretch")
                                else: st.caption(f"Sin tabla oficial registrada para {info_v['nombre']}.")

                        # 2. MÉTRICAS DIVIDIDAS
                        st.divider()
                        st.subheader("📊 2. Rendimiento Dividido (Local Puro vs Visita Puro)")
                        st.caption("📌 Nota: Muestra el desempeño exclusivo en sus respectivos torneos oficiales vigentes.")
                        stats_l = MotorAPISportsUltra.obtener_metricas_divididas(info_l["id"], first_league_id_l)
                        stats_v = MotorAPISportsUltra.obtener_metricas_divididas(info_v["id"], first_league_id_v)

                        pj_v = stats_v.get("visita", {}).get("pj", 0)
                        pg_v = stats_v.get("visita", {}).get("pg", 0)

                        data_metrics = [
                            {
                                "Condición": f"🏠 {info_l['nombre']} (Local Puro)",
                                "PJ": stats_l.get("local", {}).get("pj", 0), "PG": stats_l.get("local", {}).get("pg", 0),
                                "PE": stats_l.get("local", {}).get("pe", 0), "PP": stats_l.get("local", {}).get("pp", 0),
                                "Goles Favor (GF)": stats_l.get("local", {}).get("gf", 0), "Goles Contra (GC)": stats_l.get("local", {}).get("gc", 0),
                                "Prom. GF/Partido": stats_l.get("local", {}).get("avg_gf", 0.0), "Prom. GC/Partido": stats_l.get("local", {}).get("avg_gc", 0.0)
                            },
                            {
                                "Condición": f"✈️ {info_v['nombre']} (Visita Puro)",
                                "PJ": pj_v, "PG": pg_v,
                                "PE": stats_v.get("visita", {}).get("pe", 0), "PP": stats_v.get("visita", {}).get("pp", 0),
                                "Goles Favor (GF)": stats_v.get("visita", {}).get("gf", 0), "Goles Contra (GC)": stats_v.get("visita", {}).get("gc", 0),
                                "Prom. GF/Partido": stats_v.get("visita", {}).get("avg_gf", 0.0), "Prom. GC/Partido": stats_v.get("visita", {}).get("avg_gc", 0.0)
                            }
                        ]
                        st.dataframe(pd.DataFrame(data_metrics), width="stretch")

                        # 3. INERCIA MULTITORNEO
                        st.divider()
                        st.subheader("🔥 3. Inercia y Rachas Recientes Multitorneo")
                        col_f1, col_f2 = st.columns(2)
                        with col_f1:
                            st.write(f"**Últimos 10 Partidos de {info_l['nombre']}**")
                            if not df_f1.empty: 
                                st.dataframe(df_f1[["Fecha", "Res", "Rival", "Score", "Torneo"]], width="stretch")
                            else: st.caption("Sin datos recientes.")
                        
                        with col_f2:
                            st.write(f"**Últimos 10 Partidos de {info_v['nombre']}**")
                            if not df_f2.empty: 
                                st.dataframe(df_f2[["Fecha", "Res", "Rival", "Score", "Torneo"]], width="stretch")
                            else: st.caption("Sin datos recientes.")

                        # 4. SIMULACIÓN DIXON-COLES & POISSON
                        st.divider()
                        st.subheader("🎯 4. Marcadores Probables con Corrección Dixon-Coles")
                        pl_dc, pe_dc, pv_dc, top_m = calcular_poisson_dixon_coles(lambda_l, mu_v)

                        col_p1, col_p2, col_p3 = st.columns(3)
                        with col_p1:
                            st.metric(f"🏠 Gana {info_l['nombre']}", f"{pl_dc}%")
                            st.caption(f"{lambda_l:.2f} xG Esperados")
                        with col_p2:
                            st.metric("🤝 Empate Científico", f"{pe_dc}%")
                            st.caption("Ajuste Dixon-Coles")
                        with col_p3:
                            st.metric(f"✈️ Gana {info_v['nombre']}", f"{pv_dc}%")
                            st.caption(f"{mu_v:.2f} xG Esperados")

                        st.subheader("Top 5 Marcadores Exactos")
                        st.dataframe(pd.DataFrame(top_m), width="stretch")

                        # 5. DIAGNÓSTICO PARTIDO TRAMPA
                        st.divider()
                        st.subheader("⚠️ 5. Diagnóstico Algorítmico de PARTIDO TRAMPA")
                        m_v_raw = row_p.get("Momio Visitante", "200")
                        es_favorito_v = str(m_v_raw).startswith("-") or (limpiar_y_convertir_momio(m_v_raw) or 200) < 130
                        
                        probs_ord = [("Local (1)", pl_dc), ("Empate (X)", pe_dc), ("Visita (2)", pv_dc)]
                        probs_ord.sort(key=lambda k: k[1], reverse=True)
                        t1_nom, t1_val = probs_ord[0]
                        t2_nom, t2_val = probs_ord[1]

                        if ("Local (1)" in [t1_nom, t2_nom]) and ("Empate (X)" in [t1_nom, t2_nom]):
                            doble_recomendado = "🎯 **Doble Local / Empate (1X)**"
                        elif ("Local (1)" in [t1_nom, t2_nom]) and ("Visita (2)" in [t1_nom, t2_nom]):
                            doble_recomendado = "🎯 **Doble Local / Visita (1 - 2)**"
                        else:
                            doble_recomendado = "🎯 **Doble Empate / Visita (X2)**"

                        pct_win_v = (pg_v / pj_v * 100.0) if pj_v > 0 else 0.0
                        if es_favorito_v and pct_win_v < 35.0:
                            st.error(
                                f"🔥 **ALERTA DE PARTIDO TRAMPA DETECTADA:** {info_v['nombre']} es marcado como favorito por el mercado de apuestas, pero sus métricas reales de Visitante Puro son muy bajas ({pct_win_v:.1f}% de victorias fuera de casa).\n\n"
                                f"💡 **RECOMENDACIÓN ESPECÍFICA DE DOBLE:** Se sugiere jugarlo con {doble_recomendado} (Combinando **{t1_nom}** de {t1_val}% + **{t2_nom}** de {t2_val}%)."
                            )
                        else:
                            st.success(
                                f"🟢 **RANGO NORMAL:** No se detecta sobrevaloración anómala en los momios de este partido.\n\n"
                                f"💡 **En caso de jugarlo a Doble:** La combinación cuantitativa más fuerte es {doble_recomendado} (Combinando **{t1_nom}** de {t1_val}% + **{t2_nom}** de {t2_val}%)."
                            )

                        # ------------------------------------------------------
                        # 6. HISTORIAL H2H CON FILTRO DE SEDES (BLINDADO POR ID)
                        # ------------------------------------------------------
                        st.divider()
                        st.subheader(f"📋 6. Historial Frente a Frente Multitorneo ({info_l['nombre']} vs {info_v['nombre']})")
                        if not df_h2h.empty:
                            filtro_h2h = st.radio(
                                "Filtro de Historial Directo:",
                                ["🌐 Todos los enfrentamientos directos", f"🏟️ Solo en estadio de {info_l['nombre']} ({info_l['nombre']} de Local)"],
                                horizontal=True,
                                key=f"radio_h2h_{partido_sel}"
                            )
                            
                            if "Solo en estadio" in filtro_h2h:
                                target_id = int(info_l["id"])
                                df_h2h_mostrado = df_h2h[df_h2h["home_id"] == target_id]
                                st.info(f"Mostrando únicamente enfrentamientos oficiales donde **{info_l['nombre']}** jugó de Local.")
                            else:
                                df_h2h_mostrado = df_h2h
                            
                            cols_h2h = ["Fecha", "Torneo", "Local", "Resultado", "Visita"]
                            st.dataframe(df_h2h_mostrado[cols_h2h], width="stretch")
                        else:
                            st.warning("Sin historial H2H reciente registrado para estos dos clubes.")

                        # 7. BAJAS
                        st.divider()
                        st.subheader("🏥 7. Reporte de Bajas y Lesionados")
                        col_b1, col_b2 = st.columns(2)
                        with col_b1:
                            st.write(f"**Bajas en {info_l['nombre']}**")
                            df_b1 = MotorAPISportsUltra.obtener_bajas(info_l["id"])
                            if not df_b1.empty: st.dataframe(df_b1, width="stretch")
                            else: st.caption("Sin reporte oficial de bajas.")
                        with col_b2:
                            st.write(f"**Bajas en {info_v['nombre']}**")
                            df_b2 = MotorAPISportsUltra.obtener_bajas(info_v["id"])
                            if not df_b2.empty: st.dataframe(df_b2, width="stretch")
                            else: st.caption("Sin reporte oficial de bajas.")

                    else:
                        st.error(f"⚠️ No se encontró alguno de los equipos en API-Sports para la liga {liga_contexto}. Revisa la ortografía.")
    else:
        st.info("Ingresa partidos completos en el Módulo 8 (Captura) para consultar la Big Data de la API.")

# MÓDULO 3: DETECTOR DE EMPATES
elif st.session_state["menu_activo"] == "🤝 3. Detector de Empates":
    st.subheader("🤝 Partidos Identificados en ZONA DE EMPATE (Diferencia < 10% Y Prob. Empate ≥ 29%)")
    df_emp = df_analisis[df_analisis["Clasificación Partido"] == "ZONA DE EMPATE"]
    if not df_emp.empty:
        st.dataframe(df_emp, width="stretch")
    else:
        st.info("No hay partidos calificados en ZONA DE EMPATE bajo el criterio científico estricto actualmente.")

# MÓDULO 4: DETECTOR DE TRAMPAS
elif st.session_state["menu_activo"] == "🔥 4. Detector de Trampas":
    st.subheader("🔥 Partidos Clasificados como PARTIDO TRAMPA")
    df_trm = df_analisis[df_analisis["Clasificación Partido"] == "PARTIDO TRAMPA"]
    if not df_trm.empty:
        st.dataframe(df_trm, width="stretch")
    else:
        st.info("No se detectan partidos trampa con los momios ingresados.")

# MÓDULO 5: POISSON & DIXON-COLES
elif st.session_state["menu_activo"] == "🎯 5. Método Poisson & Dixon-Coles":
    st.subheader("🎯 Simulación por Distribución de Dixon-Coles & Poisson (Sincronizada)")
    if partidos_validos:
        partido_poisson = st.selectbox(
            "Selecciona partido para simular marcadores:",
            partidos_validos,
            key="selectbox_tab5",
            on_change=sync_tab5_to_tab2
        )

        if partido_poisson:
            row_p = df_analisis[df_analisis["Partido"] == partido_poisson].iloc[0]
            num_p = int(row_p["#"])
            p_orig = st.session_state["tabla_progol"][num_p - 1]
            
            if partido_poisson in st.session_state["api_cache_xg"]:
                cache = st.session_state["api_cache_xg"][partido_poisson]
                xg_local = cache["xg_l"]
                xg_visita = cache["xg_v"]
                loc_name = cache["name_l"]
                vis_name = cache["name_v"]
                st.caption("✅ **Fuente de xG:** Datos reales descargados de la API y guardados permanentemente en disco.")
            else:
                loc_name = p_orig.get("Local", "Local")
                vis_name = p_orig.get("Visita", "Visita")
                st.warning("⚠️ Este partido aún no se descarga de la API. Ve al Módulo 2 y presiona 'Descargar Big Data' para fijar sus datos reales.")
                pl = row_p["Prob. Local (%)"]
                pv = row_p["Prob. Visitante (%)"]
                
                try:
                    pl_num = float(str(pl).replace("%", "").strip())
                    pv_num = float(str(pv).replace("%", "").strip())
                    xg_local = max(0.5, (pl_num / 100.0) * 2.5)
                    xg_visita = max(0.5, (pv_num / 100.0) * 2.2)
                except Exception:
                    xg_local, xg_visita = 1.2, 1.0

            pl_dc, pe_dc, pv_dc, top_m = calcular_poisson_dixon_coles(xg_local, xg_visita)

            col_xg1, col_xg2, col_xg3 = st.columns(3)
            with col_xg1: 
                st.metric(f"🏠 Gana {loc_name}", f"{pl_dc}%")
                st.caption(f"{xg_local:.2f} xG Esperados")
            with col_xg2: 
                st.metric("🤝 Empate Científico", f"{pe_dc}%")
                st.caption("Ajuste Dixon-Coles")
            with col_xg3: 
                st.metric(f"✈️ Gana {vis_name}", f"{pv_dc}%")
                st.caption(f"{mu_v:.2f} xG Esperados")

            st.divider()
            st.subheader("Top 5 Marcadores Exactos Probables")
            st.dataframe(pd.DataFrame(top_m), width="stretch")

# MÓDULO 6: QUINIELA MÚLTIPLE (7/8 DOBLES)
elif st.session_state["menu_activo"] == "🎫 6. Quiniela Múltiple (7/8 Dobles)":
    st.subheader("🎫 Configuración de Volante Múltiple (Quiniela Directa Progol)")
    st.caption("Asignación de coberturas dobles según dificultad de casillero y certeza del favorito.")

    cant_dobles = st.radio("Elige la cantidad de Dobles para tu Boleto:", [7, 8], index=0, horizontal=True)
    cant_fijos = 14 - cant_dobles

    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.metric("🔥 Dobles Asignados", f"{cant_dobles} Dobles")
    with col_m2:
        st.metric("🟢 Fijos Asignados", f"{cant_fijos} Fijos")

    st.divider()
    st.subheader(f"📋 Desglose de Volante Sugerido ({cant_dobles} Dobles + {cant_fijos} Fijos)")

    evaluacion_partidos = []
    for r in df_analisis.to_dict("records"):
        num = r.get("#")
        partido_nombre = r.get("Partido")
        clasif = r.get("Clasificación Partido")

        if partido_nombre in st.session_state["api_cache_xg"]:
            cache = st.session_state["api_cache_xg"][partido_nombre]
            pl, pe, pv, _ = calcular_poisson_dixon_coles(cache["xg_l"], cache["xg_v"])
            fuente = "Big Data API"
        else:
            pl_str = str(r.get("Prob. Local (%)", "0")).replace("%", "").strip()
            pe_str = str(r.get("Prob. Empate (%)", "0")).replace("%", "").strip()
            pv_str = str(r.get("Prob. Visitante (%)", "0")).replace("%", "").strip()
            try:
                pl, pe, pv = float(pl_str), float(pe_str), float(pv_str)
            except Exception:
                pl, pe, pv = 33.3, 33.3, 33.3
            fuente = "Momios Caliente"

        opciones = [("1", pl, "Local"), ("X", pe, "Empate"), ("2", pv, "Visita")]
        opciones.sort(key=lambda x: x[1], reverse=True)
        top1_code, top1_val, top1_txt = opciones[0]
        top2_code, top2_val, top2_txt = opciones[1]

        dif_top = top1_val - top2_val
        es_trampa = (clasif == "PARTIDO TRAMPA")
        es_empate = (clasif == "ZONA DE EMPATE")
        
        score_necesidad_doble = (100.0 - dif_top) + (30.0 if es_trampa else 0.0) + (20.0 if es_empate else 0.0)

        doble_codes = {top1_code, top2_code}
        if "1" in doble_codes and "X" in doble_codes:
            pron_doble = "1X (Local / Empate)"
        elif "1" in doble_codes and "2" in doble_codes:
            pron_doble = "1 - 2 (Local / Visita)"
        else:
            pron_doble = "X2 (Empate / Visita)"

        evaluacion_partidos.append({
            "#": num,
            "Partido": partido_nombre,
            "top1_code": top1_code,
            "top1_val": top1_val,
            "top1_txt": top1_txt,
            "top2_code": top2_code,
            "top2_val": top2_val,
            "top2_txt": top2_txt,
            "pron_doble": pron_doble,
            "score_doble": score_necesidad_doble,
            "clasif": clasif,
            "fuente": fuente
        })

    evaluacion_partidos.sort(key=lambda x: x["score_doble"], reverse=True)

    for idx, item in enumerate(evaluacion_partidos):
        if idx < cant_dobles:
            item["tipo"] = "🔥 DOBLE"
            item["pronostico"] = item["pron_doble"]
            item["argumento"] = f"Alta Incertidumbre ({item['top1_txt']} {item['top1_val']:.1f}% / {item['top2_txt']} {item['top2_val']:.1f} - {item['clasif']})"
        else:
            item["tipo"] = "🟢 FIJO"
            item["pronostico"] = f"{item['top1_code']} ({item['top1_txt']})"
            item["argumento"] = f"Favorito Firme ({item['top1_txt']} con {item['top1_val']:.1f}% de Certeza)"

    evaluacion_partidos.sort(key=lambda x: x["#"])

    df_quiniela_boletos = pd.DataFrame([
        {
            "#": x["#"],
            "Partido": x["Partido"],
            "Estructura": x["tipo"],
            "Pronóstico Sugerido": x["pronostico"],
            "Argumentación Técnica": x["argumento"]
        }
        for x in evaluacion_partidos
    ])

    st.dataframe(df_quiniela_boletos, width="stretch", height=540)

    st.divider()
    st.subheader("📲 Formato Directo para Copiar / WhatsApp")
    combinaciones = 2 ** cant_dobles
    costo_total = combinaciones * 15
    texto_wp = f"*QUINIELA PROGOL ({cant_dobles} DOBLES + {cant_fijos} FIJOS)*\n"
    texto_wp += f"Total Combinaciones: {combinaciones:,} | Costo Estimado: ${costo_total:,} MXN\n"
    texto_wp += "----------------------------------------\n"
    for item in evaluacion_partidos:
        texto_wp += f"{item['#']}. {item['Partido']} ➔ [{item['pronostico']}]\n"
    st.code(texto_wp, language="text")

# ------------------------------------------------------------------------------
# MÓDULO 7: MATRIZ REDUCIDA CALIBRADA (CONFIGURABLE: 7 U 8 DOBLES)
# ------------------------------------------------------------------------------
elif st.session_state["menu_activo"] == "🎰 7. Matriz Reducida":
    st.subheader("🎰 Generador de Matriz Reducida Optimizada")
    st.caption("Distribución matemática reducida de 12 combinaciones para optimizar el volante cubriendo fijos inamovibles y dobles estratégicos.")

    # Selector de 7 u 8 dobles
    cant_dobles_matriz = st.radio(
        "Configura la cantidad de Dobles para la Matriz:",
        [7, 8],
        index=0,
        horizontal=True,
        key="radio_cant_dobles_matriz"
    )
    cant_fijos_matriz = 14 - cant_dobles_matriz

    # Matrices matemáticas reducidas estándar de 12 columnas (0 = Opción Principal, 1 = Cobertura)
    MATRIZ_7_DOBLES = [
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 1, 1, 1, 1],
        [0, 1, 1, 0, 0, 1, 1],
        [0, 1, 1, 1, 1, 0, 0],
        [1, 0, 1, 0, 1, 0, 1],
        [1, 0, 1, 1, 0, 1, 0],
        [1, 1, 0, 0, 1, 1, 0],
        [1, 1, 0, 1, 0, 0, 1],
        [0, 0, 1, 0, 1, 1, 0],
        [1, 1, 1, 0, 0, 0, 0],
        [1, 0, 0, 1, 1, 0, 0],
        [0, 1, 0, 1, 0, 1, 0]
    ]

    MATRIZ_8_DOBLES = [
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 1, 1, 1, 1, 1],
        [0, 1, 1, 0, 0, 1, 1, 0],
        [0, 1, 1, 1, 1, 0, 0, 1],
        [1, 0, 1, 0, 1, 0, 1, 1],
        [1, 0, 1, 1, 0, 1, 0, 0],
        [1, 1, 0, 0, 1, 1, 0, 1],
        [1, 1, 0, 1, 0, 0, 1, 0],
        [0, 0, 1, 0, 1, 1, 0, 1],
        [1, 1, 1, 0, 0, 0, 0, 0],
        [1, 0, 0, 1, 1, 0, 0, 1],
        [0, 1, 0, 1, 0, 1, 0, 0]
    ]

    matriz_activa = MATRIZ_8_DOBLES if cant_dobles_matriz == 8 else MATRIZ_7_DOBLES

    clasificados = []
    for r in st.session_state["tabla_progol"]:
        num = r.get("#")
        loc = r.get("Local", "").strip()
        vis = r.get("Visita", "").strip()
        
        ml = limpiar_y_convertir_momio(r.get("Momio Local"))
        me = limpiar_y_convertir_momio(r.get("Momio Empate"))
        mv = limpiar_y_convertir_momio(r.get("Momio Visitante"))
        und = limpiar_y_convertir_momio(r.get("Under 2.5"))
        ov = limpiar_y_convertir_momio(r.get("Over 2.5"))
        
        p_nombre = f"{loc} vs {vis}" if loc and vis else f"Casilla {num}"

        # Regla del -140 para fijos
        es_fijo_l = ml is not None and ml <= -140
        es_fijo_v = mv is not None and mv <= -140

        score_firmeza = 0.0
        if ml is not None and ml < 0: score_firmeza = abs(ml)
        elif mv is not None and mv < 0: score_firmeza = abs(mv)

        if es_fijo_l:
            tipo = "FIJO"
            op1, op2 = "1", "1"
        elif es_fijo_v:
            tipo = "FIJO"
            op1, op2 = "2", "2"
        else:
            tipo = "DOBLE"
            # Criterio A: Partido abierto (Over negativo y Empate >= +265) -> Doble 1-2
            if ov is not None and ov < 0 and me is not None and me >= 265:
                op1, op2 = "1", "2"
            # Criterio B: Partido cerrado (Under negativo o Empate <= +215) -> Doble con Empate
            elif (und is not None and und < 0) or (me is not None and me <= 215):
                if ml is not None and mv is not None and ml < mv:
                    op1, op2 = "1", "X"
                else:
                    op1, op2 = "X", "2"
            else:
                op1, op2 = ("1", "X") if (ml or 0) < (mv or 0) else ("X", "2")

        clasificados.append({
            "#": num, "Partido": p_nombre, "Tipo": tipo, "Op1": op1, "Op2": op2, "Score": score_firmeza
        })

    # Balanceador exacto configurable de 7 a 8 dobles
    candidatos_dobles = [c for c in clasificados if c["Tipo"] == "DOBLE"]
    candidatos_fijos = [c for c in clasificados if c["Tipo"] == "FIJO"]

    if len(candidatos_dobles) > cant_dobles_matriz:
        # Si sobran dobles, los de menor incertidumbre se convierten a fijos
        candidatos_dobles.sort(key=lambda x: x["Score"], reverse=True)
        transferir = candidatos_dobles[:(len(candidatos_dobles) - cant_dobles_matriz)]
        for t in transferir:
            t["Tipo"] = "FIJO"
    elif len(candidatos_dobles) < cant_dobles_matriz:
        # Si faltan dobles, los fijos menos contundentes se cubren con doble
        candidatos_fijos.sort(key=lambda x: x["Score"])
        transferir = candidatos_fijos[:(cant_dobles_matriz - len(candidatos_dobles))]
        for t in transferir:
            t["Tipo"] = "DOBLE"
            if t["Op1"] == "1": t["Op2"] = "X"
            elif t["Op1"] == "2": t["Op2"] = "X"

    fijos_finales = [c for c in clasificados if c["Tipo"] == "FIJO"]
    dobles_finales = [c for c in clasificados if c["Tipo"] == "DOBLE"]

    col_res1, col_res2 = st.columns(2)
    with col_res1:
        st.metric("🔥 Dobles en Matriz", f"{len(dobles_finales)} Dobles")
    with col_res2:
        st.metric("🟢 Fijos en Matriz", f"{len(fijos_finales)} Fijos")

    partidos_con_datos = [c for c in clasificados if c["Partido"] != f"Casilla {c['#']}"]
    if len(partidos_con_datos) == 14:
        boletos_12 = []
        for b_idx in range(12):
            fila_boleto = []
            d_idx = 0
            for c in clasificados:
                if c["Tipo"] == "DOBLE":
                    pick = c["Op2"] if matriz_activa[b_idx][d_idx] == 1 else c["Op1"]
                    d_idx += 1
                else:
                    pick = c["Op1"]
                fila_boleto.append(pick)
            boletos_12.append(fila_boleto)

        col_nombres = [f"Boleto {i+1}" for i in range(12)]
        df_matriz_final = pd.DataFrame(boletos_12, index=col_nombres).T
        df_matriz_final.index = [f"#{c['#']} {c['Partido']} ({c['Tipo']})" for c in clasificados]

        st.dataframe(df_matriz_final, width="stretch")

        st.divider()
        st.subheader("📱 Boletos Individuales para Llenado Rápido")
        tabs_bol = st.tabs([f"Boleto #{i+1}" for i in range(12)])
        for i, tab in enumerate(tabs_bol):
            with tab:
                df_b = pd.DataFrame({
                    "Casilla": [f"#{j+1}" for j in range(14)],
                    "Partido": [clasificados[j]["Partido"] for j in range(14)],
                    "Tipo": [clasificados[j]["Tipo"] for j in range(14)],
                    "Pronóstico": boletos_12[i]
                })
                st.dataframe(df_b, width="stretch", height=480)
    else:
        st.info("Ingresa los 14 partidos y momios en el Módulo 8 para visualizar los 12 boletos generados.")

# ------------------------------------------------------------------------------
# MÓDULO 8: CAPTURA Y EDICIÓN (CON SISTEMA ANTI-APAGÓN)
# ------------------------------------------------------------------------------
elif st.session_state["menu_activo"] == "📋 8. CAPTURA Y EDICIÓN":
    st.subheader("Edición de Quiniela Manual (Celda a Celda)")
    st.info("💡 Captura momios y líneas. Al terminar de capturar, usa los botones de respaldo de abajo para proteger tus datos contra reinicios del servidor.")

    df_cap_edit = pd.DataFrame(st.session_state["tabla_progol"])
    
    grid_captura = st.data_editor(
        df_cap_edit,
        column_order=[
            "#", "Liga", "Local", "Visita", 
            "Momio Local", "Momio Empate", "Momio Visitante", 
            "Over 2.5", "Under 2.5", 
            "Apertura Local", "Apertura Empate", "Apertura Visitante"
        ],
        column_config={
            "Liga": st.column_config.SelectboxColumn(
                "Liga / Torneo",
                help="Selecciona la liga para garantizar la búsqueda exacta de los equipos en la API",
                options=OPCIONES_LIGAS,
                required=True,
                default="Liga MX"
            ),
            "Over 2.5": st.column_config.TextColumn(
                "Más 2.5 (Over)",
                help="Momio para Más de 2.5 goles (ej: -150 o +120)"
            ),
            "Under 2.5": st.column_config.TextColumn(
                "Menos 2.5 (Under)",
                help="Momio para Menos de 2.5 goles (ej: -160 o +135)"
            )
        },
        num_rows="fixed",
        width="stretch",
        key="grid_excel_v8_con_copas_y_amistosos"
    )

    st.write("")
    col_c1, col_c2, col_c3 = st.columns([2.5, 2.5, 3])
    
    with col_c1:
        if st.button("💾 Guardar Cambios en Servidor", type="primary"):
            datos_guardar = grid_captura.to_dict("records")
            st.session_state["tabla_progol"] = datos_guardar
            guardar_disco(datos_guardar)
            st.success("✅ Cambios guardados en memoria del servidor.")
            st.rerun()

    with col_c2:
        if st.button("🧹 Empezar 100% en Blanco", type="secondary"):
            st.session_state["tabla_progol"] = TABLA_EN_BLANCO
            guardar_disco(TABLA_EN_BLANCO)
            st.session_state["api_cache_xg"] = {}
            guardar_cache_api({})
            st.rerun()

def generar_boletos_bolsa_grande(n_boletos, df_partidos):
    """Genera N boletos con máximo 4 empates y de 2 a 3 sorpresas."""
    boletos_lista = []
    intentos = 0
    
    while len(boletos_lista) < n_boletos and intentos < 3000:
        intentos += 1
        ticket = []
        empates = 0
        sorpresas = 0
        
        for idx, row in df_partidos.iterrows():
            base = str(row.get("Prediccion", "1"))
            es_riesgo = str(row.get("Riesgo", "Bajo")) == "Alto"
            
            eleccion = base
            coles = random.random()
            if es_riesgo and sorpresas < 3 and coles > 0.55:
                eleccion = "2" if base == "1" else "X"
                sorpresas += 1
                
            if eleccion == "X":
                empates += 1
                
            ticket.append(eleccion)
            
        if empates <= 4 and 2 <= sorpresas <= 3:
            if ticket not in boletos_lista:
                boletos_lista.append(ticket)
                
    return boletos_lista

if st.session_state["menu_activo"] == "🔥 9. Generador Bolsa Grande (Acumulado)":
    st.subheader("🎯 Módulo Especializado: Bolsa Grande / Acumulado")
    st.write("Genera boletos optimizados aplicando filtros estrictos: Máximo 4 empates y de 2 a 3 sorpresas científicas por boleto.")
    
    cant_bols = st.slider("¿Cuántos boletos deseas generar para este acumulado?", min_value=5, max_value=30, value=10, step=5)
    
    if st.button("🚀 Generar Matriz de Acumulado"):
        if 'df_analisis' in locals() or 'df_analisis' in globals():
            boletos_resultado = generar_boletos_bolsa_grande(cant_bols, df_analisis)
            if boletos_resultado:
                st.success(f"¡Se han generado {len(boletos_resultado)} boletos exitosamente con los filtros de Bolsa Grande!")
                for i, bol in enumerate(boletos_resultado, 1):
                    st.write(f"Boleto {i}: {bol}")
            else:
                st.warning("Intenta de nuevo o ajusta ligeramente tus parámetros para encontrar combinaciones exactas.")
        else:
            st.info("Por favor, ejecuta primero tu análisis base (Módulo 1) para cargar los partidos.")
