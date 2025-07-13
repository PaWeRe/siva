import gradio as gr
import requests
import uuid
import json

API_URL = "http://localhost:8000/chat"

# Generate a unique session ID per user
session_id = str(uuid.uuid4())

def chat_with_agent(user_input, history=None):
    payload = {"session_id": session_id, "message": user_input}
    try:
        response = requests.post(API_URL, json=payload)
        if response.status_code == 200:
            reply = response.json().get("reply", "No reply from server.")
            data = response.json().get("data", {})
            return reply, json.dumps(data, indent=2)
        else:
            return f"Error: {response.status_code}", "{}"
    except Exception as e:
        return f"Error: {e}", "{}"

with gr.Blocks() as demo:
    gr.Markdown("# SIVA Patient Intake Voice Agent\nSpeak or type to interact with the intake agent.")
    with gr.Row():
        user_input = gr.Textbox(label="Your message or use mic", lines=2)
        mic = gr.Audio(sources=["microphone"], type="filepath", label="Mic (not used yet)")
    reply = gr.Textbox(label="Agent reply", interactive=False)
    data_panel = gr.Code(label="Collected Intake Data (JSON)", language="json")
    submit_btn = gr.Button("Send")

    submit_btn.click(chat_with_agent, inputs=[user_input], outputs=[reply, data_panel])
    user_input.submit(chat_with_agent, inputs=[user_input], outputs=[reply, data_panel])

if __name__ == "__main__":
    demo.launch() 