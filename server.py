from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Tu API Key de YouTube (debe estar configurada como variable de entorno en Render)
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")

# Dirección IP de tu laptop a través de Tailscale
LAPTOP_URL = "http://100.90.173.124:5050/control"

def enviar_comando_laptop(comando, url=None):
    try:
        payload = {"command": comando}
        if url:
            payload["url"] = url

        print(f"✅ Enviando a laptop: {payload} -> {LAPTOP_URL}")
        response = requests.post(LAPTOP_URL, json=payload, timeout=2)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error al contactar con la laptop: {e}")
        return False

@app.route("/webhook", methods=["POST"])
def alexa_webhook():
    try:
        data = request.get_json()
        print("📡 Solicitud recibida desde Alexa")

        if data["request"]["type"] == "LaunchRequest":
            return build_response("Bienvenido. Dime qué canción deseas reproducir.")

        if data["request"]["type"] == "IntentRequest":
            intent = data["request"]["intent"]
            name = intent["name"]

            if name == "PlaySongIntent":
                song_name = intent["slots"]["song"]["value"]
                if not song_name or any(word in song_name.lower() for word in ["volumen", "pausa", "cierra", "siguiente"]):
                    return build_response("No entendí bien qué canción deseas reproducir. Por favor, intenta de nuevo.")
                
                video_title, video_url = search_youtube(song_name)
                enviar_comando_laptop("open", url=video_url)
                return build_response(f"Encontré {video_title} en YouTube. Te envié el enlace a la app de Alexa.", video_url)

            elif name == "PauseVideoIntent":
                enviar_comando_laptop("pause")
                return build_response("Video pausado.")

            elif name == "ResumeVideoIntent":
                enviar_comando_laptop("play")
                return build_response("Reproduciendo el video.")

            elif name == "VolumeUpIntent":
                enviar_comando_laptop("volume_up")
                return build_response("Subiendo el volumen.")

            elif name == "VolumeDownIntent":
                enviar_comando_laptop("volume_down")
                return build_response("Bajando el volumen.")

            elif name == "NextSongIntent":
                enviar_comando_laptop("next")
                return build_response("Pasando a la siguiente canción.")

            elif name == "CloseYoutubeIntent":
                enviar_comando_laptop("close")
                return build_response("Cerrando YouTube.")

        return build_response("No entendí tu solicitud.")

    except Exception as e:
        print(f"❌ Error en el webhook: {e}")
        return build_response("Ocurrió un error al procesar la solicitud.")

def search_youtube(query):
    params = {
        "part": "snippet",
        "q": query,
        "key": YOUTUBE_API_KEY,
        "maxResults": 1,
        "type": "video"
    }
    response = requests.get("https://www.googleapis.com/youtube/v3/search", params=params)
    results = response.json()
    item = results["items"][0]
    video_title = item["snippet"]["title"]
    video_id = item["id"]["videoId"]
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    return video_title, video_url

def build_response(speech_text, video_url=None):
    response = {
        "version": "1.0",
        "response": {
            "outputSpeech": {
                "type": "PlainText",
                "text": speech_text
            },
            "shouldEndSession": True
        }
    }
    if video_url:
        response["response"]["card"] = {
            "type": "Simple",
            "title": "Resultado de YouTube",
            "content": video_url
        }
    return jsonify(response)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
