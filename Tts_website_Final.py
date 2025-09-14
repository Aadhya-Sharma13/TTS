# text-to-speech-website.py
# A simple web application using Flask to convert text to speech
# in English, Hindi, and Punjabi, with download functionality.

import os
import io
from flask import Flask, render_template_string, request, send_file
from gtts import gTTS

app = Flask(__name__)

# --- HTML Template with Embedded CSS and JavaScript ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Multilingual Text-to-Speech</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f9;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            color: #333;
        }
        .container {
            background-color: #fff;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            width: 90%;
            max-width: 600px;
            text-align: center;
        }
        h1 {
            color: #4a4e69;
            margin-bottom: 20px;
        }
        textarea {
            width: 100%;
            height: 150px;
            padding: 10px;
            border: 1px solid #ccc;
            border-radius: 8px;
            margin-bottom: 15px;
            font-size: 16px;
            resize: vertical;
            box-sizing: border-box;
        }
        .controls {
            display: flex;
            flex-direction: column;
            gap: 15px;
            align-items: center;
        }
        .audio-controls {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-top: 10px;
        }
        select {
            padding: 10px;
            border-radius: 8px;
            border: 1px solid #ccc;
            font-size: 16px;
            width: 100%;
            max-width: 300px;
            box-sizing: border-box;
        }
        button {
            padding: 12px 25px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
            transition: background-color 0.3s ease;
            width: 100%;
            max-width: 200px;
            box-sizing: border-box;
            color: #fff;
        }
        #speakButton {
            background-color: #6a0572;
        }
        #speakButton:hover {
            background-color: #4a0350;
        }
        #downloadButton {
            background-color: #05668d;
        }
        #downloadButton:hover {
            background-color: #034b6b;
        }
        #playPauseButton {
            background-color: #f39c12;
        }
        #playPauseButton:hover {
            background-color: #e67e22;
        }
        
        .message {
            margin-top: 20px;
            font-weight: bold;
            color: #e74c3c;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Multilingual Text-to-Speech</h1>
        <textarea id="textInput" placeholder="Enter text in English, Hindi, or Punjabi..."></textarea>
        <div class="controls">
            <select id="voiceSelect">
                <option value="en">English Voice</option>
                <option value="hi">Hindi Voice</option>
                <option value="pa">Punjabi Voice</option>
            </select>
            <button id="speakButton">Speak</button>
            <div class="audio-controls">
                <button id="playPauseButton" style="display: none;">Pause</button>
            </div>
            <button id="downloadButton">Download MP3</button>
        </div>
        <div id="message" class="message"></div>
    </div>

    <script>
        let currentAudio = null;
        const speakButton = document.getElementById('speakButton');
        const playPauseButton = document.getElementById('playPauseButton');
        const downloadButton = document.getElementById('downloadButton');
        const messageDiv = document.getElementById('message');

        const showPlayPauseButton = () => {
            playPauseButton.style.display = 'block';
        };

        const hidePlayPauseButton = () => {
            playPauseButton.style.display = 'none';
        };

        speakButton.addEventListener('click', async () => {
            const text = document.getElementById('textInput').value;
            const lang = document.getElementById('voiceSelect').value;
            
            if (text.trim() === '') {
                messageDiv.textContent = 'Please enter some text to speak.';
                messageDiv.style.color = '#e74c3c';
                return;
            }

            if (currentAudio) {
                currentAudio.pause();
                currentAudio.currentTime = 0;
                URL.revokeObjectURL(currentAudio.src);
            }

            messageDiv.textContent = 'Generating audio...';
            messageDiv.style.color = '#3498db';
            
            try {
                const response = await fetch('/tts', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text, lang, download: false })
                });

                if (!response.ok) {
                    const errorText = await response.text();
                    throw new Error(errorText || 'Network response was not ok');
                }

                const audioBlob = await response.blob();
                const audioUrl = URL.createObjectURL(audioBlob);
                currentAudio = new Audio(audioUrl);
                currentAudio.play();
                
                playPauseButton.textContent = 'Pause';
                showPlayPauseButton();

                currentAudio.onplay = () => {
                    messageDiv.textContent = 'Playing audio...';
                    messageDiv.style.color = '#3498db';
                    playPauseButton.textContent = 'Pause';
                };

                currentAudio.onpause = () => {
                    messageDiv.textContent = 'Audio paused.';
                    messageDiv.style.color = '#f39c12';
                    playPauseButton.textContent = 'Resume';
                };

                currentAudio.onended = () => {
                    messageDiv.textContent = 'Playback finished.';
                    messageDiv.style.color = '#27ae60';
                    hidePlayPauseButton();
                    URL.revokeObjectURL(audioUrl); // Clean up the URL
                    currentAudio = null;
                };

            } catch (error) {
                console.error('Error during audio playback:', error);
                messageDiv.textContent = 'Error: ' + error.message;
                messageDiv.style.color = '#e74c3c';
                hidePlayPauseButton();
            }
        });

        playPauseButton.addEventListener('click', () => {
            if (currentAudio) {
                if (currentAudio.paused) {
                    currentAudio.play();
                } else {
                    currentAudio.pause();
                }
            }
        });
        
        downloadButton.addEventListener('click', async () => {
            const text = document.getElementById('textInput').value;
            const lang = document.getElementById('voiceSelect').value;

            if (text.trim() === '') {
                messageDiv.textContent = 'Please enter some text to download.';
                messageDiv.style.color = '#e74c3c';
                return;
            }

            messageDiv.textContent = 'Preparing download...';
            messageDiv.style.color = '#3498db';

            try {
                const response = await fetch('/tts', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text, lang, download: true })
                });
                
                if (!response.ok) {
                    const errorText = await response.text();
                    throw new Error(errorText || 'Network response was not ok');
                }

                const blob = await response.blob();
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = `speech_${new Date().toISOString()}.mp3`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);

                messageDiv.textContent = 'Download started!';
                messageDiv.style.color = '#27ae60';

            } catch (error) {
                console.error('Error during download:', error);
                messageDiv.textContent = 'Error: ' + error.message;
                messageDiv.style.color = '#e74c3c';
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Renders the main HTML page for the text-to-speech application."""
    print("--- Serving index.html page ---")
    return render_template_string(HTML_TEMPLATE)

@app.route('/tts', methods=['POST'])
def tts():
    """
    Handles text-to-speech conversion requests.
    
    Accepts JSON with 'text', 'lang', and a 'download' boolean.
    Generates an MP3 file in memory and either sends it for playback
    or with a download-triggering header.
    """
    try:
        data = request.json
        text = data.get('text', '')
        lang = data.get('lang', 'en')
        download_requested = data.get('download', False)

        print(f"--- Received request: Text='{text[:30]}...', Language='{lang}', Download={download_requested} ---")

        # Validate input
        if not text.strip():
            print("--- Error: Text is empty ---")
            return "Text cannot be empty", 400

        # Create a gTTS object with the specified language
        tts_obj = gTTS(text=text, lang=lang)
        
        # Save the audio data to a BytesIO object (in-memory file)
        audio_stream = io.BytesIO()
        tts_obj.write_to_fp(audio_stream)
        audio_stream.seek(0) # Rewind the stream to the beginning
        
        # Determine the filename
        filename = f"speech_{lang}.mp3"

        # If download is requested, add the Content-Disposition header
        if download_requested:
            print("--- Sending file for download ---")
            return send_file(
                audio_stream,
                mimetype='audio/mpeg',
                as_attachment=True,
                download_name=filename
            )
        else:
            # For playback, just send the file
            print("--- Sending file for playback ---")
            return send_file(
                audio_stream,
                mimetype='audio/mpeg'
            )

    except Exception as e:
        # Catch any errors during the process and print them to the terminal
        print(f"--- An error occurred during TTS generation: {e} ---")
        return f"Error: {str(e)}", 500

if __name__ == '__main__':
    # Run the Flask application
    # host='0.0.0.0' makes the server accessible on the local network
    app.run(debug=True, host='0.0.0.0', port=5000)

