from openai import OpenAI
import time
from pygame import mixer
import os
from googlesearch import search

# Put your API key here with 'OpenAI(api_key="key_here")'
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
mixer.init()

# This is the memory maintainer where we add instructions
conversation_history = [
    {
        "role": "system",
        "content": (
            "You are an assistant named Jarvis. Keep your responses short yet human, don't be robotic. "
            "You can execute commands. Only ever execute these commands upon given explicit instruction from the user. "
            "Here are the commands:\n\n"
            "* #lights-1/0 - this command triggers the lights, 1 meaning on while 0 means off.\n"
            "* {google} - whenever a user asks for something relative to real-time information, you reply with: '{google} (summarized query)'. You will then get a set of results, which you have to interpret and tell the user in natural language \n\n"
            "It is imperative that you end your sentence with these triggers and do not say anything after them. "
            "The hashtag is the trigger character, and whatever is after the tag is the command to be triggered."
        )
    }
]

def perform_web_search(query, num_results=3):
    try:
        results = list(search(query, num_results=num_results, advanced=True))
        return [{'title': r.title, 'description': r.description, 'url': r.url} for r in results]
    except Exception as e:
        print(f"Error performing web search: {e}")
        return []

def process_response(response):
    if response.startswith("{google}"):
        search_query = response[8:].strip()
        print(f"Performing web search for: {search_query}")
        search_results = perform_web_search(search_query)

        if search_results:
            search_info = "\n".join(
                [f"Title: {r['title']}\nDescription: {r['description']}" for r in search_results]
            )
            follow_up_message = (
                f"Here are the search results for '{search_query}':\n\n{search_info}\n\n"
                "Please provide a response based on this information."
            )
            return ask_question_memory(follow_up_message)
        else:
            return f"I'm sorry, but I couldn't find any relevant search results for '{search_query}'."
    else:
        return response

def ask_question_memory(question):
    try:
        conversation_history.append({"role": "user", "content": question})
        
        # Set your preferred base model settings below
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=conversation_history,
            temperature=0.5,
            max_tokens=8192,
            top_p=0.9,
            frequency_penalty=0,
            presence_penalty=0,
            response_format={"type": "text"}
        )

        ai_response = response.choices[0].message.content
        conversation_history.append({"role": "assistant", "content": ai_response})
        processed_response = process_response(ai_response)
        return processed_response
    except Exception as e:
        return f"An error occurred: {e}"

def generate_tts(sentence, speech_file_path):
    response = client.audio.speech.create(model="tts-1", voice="echo", input=sentence)
    response.stream_to_file(speech_file_path)
    return str(speech_file_path)

def play_sound(file_path):
    mixer.music.load(file_path)
    mixer.music.play()

def TTS(text):
    speech_file_path = generate_tts(text, "speech.mp3")
    play_sound(speech_file_path)
    while mixer.music.get_busy():
        time.sleep(1)
    mixer.music.unload()
    os.remove(speech_file_path)
    return "done"

if __name__ == "__main__":
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            break
        response = ask_question_memory(user_input)
        print("Assistant:", response)
        TTS(response)
