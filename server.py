from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
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
                video_title, video_url = search_youtube(song_name)

                speech_text = f"Encontré {video_title} en YouTube."
                return build_response(speech_text, video_url)

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
