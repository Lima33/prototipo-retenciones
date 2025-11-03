import google.generativeai as genai
import os

# --- Pega tu clave directamente aquí ---
YOUR_API_KEY = "AIzaSyC_lfPzIsTIebV39tiEkRuwh0KgdCK7Q0o"
# ------------------------------------------

try:
    genai.configure(api_key=YOUR_API_KEY)

    print(f"Buscando modelos disponibles para tu API Key...")
    print("=============================================")

    # Esto intentará listar todos los modelos que tu clave puede ver
    for m in genai.list_models():
        print(m.name)

    print("=============================================")
    print("--- Fin de la lista ---")

except Exception as e:
    print(f"!!!!!!!!!! ERROR !!!!!!!!!!!")
    print(f"Ocurrió un error: {e}")
    print("---------------------------")