"""WebSocket handlers for SIVA application."""

import os
import tempfile
from fastapi import WebSocket
from cartesia import AsyncCartesia
from openai import OpenAI

from config.settings import settings


async def websocket_tts(websocket: WebSocket):
    """Handle Text-to-Speech WebSocket connections."""
    print("TTS WebSocket connection received")
    await websocket.accept()
    print("TTS WebSocket accepted")
    client = AsyncCartesia(api_key=settings.cartesia_api_key)
    print("Cartesia client created")
    try:
        print("Waiting for text message...")
        data = await websocket.receive_text()
        print(f"Received text: {data[:50]}...")

        print("Creating Cartesia WebSocket...")
        ws = await client.tts.websocket()
        print("Cartesia WebSocket created, sending request...")

        output_generate = await ws.send(
            model_id=settings.sonic_model_id,
            transcript=data,
            voice={"id": settings.voice_id},
            output_format={
                "container": "raw",
                "encoding": "pcm_f32le",
                "sample_rate": 44100,
            },
            stream=True,
        )
        print("TTS request sent, processing audio chunks...")

        chunk_count = 0
        async for out in output_generate:
            if out.audio is not None:
                chunk_count += 1
                # print(f"Sending chunk {chunk_count}: {len(out.audio)} bytes")
                await websocket.send_bytes(out.audio)

        print(f"Finished sending {chunk_count} chunks")
        await ws.close()
        print("Cartesia WebSocket closed")

        # Close the WebSocket connection gracefully
        await websocket.close()
        print("Frontend WebSocket closed")

    except Exception as e:
        print(f"TTS WebSocket error: {e}")
        import traceback

        traceback.print_exc()
        try:
            await websocket.close()
        except:
            pass
    finally:
        await client.close()
        print("Cartesia client closed")


async def websocket_stt(websocket: WebSocket):
    """Handle Speech-to-Text WebSocket connections."""
    print("STT WebSocket connection received")
    await websocket.accept()
    print("STT WebSocket accepted")

    # Initialize OpenAI client
    client = OpenAI(api_key=settings.openai_api_key)

    try:
        print("[STT] Waiting for single audio chunk from client")
        # Receive a single audio message from the client
        audio_data = await websocket.receive_bytes()
        print(f"[STT] Received audio chunk: {len(audio_data)} bytes")

        print(f"[STT] Total audio received: {len(audio_data)} bytes")

        if len(audio_data) == 0:
            print("[STT] No audio data received")
            try:
                await websocket.send_text("")
                print("[STT] Sent empty response to client")
            except Exception:
                print("[STT] Could not send empty response (WebSocket closed)")
            return

        # Save audio to temporary file for OpenAI Whisper
        # Create temporary file with .wav extension
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_file.write(audio_data)
            temp_filename = temp_file.name
        print(f"[STT] Audio written to temp file: {temp_filename}")

        try:
            # Use OpenAI Whisper for transcription
            print("[STT] Sending audio to OpenAI Whisper...")
            with open(temp_filename, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model=settings.openai_whisper_model, file=audio_file, language="en"
                )

            result_text = transcript.text.strip()
            print(f"[STT] Whisper transcript: '{result_text}'")

            # Send transcript back to client
            try:
                await websocket.send_text(result_text)
                print(f"[STT] Transcript sent to client: '{result_text}'")

                # Close the WebSocket gracefully after sending response
                await websocket.close()
                print("[STT] WebSocket closed gracefully after sending transcript")

            except Exception as send_error:
                print(
                    f"[STT] Could not send transcript (WebSocket may be closed): {send_error}"
                )

        except Exception as e:
            print(f"[STT] OpenAI Whisper error: {e}")
            try:
                await websocket.send_text("")
                print("[STT] Sent empty response to client after Whisper error")
            except Exception:
                print("[STT] Could not send empty response (WebSocket may be closed)")

        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_filename)
                print(f"[STT] Temporary audio file cleaned up: {temp_filename}")
            except Exception:
                print(f"[STT] Could not clean up temp file: {temp_filename}")

        print("[STT] STT processing complete")

    except Exception as e:
        print(f"STT WebSocket error: {e}")
        import traceback

        traceback.print_exc()
        try:
            await websocket.send_text("")
            await websocket.close()
        except Exception:
            pass
