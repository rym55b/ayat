from flask import Flask, request, send_file, render_template
import os
import cv2
import numpy as np
import ffmpeg
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

app = Flask(__name__)

# Paramètres de la vidéo
WIDTH, HEIGHT = 1280, 720
BG_COLOR = (0, 0, 0)
TEXT_COLOR = (255, 255, 255)
FONT_PATH = "Amiri-Regular.ttf"  # Assurez-vous que la police est dans le même répertoire
FONT_SIZE = 60
FPS = 30
DURATION_PER_VERSE = 5
SCROLL_SPEED = 4

TEMP_VIDEO = "temp_video.mp4"
OUTPUT_VIDEO = "output.mp4"

@app.route('/')
def index():
    return render_template('index.html')  # Affiche la page web

@app.route('/generate-video', methods=['POST'])
def generate_video():
    verse = request.form['verse']
    audio_file = request.files['audio']
    audio_file.save("temp_audio.m4a")

    # Générer la vidéo
    generate_video_with_text(verse, "temp_audio.m4a", OUTPUT_VIDEO)

    # Renvoyer la vidéo générée
    return send_file(OUTPUT_VIDEO, as_attachment=True)

def generate_video_with_text(verse, audio_file, output_file):
    # Charger la police
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)

    # Charger l'image de fond
    background = Image.open("charit.jpg").resize((WIDTH, HEIGHT))

    # Initialiser la vidéo avec OpenCV
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    video_writer = cv2.VideoWriter(TEMP_VIDEO, fourcc, FPS, (WIDTH, HEIGHT))

    # Générer la vidéo avec du texte défilant
    reshaped_text = arabic_reshaper.reshape(verse)
    bidi_text = get_display(reshaped_text)

    words = bidi_text.split()
    word_widths = [ImageDraw.Draw(Image.new("RGB", (1, 1))).textbbox((0, 0), word, font=font)[2] for word in words]
    total_width = sum(word_widths) + (len(words) - 1) * 20

    start_x = -total_width
    end_x = WIDTH
    x_position = start_x
    y_position = HEIGHT - 255

    while x_position < end_x:
        frame = background.copy()
        draw = ImageDraw.Draw(frame)

        current_x = x_position
        for word, width in zip(words, word_widths):
            draw.text((current_x, y_position), word, font=font, fill=TEXT_COLOR)
            current_x += width + 20

        frame_cv = cv2.cvtColor(np.array(frame), cv2.COLOR_RGB2BGR)
        video_writer.write(frame_cv)
        x_position += SCROLL_SPEED

    video_writer.release()

    # Ajouter l’audio avec FFmpeg
    ffmpeg.concat(
        ffmpeg.input(TEMP_VIDEO).video,
        ffmpeg.input(audio_file).audio,
        v=1, a=1
    ).output(output_file, vcodec="libx264", acodec="aac").run(overwrite_output=True)

if __name__ == '__main__':
    app.run(debug=True)