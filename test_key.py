import google.generativeai as genai

# I removed the colon from the end of your string below:
NEW_KEY = "AIzaSyASORZJjsXwpnxpd4iYP2BMk71ulqLJnQc" 

print(f"🔑 Testing Key: ...{NEW_KEY[-6:]}")

try:
    genai.configure(api_key=NEW_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash-lite")
    response = model.generate_content("Are you online?")
    print(f"✅ SUCCESS! Response: {response.text}")
except Exception as e:
    print(f"❌ FAIL: {e}")