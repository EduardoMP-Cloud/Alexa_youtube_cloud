from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")

LAPTOP_URL = "https://a418-2001-1388-1e43-fe43-ac70-4e76-f0fa-547d.ngrok-free.app/control"  # Se usa ngrok http 5050

def enviar_comando_laptop(comando, url=None):
    try:
        payload = {"command": comando}
        if url:
            payload["url"] = url

        print(f"Enviando a laptop: {payload} -> {LAPTOP_URL}")

        response = requests.post(LAPTOP_URL, json=payload, timeout=1)
        return response.status_code == 200

    except Exception as e:
        print("No se pudo contactar con la laptop:", e)
        return False

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"

@app.route("/webhook", methods=["POST"])
def alexa_webhook():
    try:
        data = request.get_json()

        if data["request"]["type"] == "LaunchRequest":
            return build_response("Bienvenido. Dime qué canción deseas reproducir.")

        if data["request"]["type"] == "IntentRequest":
            intent = data["request"]["intent"]
            if intent["name"] == "PlaySongIntent":
                song_name = intent["slots"]["song"]["value"]

                if not song_name or any(word in song_name.lower() for word in ["volumen", "pausa", "cierra", "siguiente"]):
                    return build_response("No entendí bien qué canción deseas reproducir. Por favor, intenta de nuevo.")

                video_title, video_url = search_youtube(song_name)
                laptop_activa = enviar_comando_laptop("open", url=video_url)
                return build_response(f"Encontré {video_title} en YouTube. Te envié el enlace a la app de Alexa.", video_url)

            elif intent["name"] == "PauseVideoIntent":
                enviar_comando_laptop("pause")
                return build_response("Video pausado.")

            elif intent["name"] == "VolumeUpIntent":
                enviar_comando_laptop("volume_up")
                return build_response("Subiendo el volumen.")

            elif intent["name"] == "VolumeDownIntent":
                enviar_comando_laptop("volume_down")
                return build_response("Bajando el volumen.")

            elif intent["name"] == "NextSongIntent":
                enviar_comando_laptop("next")
                return build_response("Pasando a la siguiente canción.")

            elif intent["name"] == "CloseYoutubeIntent":
                enviar_comando_laptop("close")
                return build_response("Cerrando YouTube.")

        return build_response("No entendí tu solicitud.")

    except Exception as e:
        print(f"Error: {e}")
        return build_response("Ocurrió un error al procesar la solicitud.")

def search_youtube(query):
    params = {
        "part": "snippet",
        "q": query,
        "key": YOUTUBE_API_KEY,
        "maxResults": 1,
        "type": "video"
    }

    response = requests.get(YOUTUBE_SEARCH_URL, params=params)
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

