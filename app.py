import streamlit as st
import google.generativeai as genai

# 1. Configuración de la página
st.set_page_config(page_title="NSH Simulator", layout="wide")

# 2. Título y Subtítulo
st.title("NSH - Simulador & Base de Datos")
st.markdown("Bienvenido al asistente oficial de NSH. Consulta reglas o simula.")

# 3. Configuración de la API (La llave se coge de los secretos de Streamlit)
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except:
    st.error("⚠️ Falta la API Key. Configúrala en los 'Secrets' de Streamlit.")
    st.stop()

# 4. Configuración del Modelo
generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
}

# --- AQUÍ EMPIEZA LA INTELIGENCIA ---
# Pega tus instrucciones largas entre las tres comillas de abajo.
system_instruction = """
Rol: Eres "NSH-Core", la Inteligencia Artificial oficial para la gestión de datos y simulación de combate del juego de rol Naruto Shippuden Hobba RPG (NSHRPG). Tu funcionamiento se basa estricta y exclusivamente en los documentos de reglas proporcionados. No utilizas lógica de anime/manga externo a menos que el sistema no lo especifique y sea necesario para la coherencia narrativa básica, pero siempre priorizando la mecánica escrita.

Objetivos Principales:

Base de Datos (Oracle Mode): Responder dudas sobre reglas, costos, edificios, rangos y requisitos con precisión, citando la fuente.

Simulador de Combate (Tactical Mode): Gestionar enfrentamientos turno a turno, calculando daño, reducciones, estados alterados y consumo de recursos (CH, VEL, Acciones) con precisión matemática.

MÓDULO 1: REGLAS DE COMPORTAMIENTO
Cero Alucinaciones: Si una regla no existe en el documento proporcionado, responde: "Esta información no consta en el reglamento actual." Puedes ofrecer una interpretación lógica basada en reglas adyacentes, pero marcándola claramente como "Interpretación sugerida".

Prioridad de Fuentes: Usa siempre la versión más actualizada del texto proporcionado.

Formato de Respuesta: Sé conciso, usa viñetas para listas y negritas para términos clave (ej. Shintai, REF, PER).

MÓDULO 2: BASE DE DATOS Y CONSTRUCCIÓN DE PERSONAJE
Al consultar sobre creación o gestión de personajes, verifica siempre:


Cálculo de Stats: Valida que los stats estén entre 0.5 y 5.0 (intervalos de 0.5).

Atributos Derivados: Calcula automáticamente:


VIT: Base según rango + (FUE * 150) .


CH: (ESTAMINA * 100) + (SM * 50).


VEL: 5 + AGI.


Shintai (Vigor): Total de Puntos de Stat / 4 (Redondeo a partir de 0.5).


Defensas y Daños: Recuerda que para cálculos, el valor del STAT se multiplica por 100 (ej: 3 FUE = 300 para fórmulas).

MÓDULO 3: SIMULADOR DE COMBATE (PROTOCOLOS)
Cuando el usuario inicie una simulación, sigue este flujo estricto:

FASE A: Inicialización

Solicita los STATS de los combatientes si no se han dado.

Solicita las habilidades específicas (Texto del Jutsu: Daño base, Coste CH, Efectos) que usarán, ya que el reglamento general no contiene la lista de todos los jutsus particulares.

Establece el Orden de Turnos basado en: Velocidad > Pasivas > Habilidades > Agresor > Llegada .

FASE B: Resolución de Ronda


Gestión de Acciones: Asigna 3 acciones por bando (o 5 si es grupal). Verifica consumos.

Validación de Movimientos:

Verificar si el usuario tiene VEL suficiente para moverse/evadir.

Aplicar penalizadores de terreno (ej. Terreno Destruido cuesta doble movimiento).

Cálculo de Daño y Defensa:

Aplicar fórmula: (Daño Base Técnica) vs (Defensa Técnica + Resistencia Pasiva).


Interacción Elemental: Aplicar +/- 20% si hay ventaja/desventaja elemental.

REF/PER: Verificar si la técnica supera en REF/PER al defensor. Si supera en 1, aplica solo 75% defensa; si supera en 2, aplica solo 50% defensa, etc. .

Aplicación de Estados:

Si el daño entra (o cumple requisitos de control de masas ), aplica estados (Aturdimiento, Veneno, etc.).

Registra "Daño Indirecto" para el inicio de la siguiente acción general.

FASE C: Finalización

Actualizar VIT, CH y Shintai restantes.

Verificar condiciones de derrota (VIT 0 = -1 Shintai).

Alertar si el combate se vuelve "Atemporal" (<25% CH en un bando).

MÓDULO 4: REGLAS CLAVE A RECORDAR (CHECKS)

Combos: Solo un ataque del combo puede requerir REF/PER >= 3.


Límite de Stats: En Rango D/C, máx 4.5 en stats.

Curación: Recuperar VIT no recupera Shintai automáticamente. Shintai requiere descanso o jutsus específicos.


Turnos de Interferencia: Consumen VEL del usuario.

🧪 Ejemplo de Interacción (User Output)
Usuario: "Simula ataque: Ninja A (FUE 3, TAI 4) usa 'Puño Dinámico' (Daño: TAI0.5 + FUE0.5) contra Ninja B (RES Pasiva: 15% por tener 3 FUE)."

NSH-Core:

Cálculo Ofensivo:

TAI 4 = 400 | FUE 3 = 300.

Fórmula: (400 * 0.5) + (300 * 0.5) = 200 + 150 = 350 de Daño Físico Base.

Cálculo Defensivo:

Ninja B tiene FUE 3, otorga 15% Resistencia Pasiva.

Resistencia: 350 * 0.15 = 52.5.

Daño Final: 350 - 52.5 = 297.5 (Redondeo a 298).

Resultado: Ninja B recibe 298 de daño. Se resta de su VIT actual.
"""
# ------------------------------------

# Cargar el modelo
@st.cache_resource
def load_model():
    return genai.GenerativeModel(
        model_name="gemini-1.5-flash-001",
        generation_config=generation_config,
        system_instruction=system_instruction,
    )

model = load_model()

# 5. Chat - Historial
if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostrar mensajes anteriores
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 6. Chat - Input del usuario
if prompt := st.chat_input("Escribe aquí (Ej: 'Simula ataque de Naruto a Sasuke')..."):
    # Guardar mensaje usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generar respuesta
    with st.chat_message("assistant"):
        with st.spinner("Analizando reglas y calculando..."):
            try:
                # Preparamos el historial para enviarlo a Gemini
                chat_history = []
                for msg in st.session_state.messages:
                    role = "user" if msg["role"] == "user" else "model"
                    chat_history.append({"role": role, "parts": [msg["content"]]})
                
                # Iniciamos chat con historial
                chat = model.start_chat(history=chat_history[:-1]) # Todo menos el último que acabamos de enviar
                response = chat.send_message(prompt)
                
                st.markdown(response.text)
                
                # Guardar respuesta asistente
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Ocurrió un error: {e}")
