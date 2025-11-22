import os
from dotenv import load_dotenv
from openai import OpenAI

# 1. Load the secret password from .env
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

# CHECK: Did we actually find the key?
print("------------------------------------------------")
if not api_key:
    print("❌ ERROR: Could not find GROQ_API_KEY in .env file.")
    print("Please check your .env file name and content.")
    exit() # Stop the program
else:
    print(f"✅ Success: Found API Key! (Starts with: {api_key[:5]}...)")
print("------------------------------------------------")

# 2. Setup the Client (Connect to Groq)
try:
    client = OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=api_key
    )
    print("📡 Connecting to Groq Server...")
except Exception as e:
    print(f"❌ ERROR: Client setup failed. {e}")
    exit()

# 3. Send a test message
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Say 'The Backend is working!' if you can hear me."}
]

print("🧠 Sending message to AI...")

try:
    completion = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=messages
    )
    
    # 4. Print the result
    response = completion.choices[0].message.content
    print("\n🎉 AI RESPONSE:")
    print(response)
    print("\n------------------------------------------------")

except Exception as e:
    print(f"\n❌ CRITICAL ERROR: {e}")
    print("Common causes:")
    print("1. Your API Key is invalid.")
    print("2. Your internet is blocking the connection.")