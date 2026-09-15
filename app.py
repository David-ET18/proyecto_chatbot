import os
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# -----------------------------------------------------------------------
# Configuracion del modelo
# -----------------------------------------------------------------------
# Por defecto apunta a OpenRouter (modelos gratuitos, API compatible con OpenAI).
# Si luego usas la API oficial de OpenAI, solo cambia OPENAI_BASE_URL y
# OPENAI_MODEL en el archivo .env; el codigo no cambia.
API_KEY = os.getenv("OPENAI_API_KEY", "")
BASE_URL = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
MODEL = os.getenv("OPENAI_MODEL", "nvidia/nemotron-3.5-lightning:free")

# -----------------------------------------------------------------------
# Prompt Template (rol, contexto, tarea, restricciones, estilo)
# -----------------------------------------------------------------------
SYSTEM_PROMPT = """Eres un asistente experto en gastronomia peruana.

Contexto: Atiendes usuarios interesados en platos, ingredientes, preparacion \
y cultura gastronomica peruana.

Tarea: Responde las preguntas del usuario de manera clara y util.

Restricciones: No inventes informacion. Si no tienes informacion suficiente, \
indicalo explicitamente en vez de inventar datos.

Estilo: Lenguaje claro, amigable y apropiado para un usuario general. \
Evita tecnicismos innecesarios. Si es util, organiza la respuesta con \
listas breves."""

# -----------------------------------------------------------------------
# Interfaz
# -----------------------------------------------------------------------
st.set_page_config(page_title="Chef IA", page_icon="🇵🇪")
st.title("🇵🇪 Chef IA")
st.caption("Asistente de gastronomía peruana")

if not API_KEY:
    st.error(
        "⚠️ No se encontró OPENAI_API_KEY.\n\n"
        "1. Copia el archivo `.env.example` como `.env` (mismo nombre, sin '.example').\n"
        "2. Abre `.env` y pega tu clave real en OPENAI_API_KEY.\n"
        "3. Guarda el archivo y vuelve a ejecutar `streamlit run app.py`."
    )
    st.stop()

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

# Historial de conversacion persistente durante la sesion
if "mensajes" not in st.session_state:
    st.session_state.mensajes = []

# Mostrar historial existente
for m in st.session_state.mensajes:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Entrada del usuario
prompt = st.chat_input("Escribe tu pregunta sobre gastronomía peruana...")

if prompt:
    st.session_state.mensajes.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Se arma el mensaje de sistema + todo el historial para conservar contexto
    mensajes_api = [{"role": "system", "content": SYSTEM_PROMPT}] + st.session_state.mensajes

    with st.chat_message("assistant"):
        placeholder = st.empty()
        respuesta_completa = ""
        try:
            stream = client.chat.completions.create(
                model=MODEL,
                messages=mensajes_api,
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content or ""
                respuesta_completa += delta
                placeholder.markdown(respuesta_completa + "▌")
            placeholder.markdown(respuesta_completa)
        except Exception as e:
            error_str = str(e)
            if "404" in error_str and "unavailable for free" in error_str.lower():
                respuesta_completa = (
                    "⚠️ El modelo gratuito configurado ya no está disponible "
                    "(OpenRouter rota su lista de modelos gratis con frecuencia).\n\n"
                    "Ve a https://openrouter.ai/models?max_price=0, copia el ID de "
                    "otro modelo que termine en `:free`, y actualiza `OPENAI_MODEL` "
                    "en tu archivo `.env`."
                )
            else:
                respuesta_completa = (
                    f"Ocurrió un error al consultar el modelo: {e}\n\n"
                    "Verifica tu API key, el modelo configurado y tu conexión."
                )
            placeholder.markdown(respuesta_completa)

    st.session_state.mensajes.append({"role": "assistant", "content": respuesta_completa})

# -----------------------------------------------------------------------
# Barra lateral: info y utilidades
# -----------------------------------------------------------------------
with st.sidebar:
    st.header("Configuración")
    st.write(f"**Modelo actual:** `{MODEL}`")
    st.write(f"**Endpoint:** `{BASE_URL}`")
    if st.button("🗑️ Limpiar conversación"):
        st.session_state.mensajes = []
        st.rerun()

    st.divider()
    st.subheader("Preguntas de prueba sugeridas")
    st.markdown(
        "- ¿Qué es el ceviche?\n"
        "- ¿Qué ingredientes lleva?\n"
        "- ¿Cuál es un plato típico de Arequipa?\n"
        "- ¿Qué plato recomendarías para alguien que no puede comer picante?\n"
        "- ¿Qué ingredientes necesito para preparar una causa limeña?"
    )