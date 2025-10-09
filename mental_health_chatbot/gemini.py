import os
from google import genai
from google.genai.errors import APIError

API_KEY = "AIzaSyA9tU4xbOTaLSloTwE-CgW6acK5jp4ZPec"

# 1. Initialize the Client and Start a Chat Session
try:
    # Pass the API key directly to the client
    client = genai.Client(api_key=API_KEY)

    # Use a fast model suitable for chat
    chat = client.chats.create(model='gemini-2.5-flash')

    # print("🤖 Gemini Chat Session Started!")
    # print("Model: gemini-2.5-flash")
    # print("Type 'quit' or 'exit' to end the conversation.")
    # print("-" * 40)

except APIError as e:
    print(f"❌ API Error during client initialization: {e}")
    print("Please check if your API key is valid and has not been revoked.")
    exit()
except Exception as e:
    print(f"❌ An unexpected error occurred: {e}")
    exit()


# 2. Main Chat Loop
def run_gemini_chat(u_input):
    """Handles the continuous user input and model response cycle."""
    chat_number = 1
    while True:
        try:
            user_input = u_input
            chat_number+=1

            # if user_input.lower() in ['quit', 'exit']:
            #     print("-" * 40)
            #     print("👋 Ending chat session. Goodbye!")
            #     break

            # Send the message. The chat object manages the history automatically.
            response = chat.send_message(user_input)

            # Print the model's response
            # print(f"🧠 Gemini: {response.text}")
            gemini_response = response.text
            return gemini_response

        except APIError as e:
            print(f"\n❌ API Request Failed: {e}")
            print("The conversation history might be too long, or there might be a network issue.")
            break
        except Exception as e:
            print(f"\n❌ An error occurred during the conversation: {e}")
            break


# # 3. Execute the Chat and Show History
# if 'client' in locals() and 'chat' in locals():
#     run_chat()

#     # Optional: Display the final conversation history
#     print("\n" + "=" * 20 + " Conversation History " + "=" * 20)
#     for message in chat.get_history():
#         role = "User" if message.role == "user" else "Gemini"
#         text = message.parts[0].text
#         print(f"[{role}]: {text}")
#     print("=" * 62)