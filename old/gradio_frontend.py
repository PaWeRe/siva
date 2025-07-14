import gradio as gr
import requests
import uuid
import json
import websockets
import asyncio
import sounddevice as sd
import numpy as np
import threading
import time
import os
import subprocess

API_URL = "http://localhost:8000/chat"
TTS_WS_URL = "ws://localhost:8000/ws/tts"
STT_WS_URL = "ws://localhost:8000/ws/stt"

# Generate a unique session ID per user
session_id = str(uuid.uuid4())

# Global state for the call
call_active = False
transcript_log = []

ASSETS_DIR = os.path.join(os.path.dirname(__file__), 'assets')
DING_PATH = os.path.join(ASSETS_DIR, 'ding.wav')

def test_backend_connection():
    """Test if the backend is reachable"""
    try:
        response = requests.get("http://localhost:8000/")
        if response.status_code == 200:
            return "✅ Backend connected"
        else:
            return f"❌ Backend error: {response.status_code}"
    except Exception as e:
        return f"❌ Backend unreachable: {e}"

def chat_with_agent(user_input):
    payload = {"session_id": session_id, "message": user_input}
    try:
        print(f"Sending to chat API: {payload}")
        response = requests.post(API_URL, json=payload)
        print(f"Chat API response status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Chat API response: {result}")
            reply = result.get("reply", "No reply from server.")
            data = result.get("data", {})
            end_call = result.get("end_call", False) # Added end_call flag
            return reply, data, end_call
        else:
            return f"Error: {response.status_code}", {}, False
    except Exception as e:
        print(f"Chat API error: {e}")
        return f"Error: {e}", {}, False

def play_tts(text):
    print(f"Playing TTS for: {text[:50]}...")
    async def tts_ws(text):
        try:
            print(f"Connecting to TTS WebSocket: {TTS_WS_URL}")
            async with websockets.connect(TTS_WS_URL) as ws:
                print("TTS WebSocket connected, sending text...")
                await ws.send(text)
                audio_chunks = b""
                chunk_count = 0
                try:
                    # Add timeout to prevent hanging
                    async with asyncio.timeout(30):  # 30 second timeout
                        async for chunk in ws:
                            if isinstance(chunk, bytes):
                                audio_chunks += chunk
                                chunk_count += 1
                                print(f"Received chunk {chunk_count}: {len(chunk)} bytes")
                            else:
                                print(f"Received non-bytes: {type(chunk)}")
                except websockets.exceptions.ConnectionClosed:
                    print("TTS WebSocket closed normally")
                    pass
                except asyncio.TimeoutError:
                    print("TTS WebSocket timeout - proceeding with received audio")
                    pass
                
                print(f"TTS received {len(audio_chunks)} bytes of audio in {chunk_count} chunks")
                if audio_chunks:
                    try:
                        audio_np = np.frombuffer(audio_chunks, dtype=np.float32)
                        print(f"Playing audio: {len(audio_np)} samples")
                        sd.play(audio_np, 44100)
                        sd.wait()
                        print("Audio playback finished")
                    except Exception as audio_error:
                        print(f"Audio playback error: {audio_error}")
                else:
                    print("No audio data received")
        except Exception as e:
            print(f"TTS error: {e}")
            import traceback
            traceback.print_exc()
    
    try:
        asyncio.run(tts_ws(text))
    except Exception as e:
        print(f"TTS asyncio error: {e}")
        import traceback
        traceback.print_exc()

def transcribe_audio(audio_path):
    async def stt_ws(audio_path):
        try:
            async with websockets.connect(STT_WS_URL) as ws:
                with open(audio_path, "rb") as f:
                    while chunk := f.read(4096):
                        await ws.send(chunk)
                await ws.close()
                
                transcript = ""
                try:
                    async for message in ws:
                        transcript += message
                except websockets.exceptions.ConnectionClosed:
                    pass
                return transcript
        except Exception as e:
            print(f"STT error: {e}")
            return "Error in speech recognition"
    return asyncio.run(stt_ws(audio_path))

def start_call():
    global call_active, transcript_log
    print("Starting call...")
    call_active = True
    transcript_log = []
    
    try:
        # Agent starts the conversation
        greeting = "Hello! I'm Jessica from Tsidi Health Services. I'm here to help collect some information before your doctor visit. Let's get started!"
        transcript_log.append(("Agent", greeting))
        print(f"Playing greeting: {greeting}")
        
        # Play greeting
        play_tts(greeting)
        print("Greeting played, getting first question...")
        
        # Get agent's first question by sending empty message to trigger intro
        reply, data, end_call = chat_with_agent("")
        print(f"Agent reply: {reply}")
        transcript_log.append(("Agent", reply))
        play_tts(reply)
        
        mic_status = "🎤 Mic is ON – please speak now!"
        try:
            subprocess.run(['afplay', DING_PATH])
        except Exception as e:
            print(f"Ding sound error: {e}")
        return format_transcript(), json.dumps(data, indent=2), gr.update(visible=True), gr.update(visible=False), gr.update(visible=True), gr.update(value=mic_status)
    except Exception as e:
        print(f"Error in start_call: {e}")
        return f"Error starting call: {e}", "{}", gr.update(visible=False), gr.update(visible=True), gr.update(visible=False), gr.update(value="Mic is OFF.")

def stop_call():
    global call_active
    print("Stopping call...")
    call_active = False
    transcript_log.append(("System", "Call ended"))
    return format_transcript(), "{}", gr.update(visible=False), gr.update(visible=True), gr.update(visible=False), gr.update(value="Mic is OFF. Call ended.")

def handle_user_response(audio_path):
    global transcript_log
    if not call_active or not audio_path:
        return format_transcript(), "{}", gr.update(visible=True), gr.update(visible=False), gr.update(value="Mic is OFF.")
    
    # Transcribe user's response
    user_text = transcribe_audio(audio_path)
    transcript_log.append(("You", user_text))
    
    # Get agent's response
    reply, data, end_call = chat_with_agent(user_text)
    transcript_log.append(("Agent", reply))
    
    # Play agent's response
    play_tts(reply)
    
    mic_status = "🎤 Mic is ON – please speak now!"
    if end_call:
        call_active = False
        mic_status = "Mic is OFF. Call ended."
        return format_transcript(), json.dumps(data, indent=2), gr.update(visible=False), gr.update(visible=True), gr.update(value=mic_status)
    else:
        mic_status = "Mic is OFF. Processing..."
        try:
            subprocess.run(['afplay', DING_PATH])
        except Exception as e:
            print(f"Ding sound error: {e}")
        return format_transcript(), json.dumps(data, indent=2), gr.update(visible=True), gr.update(visible=False), gr.update(value=mic_status)

def format_transcript():
    formatted = ""
    for speaker, text in transcript_log:
        formatted += f"**{speaker}:** {text}\n\n"
    return formatted

def end_call():
    global call_active
    call_active = False
    return format_transcript(), "{}", gr.update(visible=False), gr.update(visible=True)

with gr.Blocks(title="SIVA - Voice Patient Intake") as demo:
    gr.Markdown("# 🎤 SIVA Voice Patient Intake\n### Click 'Start Call' to begin your voice consultation with Jessica")
    
    # Add backend status
    backend_status = gr.Textbox(value=test_backend_connection(), label="Backend Status", interactive=False)
    mic_status_display = gr.Markdown(value="", label="Mic Status")
    
    with gr.Row():
        with gr.Column(scale=2):
            start_btn = gr.Button("📞 Start Call", variant="primary", size="lg")
            stop_btn = gr.Button("⏹️ Stop Call", variant="stop", size="lg", visible=False)
            
            mic_input = gr.Audio(
                sources=["microphone"], 
                type="filepath", 
                label="🎙️ Speak your response",
                visible=False
            )
            
        with gr.Column(scale=3):
            transcript_display = gr.Markdown(
                value="*Call not started. Click 'Start Call' to begin.*",
                label="Live Conversation"
            )
    
    with gr.Row():
        data_display = gr.Code(
            value="{}",
            label="📋 Collected Information",
            language="json"
        )
    
    # Event handlers
    start_btn.click(
        start_call,
        outputs=[transcript_display, data_display, mic_input, start_btn, stop_btn, mic_status_display]
    )
    
    stop_btn.click(
        stop_call,
        outputs=[transcript_display, data_display, mic_input, start_btn, stop_btn, mic_status_display]
    )
    
    mic_input.change(
        handle_user_response,
        inputs=[mic_input],
        outputs=[transcript_display, data_display, mic_input, start_btn, mic_status_display]
    )

if __name__ == "__main__":
    demo.launch() 