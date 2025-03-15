import os
import subprocess
from flask import Flask, render_template, request, jsonify, send_file
from flask_socketio import SocketIO, emit
import yt_dlp

app = Flask(__name__)
socketio = SocketIO(app)

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/baixar", methods=["POST"])
def baixar_video():
    try:
        data = request.json
        video_url = data.get("url")

        if not video_url:
            return jsonify({"success": False, "error": "URL inválida"}), 400

        print(f"Baixando e convertendo vídeo para MP4: {video_url}")

        # Função de callback para capturar o progresso e logs do download
        def progress_hook(d):
            if d['status'] == 'downloading':
                progress = d.get('downloaded_bytes', 0)
                total = d.get('total_bytes', 1)  # Impede divisão por zero
                percent = (progress / total) * 100 if total > 0 else 0
                speed = d.get('speed', 0)  # Converte para KB/s
                speed = speed / 1024 if speed else 0  # Evita erro de NoneType, assume 0 se None
                eta = d.get('eta', 0)  # Tempo restante

                # Envia progresso para o frontend
                socketio.emit('download_progress', {
                    'percent': percent,
                    'speed': speed,
                    'eta': eta
                })

            # Log do processo
            if 'info' in d:
                socketio.emit('download_log', {'message': d['info']})

        # Opções do yt-dlp para baixar e converter para MP4
        ydl_opts = {
            "format": "bestvideo+bestaudio/best",  # Melhor qualidade
            "outtmpl": f"{DOWNLOAD_FOLDER}/%(title)s.%(ext)s",  # Padrão de nome de arquivo
            "postprocessors": [{  # Pós-processador para converter para MP4
                "key": "FFmpegVideoConvertor",
                "preferedformat": "mp4",  # Força a conversão para MP4
            }],
            "postprocessor_args": [
                "-preset", "ultrafast"  # Usando uma conversão mais rápida (ajustável)
            ],
            "prefer_ffmpeg": True,  # Usar FFmpeg
            "noplaylist": True,  # Evitar o download de playlists (caso seja um link de playlist)
            "progress_hooks": [progress_hook]  # Hook de progresso
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            video_title = ydl.prepare_filename(info)
            converted_video_title = video_title.rsplit(".", 1)[0] + ".mp4"

        return jsonify({"success": True, "downloadLink": f"/download/{os.path.basename(converted_video_title)}"})

    except Exception as e:
        print(f"Erro no backend: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/download/<filename>")
def download_file(filename):
    file_path = os.path.join(DOWNLOAD_FOLDER, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return "Arquivo não encontrado", 404

@app.route("/abrir_pasta", methods=["POST"])
def abrir_pasta():
    # Caminho da pasta onde o arquivo foi salvo
    folder_path = os.path.abspath(DOWNLOAD_FOLDER)

    # Para Windows
    if os.name == 'nt':
        subprocess.run(['explorer', folder_path])
    # Para MacOS
    elif os.name == 'posix':
        subprocess.run(['open', folder_path])
    # Para Linux
    else:
        subprocess.run(['xdg-open', folder_path])

    return jsonify({"success": True, "message": "Pasta aberta com sucesso!"})

if __name__ == "__main__":
    socketio.run(app, debug=True)
