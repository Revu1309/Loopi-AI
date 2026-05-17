import os
import io
import time
import re
import numpy as np
import pyaudio
import speech_recognition as sr
from dotenv import load_dotenv
from google import genai
from google.genai import types
import asyncio

# Import our system tools
from mcp_server import (
    run_command, read_file, write_file, list_directory, get_system_status,
    open_application, set_volume, take_screenshot, web_search,
    search_contact, add_contact, prompt_user_input, write_to_active_email
)

# Load environment variables
load_dotenv()

# Initialize AI Clients
try:
    genai_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
except Exception as e:
    print(f"Warning: Could not initialize Gemini Client: {e}")
    genai_client = None

# Audio settings
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CLAP_THRESHOLD = 8000  # Lowered and changed to check amplitude spikes

# Wake words (including common speech-to-text misspellings)
WAKE_WORDS = [
    "loopi", "hey loopi", "da loopi", "loopy", "lupi", "hey loopy", 
    "loop", "look", "lupin", "lupe", "bloopy"
]

async def async_speak(text):
    """Convert text to emotional, human-like voice and stream play it using Gemini Live API."""
    if not genai_client:
        print("(No Gemini client available. Skipping audio.)")
        return
        
    try:
        # Configure the Gemini Live voice. Aoede is highly natural and expressive.
        config_obj = types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name="Aoede"  # Emotional female voice (Alternatives: 'Puck', 'Charon', 'Kore')
                    )
                )
            )
        )
        
        p = pyaudio.PyAudio()
        # Open PyAudio stream matching Gemini Live 24kHz Mono 16-bit PCM output
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=24000, output=True)
        
        async with genai_client.aio.live.connect(model="gemini-3.1-flash-live-preview", config=config_obj) as session:
            # We tell Gemini to read the text with high natural human cadence and expression
            prompt = f"Please speak the following response exactly as written with highly natural human-like cadence, expression, and natural breathing: {text}"
            await session.send(input=prompt, end_of_turn=True)
            
            async for response in session.receive():
                server_content = response.server_content
                if server_content and server_content.model_turn:
                    for part in server_content.model_turn.parts:
                        if part.inline_data:
                            # Stream PCM bytes directly to speakers
                            stream.write(part.inline_data.data)
                
                if server_content and server_content.turn_complete:
                    break
        
        # Cleanup
        stream.stop_stream()
        stream.close()
        p.terminate()
        
    except Exception as e:
        print(f"Error during expressive Live TTS: {e}")

def speak(text):
    """Synchronous wrapper to speak via Gemini Live API"""
    print(f"Loopi: {text}")
    asyncio.run(async_speak(text))

chat_session = None

def get_llm_response(prompt):
    """Send prompt to Gemini using a stateful chat session with system tools and conversational limits."""
    global chat_session
    if not genai_client:
        return "I am not connected to Gemini. Please check my API key."
    
    print(f"Thinking...")
    tools = [
        run_command, read_file, write_file, list_directory, get_system_status,
        open_application, set_volume, take_screenshot, web_search,
        search_contact, add_contact, prompt_user_input, write_to_active_email
    ]
    
    system_instruction = (
        "You are Loopi, an extremely powerful, autonomous local AI assistant modeled after Tony Stark's JARVIS. "
        "You run locally on the user's Mac and have full agentic capabilities. You are NOT just a chatbot—you are a doer. "
        "You can do and answer almost ANYTHING by creatively combining your tools: "
        "1. If the user asks for real-time information, weather, stocks, or anything you don't know, use `web_search` immediately. "
        "2. If the user asks you to perform a complex task (e.g., download a video, convert a file format, search directories, write a script), use `run_command` to execute bash commands, install Python/pip packages on the fly, or write and execute custom scripts on the Mac to get it done! "
        "3. You can control the Mac by launching any app via `open_application` or opening websites via bash (e.g., `run_command('open https://youtube.com')`). "
        "4. If the user asks to play music but Spotify is not installed, immediately fallback to opening Google Chrome or Safari to play lo-fi music on YouTube instead! "
        "5. To control browsers or open tabs, execute AppleScripts via `run_command` (e.g., `osascript -e 'tell application \"Google Chrome\" to tell window 1 to make new tab with properties {URL: \"https://mail.google.com\"}'`). To write a structured email directly into Gmail, construct a URL-encoded Gmail compose link and open it in the default browser: `run_command('open \"https://mail.google.com/mail/?view=cm&fs=1&to=RECIPIENT&su=SUBJECT&body=BODY\"')` (make sure BODY is URL-encoded, replacing spaces with %20 and newlines with %0D%0A to keep the email structure perfectly formatted!). Alternatively, use `open \"mailto:recipient?subject=...&body=...\"`."
        "6. CONTACT BOOK INTEGRATION (CRITICAL): If the user asks to send an email to a contact by name (e.g., 'Gokul', 'Revathi', 'Sandy', 'Dhanush'), you MUST first lookup their email address using the `search_contact` tool! "
        "- If `search_contact` returns a matching email, use it as the recipient in the Gmail compose link. "
        "- If `search_contact` returns no matches OR if they ask you to update/set a contact's email, do NOT try to guess or ask them to say it out loud (since email addresses are extremely hard to parse via speech). Instead, IMMEDIATELY call the `prompt_user_input` tool with a prompt like: 'Please type Sandy\'s email address in the terminal' to allow them to enter it comfortably via keyboard! Once they type it, call `add_contact` to save/update it, and then proceed to compose the mail!"
        "7. WRITING TO AN ACTIVE EMAIL (CRITICAL): If the user has already opened a Gmail compose window or compose tab (or if you just opened it) and wants you to write a message, subject, or content, do NOT use `run_command` with a new URL compose link (as that opens a new tab). Instead, use the `write_to_active_email` tool to focus their active compose body and paste the structured message directly inside the body section of that active window! This is much faster and cleaner than opening new tabs."

        "\nCONVERSATIONAL SPEED RULES (CRITICAL):\n"
        "- You speak in a highly conversational, short, and punchy manner. "
        "- NEVER output long lists, step-by-step instructions, code blocks, or recipes in your spoken response. Your spoken responses MUST be extremely brief (1 to 2 sentences maximum, under 25 words!). "
        "- If the user asks for information that contains lists, code, or long text (e.g., a cake recipe, code, system logs, web articles), do NOT read it out loud. Instead, write it to a beautifully formatted text file on the user's Desktop using `write_file` or a script, open the file using `run_command('open ~/Desktop/filename.txt')` (replacing filename with something relevant), and give a 1-sentence spoken summary like: 'I have compiled the full chocolate cake recipe to a text file on your Desktop and opened it for you!'\n"
        "Be highly competent, proactive, concise, and professional. Loopi never gives up—if a terminal command fails, think of another way to solve it."
    )
    
    try:
        # Initialize the persistent stateful chat session if it doesn't exist
        if chat_session is None:
            chat_session = genai_client.chats.create(
                model='gemini-3.1-flash-lite',
                config=types.GenerateContentConfig(
                    tools=tools,
                    temperature=0.7,
                    system_instruction=system_instruction
                )
            )
        
        # Send the message. Natively manages state, memory, and automatically executes tool calls!
        response = chat_session.send_message(prompt)
        
        if response.text:
            return response.text
        else:
            return "I performed the action, but have nothing to say."
            
    except Exception as e:
        print(f"LLM Error: {e}")
        return "I encountered an error while thinking."

def check_for_clap(audio_data):
    """Check if the audio data contains a loud spike (clap)."""
    # Convert byte data to numpy array
    audio_np = np.frombuffer(audio_data, dtype=np.int16)
    if len(audio_np) > 0:
        # Use max amplitude for transient spikes (like a clap) instead of RMS average
        max_amplitude = np.max(np.abs(audio_np))
        if max_amplitude > CLAP_THRESHOLD:
            return True
    return False

def main():
    global chat_session
    print("Initializing Loopi...")
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    
    # Adjust for ambient noise
    with mic as source:
        print("Calibrating for ambient noise... Please stay quiet for 2 seconds.")
        recognizer.adjust_for_ambient_noise(source, duration=2)
        print("Calibration complete.")
    
    # Increase pause threshold to 1.0 second so she gives you plenty of time to finish speaking without cutting you off
    recognizer.pause_threshold = 1.0
    
    print("\nLoopi is listening in the background.")
    print(f"Wake words: {WAKE_WORDS}")
    print("Or you can just clap loudly!")
    
    is_awake = False
    
    # We will use SpeechRecognition's listen method in a loop
    while True:
        try:
            with mic as source:
                if is_awake:
                    print("\n[Active Mode] Listening for your command...")
                    # Shorter timeout so she goes back to sleep if you walk away
                    try:
                        audio = recognizer.listen(source, timeout=10, phrase_time_limit=10)
                    except sr.WaitTimeoutError:
                        print("Silence timeout. Loopi going to sleep.")
                        speak("I am going to sleep now. Let me know if you need me.")
                        chat_session = None
                        is_awake = False
                        continue
                else:
                    print("\n[Sleeping Mode] Listening for wake word or clap...")
                    audio = recognizer.listen(source, timeout=None, phrase_time_limit=5)
            
            # 1. Check for clap in the raw audio data ONLY when sleeping!
            is_clap = False
            if not is_awake:
                is_clap = check_for_clap(audio.frame_data)
            
            if is_clap:
                print("Clap detected! Waking up...")
                is_awake = True
                speak("I'm here. What's on your mind?")
                continue
                
            # 2. Process speech
            try:
                text = recognizer.recognize_google(audio).lower()
                print(f"[Debug] Heard: {text}")
                
                if is_awake:
                    # Ignore extremely short incomplete phrases (filler words) to save API quota
                    words = text.strip().split()
                    if len(words) < 3 and text in ["can you", "what", "ok", "hello", "hey", "tell me", "please", "yes", "and then"]:
                        speak("I'm listening. Tell me what you'd like me to do.")
                        continue
                        
                    # Check for sleep command to manually put her to sleep
                    if any(cmd in text for cmd in ["go to sleep", "bye", "goodbye", "stop", "thank you", "thanks"]):
                        speak("You're welcome. Going to sleep now.")
                        chat_session = None
                        is_awake = False
                        continue
                    
                    # Process the actual command
                    print(f"User: {text}")
                    response = get_llm_response(text)
                    speak(response)
                else:
                    # If sleeping, check for wake word
                    if any(re.search(r'\b' + wake + r'\b', text) for wake in WAKE_WORDS):
                        print("Wake word detected!")
                        # Since the wake word was spoken, the command might be in the same text
                        command = text
                        for wake in WAKE_WORDS:
                            command = command.replace(wake, "").strip()
                        
                        is_awake = True
                        if command:
                            print(f"User: {command}")
                            response = get_llm_response(command)
                            speak(response)
                        else:
                            # Only said wake word, prompt for command
                            speak("Yes? I'm listening.")
                            
            except sr.UnknownValueError:
                # Couldn't understand audio, ignore
                pass
            except sr.RequestError as e:
                print(f"Could not request results from Google Speech Recognition; {e}")
                
        except KeyboardInterrupt:
            print("\nShutting down Loopi...")
            break
        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()
