import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load env vars just in case, but main.py should have handled it
load_dotenv()

# MODEL CONFIG
MODEL_NAME = "gemini-2.5-flash-lite"


def generate_response(newspaper_data: dict, chat_history: list, user_message: str):
    # 1. Initialize Client INSIDE the function
    # This ensures env vars are definitely loaded before we try to connect
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables")

    client = genai.Client(api_key=api_key)

    # 2. Clean the Data
    clean_context = {
        "newspaper_name": newspaper_data.get("newspaper_name"),
        "date": newspaper_data.get("date"),
        "data": {},
    }

    full_data = newspaper_data.get("full_json_data", {})
    if full_data:
        clean_data = full_data.copy()
        if "Markdown" in clean_data:
            del clean_data["Markdown"]
        clean_context["data"] = clean_data

    # 3. Define System Instruction
    sys_instruct = f"""
    You are an expert historical analyst assisting a user with the newspaper "{clean_context['newspaper_name']}" from {clean_context['date']}.

    DATA CONTEXT:
    The full text of the newspaper is provided in the structured data below.
    {str(clean_context)}

    YOUR CAPABILITIES:
    1. Summarize articles, analyze tone, and extract specific details.
    2. Answer meta-questions (e.g., "How many words?", "What is the longest article?") by analyzing the provided text.
    3. Maintain conversation context. If the user refers to "it" or "that article", refer to the previous topic discussed in the history.
    
    GUIDELINES:
    - Be concise but informative.
    - NEVER be brief unless explicitly asked to be.
    - If the user asks for a count (words, articles), estimate it based on the text provided.
    - If the answer is not in the newspaper, strictly state that the information is missing.
    """

    # 4. Format History
    formatted_history = []
    for msg in chat_history:
        role = "user" if msg["sender"] == "user" else "model"
        formatted_history.append(
            types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])])
        )

    # 5. Create Chat & Send
    chat = client.chats.create(
        model=MODEL_NAME,
        config=types.GenerateContentConfig(
            system_instruction=sys_instruct,
            temperature=0.7,  # Slightly higher creativity
            max_output_tokens=8192,  # <--- FORCE LONG ANSWERS
        ),
        history=formatted_history,
    )

    response = chat.send_message(user_message)

    return response.text