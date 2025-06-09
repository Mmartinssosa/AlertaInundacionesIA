import feedparser
import requests
import datetime
import os
import sqlite3 # Importar SQLite
from dateutil import parser as date_parser
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename # Para asegurar nombres de archivo
from dotenv import load_dotenv
load_dotenv()

# --- Configuración de la Aplicación Flask ---
app = Flask(__name__)
CORS(app)

# --- Configuración de la Base de Datos SQLite ---
DATABASE = 'flood_data.db'

# --- Directorio para guardar imágenes de reportes ---
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'} # Extensiones permitidas para imágenes
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# NUEVAS RUTAS PARA SERVIR EL FRONTEND (index.html y otros archivos estáticos)
# ---------------------------------------------------------------------

# Calcula la ruta absoluta al directorio 'frontend'
# os.path.dirname(__file__) obtiene la ruta del archivo app.py (ej. C:/Users/.../backend/)
# os.path.abspath(os.path.join(..., '../frontend')) sube un nivel y entra en 'frontend'
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../frontend'))

@app.route('/')
def serve_index():
    print(f"Sirviendo index.html desde: {FRONTEND_DIR}")
    return send_from_directory(FRONTEND_DIR, 'index.html')

# Esta ruta es para servir otros archivos estáticos del frontend como CSS, JS personalizados, etc.
# Si solo tienes index.html y scripts/styles de CDN, esta ruta puede ser menos crítica,
# pero es buena práctica para cualquier otro archivo en 'frontend/'.
@app.route('/<path:filename>')
def serve_static(filename):
    print(f"Sirviendo archivo estático: {filename} desde: {FRONTEND_DIR}")
    return send_from_directory(FRONTEND_DIR, filename)

# ---------------------------------------------------------------------
# FIN DE LAS RUTAS PARA SERVIR EL FRONTEND

# --- Funciones Auxiliares para la Base de Datos ---
def get_db_connection():
    """Establece conexión con la base de datos SQLite."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row # Permite acceder a las columnas por nombre
    return conn

def init_db():
    """Inicializa la base de datos creando las tablas si no existen."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Tabla para reportes de inundaciones
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS flood_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lat REAL NOT NULL,
            lng REAL NOT NULL,
            address TEXT NOT NULL,
            description TEXT NOT NULL,
            water_level TEXT,
            image_filename TEXT, -- Nombre del archivo de imagen guardado
            timestamp TEXT NOT NULL
        )
    ''')

    # Tabla para mensajes de contacto
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            subject TEXT,
            message TEXT NOT NULL,
            received_at TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# --- Datos Simulados para secciones aún no conectadas a DB/APIs externas ---
# Estos podrían migrarse a tablas en SQLite también si se desea más adelante.
mock_db_data = {
    "frequent_flood_zones": [
        {"id": 1, "lat": -34.6037, "lng": -58.3816, "address": "Zona Frecuente: Palermo (Ejemplo)", "description": "Área históricamente propensa a inundaciones rápidas."},
        {"id": 2, "lat": -34.6158, "lng": -58.4333, "address": "Zona Frecuente: Cuenca Maldonado (Ejemplo)", "description": "Riesgo alto durante lluvias intensas."}
    ],
    "news": [
        {"id": 1, "title": "Fuertes Lluvias Causan Aniegos en Zona Sur (Ejemplo)", "source": "Noticias Locales", "date": datetime.datetime.now().isoformat(), "summary": "Varias calles resultaron intransitables tras el temporal de anoche...", "link": "#", "imageUrl": "https://placehold.co/400x250/1B263B/3DCCC7?text=Noticia+1"},
        {"id": 2, "title": "Alerta Meteorológica por Tormentas Intensas (Ejemplo)", "source": "Servicio Meteorológico", "date": (datetime.datetime.now() - datetime.timedelta(days=1)).isoformat(), "summary": "Se esperan condiciones adversas para las próximas horas en la región.", "link": "#", "imageUrl": "https://placehold.co/400x250/1B263B/3DCCC7?text=Noticia+2"}
    ],
    "weather": {
        "location": "Buenos Aires, AR (Ejemplo API)",
        "temperature": 23, "description": "Parcialmente Nublado", "feels_like": 22, "humidity": 70,
        "wind_speed": 18, "pressure": 1010, "iconUrl": "https://placehold.co/100x100/1B263B/3DCCC7?text=Clima",
        "last_updated": datetime.datetime.now().isoformat()
    },
    "predictions": [
        {"id": 1, "title": "Predicción IA: Riesgo Bajo Zona Costera (Ejemplo)", "area": "Zona Costera Norte", "riskLevel": "Bajo", "riskLevelColor": "text-green-400", "details": "Baja probabilidad de anegamientos menores en las próximas 24hs.", "validUntil": (datetime.datetime.now() + datetime.timedelta(hours=24)).isoformat(), "icon": "fa-shield-alt"},
    ],
    "early_warnings": [
         {"id": 1, "title": "Alerta Amarilla por Tormentas - AMBA (Ejemplo Backend)", "source": "Servicio Meteorológico Nacional (Simulado)", "issued_at": (datetime.datetime.now() - datetime.timedelta(hours=2)).isoformat(), "details": "Se esperan tormentas fuertes...", "link": "#"},
    ]
}

# --- Funciones para verificar extensiones de archivo ---
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Rutas de la API ---
@app.route('/api/flood-zones', methods=['GET'])
def get_flood_zones():
    """Devuelve las zonas de inundación (frecuentes de mock_db y reportadas de SQLite)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, lat, lng, address, description, water_level, image_filename, timestamp FROM flood_reports ORDER BY timestamp DESC")
    reported_zones_rows = cursor.fetchall()
    conn.close()

    reported_zones = []
    for row in reported_zones_rows:
        report = dict(row)
        if report['image_filename']:
            # Construir la URL completa para la imagen
            report['image_url'] = request.host_url.rstrip('/') + '/api/uploads/' + report['image_filename']
        else:
            report['image_url'] = None
        reported_zones.append(report)

    rta = jsonify({
        "frequent": mock_db_data["frequent_flood_zones"],
        "reported": reported_zones
    })

    print('====================')
    print(rta)
    print('====================')

    return rta

@app.route('/api/news', methods=['GET'])
def get_news():
    """Devuelve noticias combinadas de RSS locales + API externa, con filtrado de relevancia."""
    news_items = []

    # --- 1️⃣ Configuración de Palabras Clave para Filtrado (UNIFICADAS) ---
    # Palabras clave que indican ALTA relevancia para inundaciones
    keywords_highly_relevant = [
        "inundación", "desborde", "crecida", "alerta hídrica", "evacuación",
        "riesgo de inundación", "riada", "temporal", "anegamientos", "caos vehicular",
        "corte de luz por tormenta", "arroyo", "río", "aluvión"
    ]
    # Palabras clave que indican una relevancia MEDIA y que necesitan contexto
    keywords_medium_relevance = [
        "lluvia fuerte", "tormenta", "pronóstico", "precipitaciones",
        "defensa civil", "protección civil", "emergencia climática",
        "barrio afectado", "vías anegadas", "rescate", "damnificados",
        "suministro de agua", "infraestructura", "obra hídrica", "lluvia",
        "anegado", "calles inundadas", "viviendas afectadas",
        "clima extremo", "granizo", "alerta amarilla", "alerta naranja"
    ]
    # Palabras clave a EXCLUIR (si aparecen, la noticia es probablemente irrelevante para tu tema)
    keywords_to_exclude = [
        "fútbol", "deporte", "política", "elecciones", "economía", "bolsa",
        "dólar", "mercado", "inflación", "justicia", "celebridad", "espectáculos",
        "incendio", "sequía", "pandemia", "vacuna", "salud", "crimen", "seguridad",
        "noticias internacionales", "turismo", "gastronomía"
    ]
    # Nombres de lugares, ríos o zonas específicas de Argentina/Buenos Aires
    local_keywords = [
        "ríachuelo", "plata", "conurbano", "buenos aires", "laplata", "capital federal",
        "tigre", "quilmes", "san fernando", "vicente lópez", "san isidro", "morón",
        "merlo", "luján", "chascomús", "salado", "la plata", "buenos aires", "caba", "zona sur", "conurbano", "tigre", "quilmes",
        "avellaneda", "lanús", "brown", "lomas", "ezeiza", "morón", "berazategui",
        "san isidro", "merlo", "luján", "capital federal", "argentina", # Añadir "argentina" aquí es importante para la API externa
        "bernal", "solano", "temperley", "adrogue", "claypole", "longchamps", "glew", # Puedes añadir más localidades específicas
        "burzaco", "ezeiza", "canning", "cañuelas", "brandsen", "ensenda", "berisso",
        "quilmes", "berazategui", "florencio varela", "solano", "san francisco solano",
        "malvinas argentinas", "moreno", "general rodríguez", "pilar", "escobar",
        "san miguel", "jose c. paz", "hurlingham", "ituzaingó", "moron", "merlo",
        "la matanza", "gregorio de laferrere", "gonzález catán", "virrey del pino",
        "lomas de zamora", "lanús", "avellaneda", "wilde", "sarandí", "domínico",
        "monte grande", "esteban echeverría", "almirante brown", "rafael calzada",
        "marmol", "lavallol", "tristán suárez", "alejandro korn", "san vicente",
        "presidente perón", "guernica", "mar del plata", "rosario", "córdoba", "mendoza", # Otras ciudades importantes de Argentina
        "santa fe", "corrientes", "chaco", "formosa", "entre ríos" # Provincias del litoral con riesgo de inundaciones
    ]

    # --- Función Auxiliar para Filtrado (ahora más robusta y general) ---
    def is_relevant_article(title, summary, source_name="", link=""):
        # Combine all text fields that can contain keywords
        text = (title + " " + summary + " " + source_name + " " + link).lower()

        # Un artículo es relevante si contiene una palabra clave de alta relevancia
        is_highly_relevant = any(keyword in text for keyword in keywords_highly_relevant)

        # Un artículo es de relevancia media si contiene una palabra clave media Y un término local
        # Es crucial que las noticias de "lluvia fuerte" estén asociadas a Argentina/localidad.
        is_medium_and_local = any(keyword in text for keyword in keywords_medium_relevance) and \
                              any(loc_kw in text for loc_kw in local_keywords)

        # Un artículo es excluido si contiene cualquier palabra clave de exclusión
        is_excluded = any(keyword in text for keyword in keywords_to_exclude)

        # La lógica de inclusión: (altamente relevante O (media relevancia Y local)) Y NO excluida
        return (is_highly_relevant or is_medium_and_local) and not is_excluded

    # --- 2️⃣ Procesamiento de Feeds RSS Locales ---
    # He actualizado algunas URLs con las que tienen más probabilidad de ser feeds RSS válidos.
    # Aún así, debes verificar cada una manualmente.
    local_rss_feeds = [
        {'name': 'Clarín Lo Último', 'url': 'https://www.clarin.com/rss/lo-ultimo/'},
        {'name': 'Infobae Lo Último', 'url': 'https://www.infobae.com/feeds/rss/'},
        {'name': 'La Nación Lo Último', 'url': 'https://www.lanacion.com.ar/arc/outboundfeeds/rss/'},
        {'name': 'Página 12 Sociedad', 'url': 'https://www.pagina12.com.ar/rss/secciones/sociedad/notas'},
        {'name': 'Ámbito Municipios', 'url': 'https://www.ambito.com/rss/pages/municipios.xml'},
        {'name': 'TN Últimas Noticias', 'url': 'https://tn.com.ar/feeds/ultimas-noticias.xml'},
        {'name': 'Diario Crónica Sociedad', 'url': 'https://www.diariocronica.com.ar/rss/sociedad'},
        {'name': 'La Voz Córdoba Lo Último', 'url': 'https://www.lavoz.com.ar/feeds/ultimas-noticias.xml'},
        # Quité los que eran claramente páginas web, Facebook, o URLs que no funcionaban como RSS.
        # Es CRUCIAL que verifiques que estas URLs de RSS son VÁLIDAS.
    ]

    for feed_info in local_rss_feeds:
        try:
            parsed_feed = feedparser.parse(feed_info['url'])
            if not parsed_feed.entries:
                print(f"Advertencia: No se encontraron entradas en el feed RSS de {feed_info['name']} ({feed_info['url']}). Puede que la URL no sea válida o esté vacía.")

            for entry in parsed_feed.entries:
                title = entry.title if hasattr(entry, 'title') else 'Sin título'
                link = entry.link if hasattr(entry, 'link') else '#'
                published_date_str = entry.published if hasattr(entry, 'published') else entry.updated if hasattr(entry, 'updated') else None
                summary = entry.summary if hasattr(entry, 'summary') else entry.description if hasattr(entry, 'description') else ''

                # --- Lógica de Extracción de Imagen para RSS ---
                image_url = ''
                if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
                    image_url = entry.media_thumbnail[0]['url']
                elif hasattr(entry, 'media_content') and entry.media_content:
                    for content_item in entry.media_content:
                        if 'image' in content_item.get('type', '') and 'url' in content_item:
                            image_url = content_item['url']
                            break
                elif 'enclosures' in entry:
                    for enc in entry.enclosures:
                        if 'image' in enc.get('type', ''):
                            image_url = enc.href
                            break

                # --- Aplicar Filtrado de Relevancia para RSS con la función unificada ---
                if is_relevant_article(title, summary, feed_info['name'], link):
                    news_items.append({
                        'title': title,
                        'source': feed_info['name'],
                        'date': published_date_str,
                        'summary': summary,
                        'link': link,
                        'imageUrl': image_url
                    })
        except Exception as e:
            print(f"Error al obtener y parsear RSS de {feed_info['name']} ({feed_info['url']}): {e}")

    # 3️⃣ API externa: GNews
    USE_GNEWS = True
    if USE_GNEWS:
        try:
            GNEWS_API_KEY = os.getenv('GNEWS_API_KEY')
            if not GNEWS_API_KEY:
                print("Error: La variable de entorno GNEWS_API_KEY no está configurada.")
                # Puedes lanzar una excepción o simplemente saltar esta parte
                # return jsonify({'error': 'GNEWS_API_KEY no configurada'}), 500
            
            # Aquí la clave: 'country=ar' ya está bien.
            # Puedes probar con más artículos si quieres para ver si encuentras más relevantes.
            # Aumentar 'max' y luego filtrar más agresivamente podría ser útil.
            gnews_url = f'https://gnews.io/api/v4/search?q=inundaciones&lang=es&country=ar&max=10&apikey={GNEWS_API_KEY}'
            
            response = requests.get(gnews_url)
            response.raise_for_status()
            gnews_data = response.json()

            # --- Aplicar Filtrado de Relevancia para GNews con la función unificada ---
            gnews_filtered_articles_count = 0
            for article in gnews_data.get('articles', []):
                title = article.get('title', 'Sin título')
                description = article.get('description', '')
                source_name = article.get('source', {}).get('name', 'GNews Source')
                link = article.get('url', '#')

                if is_relevant_article(title, description, source_name, link):
                    news_items.append({
                        'title': title,
                        'source': source_name,
                        'date': article.get('publishedAt'),
                        'summary': description,
                        'link': link,
                        'imageUrl': article.get('image', '')
                    })
                    gnews_filtered_articles_count += 1
                    # Si quieres limitar el número de noticias de GNews que agregas, hazlo aquí
                    # if gnews_filtered_articles_count >= 5: # Por ejemplo, si solo quieres 5 de GNews
                    #     break

        except requests.exceptions.RequestException as e:
            print(f"Error de red o HTTP al obtener datos de GNews: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Respuesta de GNews: {e.response.text}")
        except Exception as e:
            print(f"Error inesperado al obtener datos de GNews: {e}")
    
    # Ordenamos por fecha descendente
    def get_date(n):
        try:
            return date_parser.parse(n['date'])
        except (TypeError, ValueError): # Manejar si 'date' es None o no parseable
            return datetime.datetime.min
    
    news_items.sort(key=get_date, reverse=True)
    return jsonify(news_items)

@app.route('/api/weather', methods=['GET'])
def get_weather():
    """Devuelve el pronóstico del tiempo actual usando OpenWeatherMap."""
    OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')  
    lat = request.args.get('lat', '-34.8090')  # Almirante Brown por defecto
    lon = request.args.get('lon', '-58.4060')

    try:
        url = f'https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=es'
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        weather_data = {
            "location": f"{data['name']}, {data['sys']['country']}",
            "temperature": data['main']['temp'],
            "description": data['weather'][0]['description'],
            "feels_like": data['main']['feels_like'],
            "humidity": data['main']['humidity'],
            "wind_speed": data['wind']['speed'],
            "pressure": data['main']['pressure'],
            "iconUrl": f"https://openweathermap.org/img/wn/{data['weather'][0]['icon']}@2x.png",
            "last_updated": datetime.datetime.now().isoformat()
        }   
        return jsonify(weather_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/predictions', methods=['GET'])
def get_predictions():
    """Devuelve predicciones de riesgo de inundación (datos mock para Almirante Brown)."""
    predictions_data = [
        {
            "id": 1,
            "location_name": "Almirante Brown (Adrogué)",
            "latitude": -34.7937, # Coordenadas más específicas para Adrogué/Brown
            "longitude": -58.3917,
            "prediction_time": (datetime.datetime.now() + datetime.timedelta(hours=6)).isoformat(),
            "risk_level": "Medio",
            "probability": 0.55,
            "expected_rainfall_mm_24h": 45,
            "river_level_change_cm_24h": 8,
            "recommended_action": "Mantenerse informado, limpiar desagües y asegurar objetos en patios."
        },
        {
            "id": 2,
            "location_name": "Almirante Brown (Burzaco)",
            "latitude": -34.8090, # Coordenadas para Burzaco
            "longitude": -58.4060,
            "prediction_time": (datetime.datetime.now() + datetime.timedelta(hours=12)).isoformat(),
            "risk_level": "Bajo",
            "probability": 0.15,
            "expected_rainfall_mm_24h": 10,
            "river_level_change_cm_24h": 0,
            "recommended_action": "Condiciones normales, sin riesgo inminente en la zona."
        },
        {
            "id": 3,
            "location_name": "Almirante Brown (Longchamps)",
            "latitude": -34.8569, # Coordenadas para Longchamps
            "longitude": -58.4093,
            "prediction_time": (datetime.datetime.now() + datetime.timedelta(hours=24)).isoformat(),
            "risk_level": "Alto",
            "probability": 0.70,
            "expected_rainfall_mm_24h": 90,
            "river_level_change_cm_24h": 30,
            "recommended_action": "Evitar transitar por calles anegadas. Preparar kit de emergencia familiar."
        }
    ]
    return jsonify(predictions_data)

@app.route('/api/early-warnings', methods=['GET'])
def get_early_warnings():
    """Devuelve las alertas tempranas (datos de ejemplo)."""
    return jsonify(mock_db_data["early_warnings"])

@app.route('/api/smn_alerts', methods=['GET'])
def get_smn_alerts():
    """
    Obtiene y parsea las alertas a corto plazo del SMN (GeoRSS)
    y filtra por proximidad a Almirante Brown.
    """
    SMN_ALERT_RSS_URL = "https://ssl.smn.gob.ar/feeds/avisocorto_GeoRSS.xml"
    
    # Coordenadas de Almirante Brown para filtrar alertas relevantes
    ALMIRANTE_BROWN_LAT = -34.8090
    ALMIRANTE_BROWN_LON = -58.4060
    
    # Un radio de búsqueda (en grados decimales, aprox 1 grado = 111km)
    # 0.5 grados = ~55km, debería cubrir Almirante Brown y alrededores.
    SEARCH_RADIUS_DEG = 0.5 

    try:
        feed = feedparser.parse(SMN_ALERT_RSS_URL)
        alerts = []

        if feed.bozo: # bozo=1 significa que hubo un error al parsear el feed
            print(f"Error al parsear el feed RSS del SMN: {feed.bozo_exception}")
            # Puedes retornar un error o una lista vacía, dependiendo de tu manejo de errores
            return jsonify({"error": "No se pudieron obtener las alertas del SMN en este momento.", "details": str(feed.bozo_exception)}), 500

        for entry in feed.entries:
            alert_data = {
                "title": entry.title if hasattr(entry, 'title') else "Sin título",
                "link": entry.link if hasattr(entry, 'link') else "#",
                "summary": entry.summary if hasattr(entry, 'summary') else "Sin descripción",
                "published": entry.published_parsed if hasattr(entry, 'published_parsed') else None,
                "location_name": "Desconocida", # Asumimos hasta que encontremos GeoRSS
                "latitude": None,
                "longitude": None,
                "alert_level": "Sin especificar" # Podrías extraerlo del título/sumario si es consistente
            }

            # Intentar extraer GeoRSS (geometría)
            # GeoRSS puede estar en entry.georss_point o entry.where.features[0].geometry.coordinates
            if hasattr(entry, 'georss_point'):
                try:
                    lat_str, lon_str = entry.georss_point.split(' ')
                    alert_data["latitude"] = float(lat_str)
                    alert_data["longitude"] = float(lon_str)
                    alert_data["location_name"] = "Coordenadas específicas"
                except (ValueError, AttributeError):
                    pass # Si no se puede parsear, sigue sin coordenadas

            # Otra forma de buscar GeoRSS (para el feed avisocorto_GeoRSS.xml)
            # El feed avisocorto_GeoRSS.xml tiene la ubicación en 'georss_featuretypetag' o 'georss_where'
            if hasattr(entry, 'gegeorss_featuretypetag') and entry.gegeorss_featuretypetag.startswith('P_'):
                 alert_data["location_name"] = entry.gegeorss_featuretypetag.replace('P_', '').replace('_', ' ').title()

            # Para el feed avisocorto_GeoRSS.xml, la lat/lon suelen estar en georss_where/gml_point
            if hasattr(entry, 'georss_where') and hasattr(entry.georss_where, 'gml_point') and hasattr(entry.georss_where.gml_point, 'gml_pos'):
                try:
                    coords_str = entry.georss_where.gml_point.gml_pos
                    lat_lon = coords_str.split(' ')
                    alert_data["latitude"] = float(lat_lon[0])
                    alert_data["longitude"] = float(lat_lon[1])
                except (ValueError, AttributeError, IndexError):
                    pass

            # Filtra alertas por proximidad a Almirante Brown
            if alert_data["latitude"] is not None and alert_data["longitude"] is not None:
                distance_lat = abs(alert_data["latitude"] - ALMIRANTE_BROWN_LAT)
                distance_lon = abs(alert_data["longitude"] - ALMIRANTE_BROWN_LON)
                
                # Un filtro simple por "caja" alrededor de Almirante Brown
                # Esto es una simplificación, un cálculo de distancia más preciso es haversine
                if distance_lat <= SEARCH_RADIUS_DEG and distance_lon <= SEARCH_RADIUS_DEG:
                    alerts.append(alert_data)
            else:
                # Si no tiene coordenadas, puedes intentar filtrar por texto en el título/sumario
                # Esto es menos preciso pero puede ser útil si "Almirante Brown" aparece.
                if "Almirante Brown" in alert_data["title"] or "Almirante Brown" in alert_data["summary"]:
                     alerts.append(alert_data)


        return jsonify(alerts)
    except requests.exceptions.RequestException as e:
        print(f"Error de red al obtener el feed RSS del SMN: {e}")
        return jsonify({"error": "Error de conexión al Servicio Meteorológico Nacional."}), 500
    except Exception as e:
        print(f"Error inesperado al procesar alertas del SMN: {e}")
        return jsonify({"error": f"Error interno del servidor al procesar alertas: {str(e)}"}), 500


@app.route('/api/flood-reports', methods=['POST'])
def add_flood_report():
    """Recibe y guarda un nuevo reporte de inundación en SQLite."""
    conn = None # Inicializa la conexión a None antes del try
    try:
        # Validar campos requeridos del formulario
        address = request.form.get('address')
        description = request.form.get('description')
        if not address or not description:
            return jsonify({"message": "La dirección y la descripción son campos requeridos."}), 400

        water_level = request.form.get('water_level') # Puede ser None

        # OBTENER LATITUD Y LONGITUD DIRECTAMENTE DEL FORMULARIO
        lat_str = request.form.get('lat')
        lng_str = request.form.get('lng')

        # Convertir a float y validar
        try:
            lat = float(lat_str)
            lng = float(lng_str)
        except (ValueError, TypeError):
            return jsonify({"message": "Latitud o Longitud inválida. Asegúrate de seleccionar una ubicación válida."}), 400

        image_filename = None
        if 'image' in request.files:
            image_file = request.files['image']
            if image_file.filename != '' and allowed_file(image_file.filename):
                filename = secure_filename(image_file.filename)
                # Para evitar colisiones de nombres, se podría añadir un timestamp o UUID
                unique_filename = f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                image_file.save(image_path)
                image_filename = unique_filename
                print(f"Imagen guardada: {image_filename}")
            elif image_file.filename != '':
                # Archivo presente pero no permitido
                return jsonify({"message": "Tipo de archivo de imagen no permitido."}), 400

        conn = get_db_connection() # La conexión se establece aquí
        cursor = conn.cursor()

        # Usar la tabla 'flood_reports' y las coordenadas recibidas
        cursor.execute('''
            INSERT INTO flood_reports (address, description, lat, lng, water_level, image_filename, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (address, description, lat, lng, water_level, image_filename, datetime.datetime.now().isoformat()))
        conn.commit()
        report_id = cursor.lastrowid # Obtener el ID del reporte insertado
        conn.close()

        new_report_data = {
            "id": report_id,
            "lat": lat,
            "lng": lng,
            "address": address,
            "description": description,
            "water_level": water_level,
            "image_filename": image_filename,
            "timestamp": datetime.datetime.now().isoformat()
        }
        if image_filename: # Construir URL si la imagen fue guardada
            new_report_data['image_url'] = request.host_url.rstrip('/') + '/api/uploads/' + image_filename


        print(f"Nuevo reporte guardado en DB: ID {report_id}, Dirección: {address}, Lat: {lat}, Lng: {lng}")
        return jsonify({"message": "Reporte recibido y guardado con éxito.", "report": new_report_data}), 201

    except Exception as e:
        print(f"Error al añadir reporte de inundación: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        # Este bloque se ejecuta SIEMPRE, haya o no un error en el try
        if conn: # Solo cierra la conexión si fue establecida (no es None)
            conn.close()

@app.route('/api/uploads/<filename>')
def uploaded_file(filename):
    """Sirve los archivos de imagen subidos."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/contact', methods=['POST'])
def handle_contact_form():
    """Recibe y guarda un mensaje del formulario de contacto en SQLite."""
    conn = None # ¡Inicializa la conexión a None aquí!
    try:
        if not request.is_json:
            return jsonify({"message": "La solicitud debe ser JSON."}), 400

        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        subject = data.get('subject', 'Sin Asunto')
        message = data.get('message')

        if not name or not email or not message:
            return jsonify({"message": "Nombre, email y mensaje son campos requeridos."}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO contacts (name, email, subject, message, received_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, email, subject, message, datetime.datetime.now().isoformat()))
        conn.commit()
        contact_id = cursor.lastrowid
        # conn.close() # ¡Esta línea se mueve al bloque finally!)

        print(f"Mensaje de contacto guardado en DB: ID {contact_id} de {name} ({email})")
        return jsonify({"message": "Mensaje recibido y guardado con éxito."}), 201
    except Exception as e:
        # Captura cualquier error que ocurra durante el procesamiento
        print(f"Error al manejar el formulario de contacto: {e}")
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500
    finally:
        # ¡Este bloque se ejecuta SIEMPRE!
        if conn: # Solo cierra la conexión si fue establecida (no es None)
            conn.close()

@app.route('/geocode', methods=['GET'])
def geocode():
    address = request.args.get('address')
    if not address:
        return jsonify({"error": "Falta el parámetro 'address'"}), 400

    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": address,
        "format": "json",
        "limit": 1
    }
    headers = {
        "User-Agent": "AlertaInundaciones.IA (klini@ejemplo.com)"  # Personaliza esto
    }

    response = requests.get(url, params=params, headers=headers)

    if response.status_code == 200:
        data = response.json()
        if data:
            return jsonify({
                "latitude": data[0]["lat"],
                "longitude": data[0]["lon"]
            })
        else:
            return jsonify({"error": "No se encontraron resultados para esa dirección"}), 404
    else:
        return jsonify({"error": "Error al hacer la solicitud al servicio de geocodificación"}), 500
    

# --- Ejecución de la Aplicación ---
if __name__ == '__main__':
    init_db() # Asegura que la base de datos y las tablas estén creadas al iniciar
    app.run(debug=True, host='0.0.0.0', port=5000)
