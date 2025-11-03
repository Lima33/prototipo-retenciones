import google.generativeai as genai
import os

# --- Pega tu clave de API aquí ---
YOUR_API_KEY = "AIzaSyC_lfPzIsTIebV39tiEkRuwh0KgdCK7Q0o"
# ------------------------------------------

try:
    print("Configurando API Key...")
    genai.configure(api_key=YOUR_API_KEY)
    
    # --- LÍNEA MODIFICADA ---
    print("Creando modelo (models/gemini-pro-latest)...")
    model = genai.GenerativeModel('models/gemini-pro-latest')
    # ----------------------
    
    print("Enviando prompt ('Hola')...")
    response = model.generate_content("Hola")
    
    print("--- RESPUESTA DE GEMINI ---")
    print(response.text)
    print("---------------------------")
    print("¡Éxito! La conexión funcionó.")

except Exception as e:
    print(f"!!!!!!!!!! ERROR !!!!!!!!!!!")
    print(f"Ocurrió un error: {e}")
    print("---------------------------")