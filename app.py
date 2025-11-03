# app.py (Versión 16.1 - Flujo de Dos Pasos con API Corregida)
# -----------------------------------------------------------------

import streamlit as st
import pandas as pd
from pdfminer.high_level import extract_text
import re
import io
import json

# --- Bloque 1: Configuración de la IA de Google Gemini ---
try:
    import google.generativeai as genai
    from google.api_core.exceptions import ResourceExhausted 
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"]) 
    IA_DISPONIBLE = True
except (ImportError, KeyError):
    IA_DISPONIBLE = False
except Exception as e:
    st.error(f"Error al configurar la API de Google: {e}")
    IA_DISPONIBLE = False

# --- Bloque 2: Las funciones del "Cerebro" ---

def extraer_datos_certificados_V8(texto_pdf):
    # (Función de reglas sin cambios)
    datos = { "vencimiento_fc": None, "valor_retencion": None, "tipo_retencion": None, "nro_certificado": None, "fecha_certificado": None }
    lines = [line.strip() for line in texto_pdf.split('\n') if line.strip()]
    for i, line in enumerate(lines):
        if "cert de reten ganancias" in line.lower():
            datos["tipo_retencion"] = "Retenciones Ganancias"; 
            if i + 1 < len(lines): match = re.search(r'(\d{4}-\d{8})', lines[i+1]); 
            if match: datos["nro_certificado"] = match.group(1)
        elif "cert de reten ingr.brutos" in line.lower():
            datos["tipo_retencion"] = "Retenciones ingresos brutos"; 
            if i + 1 < len(lines): match = re.search(r'(\d{4}-\d{8})', lines[i+1]); 
            if match: datos["nro_certificado"] = match.group(1)
        if "rg.830" in line.lower() or "retención iibb" in line.lower():
            for j in range(i + 1, min(i + 5, len(lines))):
                match = re.search(r'([\d\.,]+)', lines[j])
                if match and len(match.group(1)) > 3:
                    valor_limpio = match.group(1).replace('.', '').replace(',', '.'); datos["valor_retencion"] = float(valor_limpio); break
    match = re.search(r"Comprobante/s que origina/n la retención:\s*(\d{2}/\d{2}/\d{4})", texto_pdf, re.IGNORECASE); 
    if match: datos["vencimiento_fc"] = match.group(1).strip()
    match = re.search(r"Fecha:\s*(\d{2}/\d{2}/\d{4})", texto_pdf); 
    if match: datos["fecha_certificado"] = match.group(1).strip()
    return datos

def extraer_datos_con_ia_google(texto_pdf):
    if not IA_DISPONIBLE: return None
    prompt = f"""
    Eres un experto asistente contable. Analiza el siguiente texto y devuelve ÚNICAMENTE un objeto JSON con la siguiente estructura:
    - vencimiento_fc: Fecha del "Comprobante que origina la retención" en formato "dd/mm/yyyy".
    - valor_retencion: Importe de la retención como un número flotante.
    - nro_certificado: Número del certificado.
    - fecha_certificado: Fecha de emisión del certificado en formato "dd/mm/yyyy".
    - tipo_retencion: Debe ser "Retenciones Ganancias" o "Retenciones ingresos brutos".
    Si un dato no se encuentra, devuélvelo como `null`. No incluyas explicaciones.
    Texto del PDF: --- {texto_pdf} ---
    """
    try:
        generation_config = genai.GenerationConfig(response_mime_type="application/json")
        # --- APLICANDO REGLA MANDATORIA ---
        model = genai.GenerativeModel('gemini-2.5-flash-preview-09-2025', generation_config=generation_config)
        response = model.generate_content(prompt)
        return json.loads(response.text)
    except Exception as e:
        st.error(f"Error en API de Google (Certificado): {e}"); return None

def extraer_datos_op(texto_pdf):
    datos = { "orden_pago": None, "vencimiento_fc": None }
    match = re.search(r"Orden de pago:\s*(\d{5}-\d{8})", texto_pdf, re.IGNORECASE)
    if match: datos["orden_pago"] = match.group(1).strip()
    match = re.search(r"(\d{2}/\d{2}/\d{4})\s+FC", texto_pdf, re.IGNORECASE); 
    if match: datos["vencimiento_fc"] = match.group(1).strip()
    return datos

def extraer_datos_op_con_ia(texto_pdf):
    if not IA_DISPONIBLE: return None
    prompt = f"""
    Eres un experto asistente contable. Analiza un texto de una Orden de Pago y devuelve ÚNICAMENTE un objeto JSON con:
    - orden_pago: El número de la "Orden de pago".
    - vencimiento_fc: La fecha de la factura principal que se está pagando, en formato "dd/mm/yyyy".
    Texto del PDF: --- {texto_pdf} ---
    """
    try:
        generation_config = genai.GenerationConfig(response_mime_type="application/json")
        # --- APLICANDO REGLA MANDATORIA ---
        model = genai.GenerativeModel('gemini-2.5-flash-preview-09-2025', generation_config=generation_config)
        response = model.generate_content(prompt)
        return json.loads(response.text)
    except Exception as e:
        st.error(f"Error en API de Google (Orden de Pago): {e}"); return None

# --- Bloque 3: Interfaz de Usuario con Flujo de Dos Pasos ---
st.set_page_config(layout="wide", page_title="Automatización de Retenciones")
st.title("🤖 Prototipo de Carga Guiada (V16.1)")

# --- PASO 1: Carga y Procesamiento de Certificados ---
st.header("Paso 1: Procesar Certificados de Retención")
uploaded_files_step1 = st.file_uploader(
    "Sube aquí el archivo Excel y los PDFs de Certificados (Ganancias/IIBB)",
    accept_multiple_files=True,
    type=['pdf', 'xlsx'],
    key="uploader_step1"
)

if st.button("🚀 Paso 1: Procesar Certificados", key="button_step1"):
    excel_file = next((f for f in uploaded_files_step1 if f.name.endswith('.xlsx')), None)
    pdf_files = [f for f in uploaded_files_step1 if f.name.endswith('.pdf')]
    
    if excel_file and pdf_files:
        with st.spinner("Procesando Certificados..."):
            df = pd.read_excel(excel_file)
            df.columns = df.columns.str.strip()
            df['Vencimiento FC'] = pd.to_datetime(df['Vencimiento FC'], errors='coerce').dt.strftime('%d/%m/%Y')
            
            for pdf_file in pdf_files:
                texto = extract_text(pdf_file)
                if "cert de reten" in texto.lower():
                    datos_pdf = extraer_datos_certificados_V8(texto)
                    datos_faltantes = datos_pdf.get("valor_retencion") is None or datos_pdf.get("nro_certificado") is None
                    if datos_faltantes and IA_DISPONIBLE:
                        datos_ia = extraer_datos_con_ia_google(texto)
                        if datos_ia: datos_pdf.update({k: v for k, v in datos_ia.items() if v is not None})
                    
                    for index, row in df.iterrows():
                        if (datos_pdf.get('vencimiento_fc') == row['Vencimiento FC'] and 
                            datos_pdf.get('tipo_retencion') == row['Type of retention']):
                            df.loc[index, 'Valor de la retencion'] = datos_pdf.get("valor_retencion")
                            df.loc[index, 'Certificado de retencion Nro'] = datos_pdf.get("nro_certificado")
                            df.loc[index, 'Fecha del certificado de retencion'] = datos_pdf.get("fecha_certificado")
            
            st.session_state.processed_df = df
            st.success("Paso 1 completado. La tabla de retenciones está lista.")
    else:
        st.error("Por favor, sube al menos un archivo Excel y un PDF de certificado.")

# --- PASO 2: Carga y Agregado de Órdenes de Pago ---
if 'processed_df' in st.session_state:
    st.header("Paso 2: Agregar Órdenes de Pago")
    st.write("Resultado intermedio (Retenciones procesadas):")
    st.dataframe(st.session_state.processed_df)
    
    uploaded_files_step2 = st.file_uploader(
        "Sube aquí los PDFs de las Órdenes de Pago",
        accept_multiple_files=True,
        type=['pdf'],
        key="uploader_step2"
    )
    
    if st.button("➕ Paso 2: Agregar Órdenes de Pago", key="button_step2"):
        if uploaded_files_step2:
            with st.spinner("Agregando Órdenes de Pago..."):
                df = st.session_state.processed_df.copy()
                
                for pdf_file in uploaded_files_step2:
                    texto = extract_text(pdf_file)
                    if "orden de pago" in texto.lower():
                        datos_pdf = extraer_datos_op(texto)
                        if (datos_pdf.get("orden_pago") is None or datos_pdf.get("vencimiento_fc") is None) and IA_DISPONIBLE:
                            datos_ia = extraer_datos_op_con_ia(texto)
                            if datos_ia: datos_pdf.update({k: v for k, v in datos_ia.items() if v is not None})
                        
                        if datos_pdf.get("vencimiento_fc"):
                            df.loc[df['Vencimiento FC'] == datos_pdf.get("vencimiento_fc"), 'Orden de Pago'] = datos_pdf.get("orden_pago")
                
                st.session_state.processed_df = df
                st.success("Paso 2 completado. El Excel final está listo.")
        else:
            st.error("Por favor, sube al menos un PDF de Orden de Pago.")

# --- BLOQUE FINAL: Muestra de Resultados y Descarga ---
if 'processed_df' in st.session_state:
    st.header("✅ Resultados Finales")
    st.info("Puedes editar la tabla antes de descargar.")
    
    df_editado = st.data_editor(st.session_state.processed_df, num_rows="dynamic", key="data_editor", height=400)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_editado.to_excel(writer, index=False, sheet_name='Resultados')
    
    st.download_button( "📥 Descargar Excel Completado", output.getvalue(), "resultado_retenciones.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")