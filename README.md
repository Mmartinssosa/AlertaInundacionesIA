# 🌊 Alerta Inundaciones IA - Plataforma de Información y Prevención

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-Framework-black.svg)](https://flask.palletsprojects.com/)
[![SQLite](https://img.shields.io/badge/Database-SQLite-003B57.svg)](https://www.sqlite.org/index.html)
[![Frontend](https://img.shields.io/badge/Frontend-HTML%20%7C%20CSS%20%7C%20JS-orange.svg)](https://developer.mozilla.org/es/docs/Web/HTML)
[![Google Maps API](https://img.shields.io/badge/Maps-Google%20Maps%20API-green.svg)](https://developers.google.com/maps)
[![NewsAPI](https://img.shields.io/badge/News-NewsAPI-yellow.svg)](https://newsapi.org/)
[![OpenWeatherMap](https://img.shields.io/badge/Weather-OpenWeatherMap-red.svg)](https://openweathermap.org/)
[![Nominatim OSM](https://img.shields.io/badge/Geocoding-Nominatim%20OSM-lightgray.svg)](https://nominatim.org/)

---

## 💡 Sobre el Proyecto

Esta aplicación es una **plataforma web integral diseñada para proporcionar información en tiempo real y herramientas de prevención sobre inundaciones**. Permite a los usuarios visualizar zonas afectadas, reportar incidentes, acceder a noticias relevantes, consultar el pronóstico del tiempo y recibir alertas tempranas. El objetivo es ofrecer una herramienta accesible y útil para la comunidad en la gestión de eventos hidrometeorológicos extremos.

## ✨ Características Principales

* **Mapa Interactivo:** Visualización de zonas de inundación y reportes de usuarios en un mapa interactivo (Google Maps API).
* **Reporte Ciudadano:** Funcionalidad para que los usuarios reporten incidentes de inundación, incluyendo descripción, nivel del agua y la posibilidad de adjuntar una imagen.
* **Noticias de Inundaciones:** Agrega noticias de diversas fuentes sobre eventos de inundación y temporales (vía NewsAPI y SMN).
* **Pronóstico del Tiempo:** Muestra el pronóstico meteorológico actual y futuro para la ubicación del usuario (vía OpenWeatherMap).
* **Alertas Tempranas:** Proporciona un canal para la difusión de alertas y avisos de prevención.
* **Formulario de Contacto:** Permite a los usuarios enviar consultas o comentarios.
* **Base de Datos SQLite:** Persistencia de datos para reportes y mensajes de contacto.
* **Geocodificación:** Conversión de direcciones a coordenadas geográficas para la precisión de los reportes.

## 🏗️ Componentes

* **Frontend:**
    * Una página HTML interactiva construida con **Tailwind CSS** para un diseño responsivo y moderno.
    * **JavaScript** puro para la lógica del cliente y la interacción con el backend.
    * **Google Maps API** para la visualización del mapa y la geocodificación en el cliente.
    * **AOS (Animate On Scroll)** para animaciones al desplazar la página.
* **Backend:**
    * Una API RESTful robusta construida con **Python 3.x** y el microframework **Flask**.
    * **SQLite3** como base de datos ligera para el almacenamiento de reportes y mensajes.
    * **`feedparser`** para consumir feeds RSS del Servicio Meteorológico Nacional (SMN).
    * **`requests`** para interactuar con APIs externas (NewsAPI, OpenWeatherMap, Nominatim OSM).
    * **`python-dotenv`** para la gestión segura de variables de entorno (API Keys).
    * **`Flask-CORS`** para manejar las políticas de Cross-Origin Resource Sharing.

## 📋 Requisitos Previos

Asegúrate de tener instalados los siguientes componentes en tu sistema:

* **Python 3.9 o superior.**
* `pip` (el instalador de paquetes de Python), que usualmente viene con Python.
* Un navegador web moderno (Chrome, Firefox, Edge, Safari, etc.).

### 🔑 Configuración de API Keys

Este proyecto utiliza varias APIs externas. Necesitarás obtener tus propias claves y configurarlas:

1.  **Google Maps API Key:**
    * Obtén una clave API de Google Cloud Console.
    * **IMPORTANTE:** Restringe esta clave por dominio (HTTP referrers) a `http://localhost:5000/*` (para desarrollo) y `https://tu-dominio.com/*` (para producción).
    * Esta clave se inserta directamente en el archivo `index.html` en la URL de carga de la API de Google Maps.
2.  **NewsAPI Key:**
    * Regístrate en [newsapi.org](https://newsapi.org/) para obtener una clave gratuita.
    * Asegúrate de que tu plan te permita realizar suficientes solicitudes.
3.  **OpenWeatherMap API Key:**
    * Regístrate en [openweathermap.org](https://openweathermap.org/) para obtener una clave.
    * Necesitarás un plan que incluya el pronóstico de 5 días / 3 horas si estás usando esa funcionalidad.

Una vez que tengas tus claves, crea un archivo `.env` en el directorio raíz de tu backend (`backend/app.py`) con el siguiente formato:

```dotenv
NEWS_API_KEY="TU_CLAVE_DE_NEWSAPI"
OPENWEATHERMAP_API_KEY="TU_CLAVE_DE_OPENWEATHERMAP"
