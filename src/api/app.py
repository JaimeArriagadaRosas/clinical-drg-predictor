#!/usr/bin/env python3
import os, json, logging, time
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template_string, Response, stream_with_context
from src.api.gemini_api import GeminiClient
from src.api.feature_extractor import GRDFeatureExtractor
import pickle
import numpy as np
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(BASE_DIR, '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = Flask(__name__)
MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'models', 'best_model.pkl')
LABEL_ENCODER_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'dataset', 'processed', 'label_encoder.pkl')

def load_model():
    try:
        with open(MODEL_PATH, 'rb') as f: return pickle.load(f)
    except Exception as e:
        logger.error(f"Error modelo: {e}")
        return None

def load_label_encoder():
    try:
        with open(LABEL_ENCODER_PATH, 'rb') as f: return pickle.load(f)
    except Exception as e:
        logger.error(f"Error LE: {e}")
        return None

model = load_model()
label_encoder = load_label_encoder()
feature_extractor = GRDFeatureExtractor()

def predecir_grd(posibles_icd10: list, posibles_icd9: list = None, edad: int = None, sexo: str = None) -> dict:
    if not model or not label_encoder:
        return {"error": "Modelo no cargado"}
    feats = feature_extractor.create_features(icd10_codes=posibles_icd10, icd9_codes=posibles_icd9, edad_num=edad, sexo=sexo)
    vec = feature_extractor.features_to_vector(feats)
    pred = model.predict([vec])[0]
    proba = model.predict_proba([vec])[0]
    conf = proba.max()
    grd = str(label_encoder.inverse_transform([pred])[0])
    return {"grd_prediction": grd, "confidence": float(conf)}

system_instruction = (
    "Eres el Chatbot GRD, un asistente médico inteligente. "
    "Tu objetivo es conversar con el usuario, entender sus síntomas y predecir el Grupo Relacionado con Diagnóstico (GRD). "
    "Si el usuario solo saluda, devuélvele el saludo amablemente y pregúntale cuáles son sus síntomas. "
    "Cuando el usuario describa síntomas clínicos explícitos, actúa como experto en codificación médica: deduce los posibles códigos ICD-10 (y códigos ICD-9 si hay procedimientos) de esos síntomas, y llama a la herramienta 'predecir_grd' pasando explícitamente estas listas de códigos. "
    "Cuando la herramienta te devuelva la predicción, explícala al paciente de forma clara y profesional, sin mencionar los códigos internos."
)

gemini = GeminiClient(system_instruction=system_instruction, tools=[predecir_grd])
logger.info("Chatbot OK")

@app.route('/')
def index():
    h = '''<!DOCTYPE html><html><head><title>Chatbot GRD</title></head><style>
body{font-family:Arial,sans-serif;max-width:800px;margin:50px auto;padding:20px;background:#f4f7f6;}
h1 {color:#2c3e50; text-align:center;}
.chat-box{border:1px solid #dce4e6;border-radius:10px;height:450px;overflow-y:scroll;padding:20px;margin-bottom:20px;background:#ffffff;box-shadow:0 4px 6px rgba(0,0,0,0.05);}
.message{margin:15px 0;padding:12px 16px;border-radius:15px;line-height:1.5;max-width:80%;word-wrap:break-word;}
.user{background:#007bff;color:white;margin-left:auto;border-bottom-right-radius:2px;}
.bot{background:#e9ecef;color:#212529;margin-right:auto;border-bottom-left-radius:2px;white-space:pre-wrap;}
.pred{background:#fff3cd;border:1px solid #ffeaa7;padding:12px;margin:15px auto;border-radius:8px;font-size:0.95em;color:#856404;width:90%;text-align:center;}
.input-container{display:flex;gap:10px;}
input{flex:1;padding:12px;border:1px solid #ccc;border-radius:8px;font-size:16px;}
button{padding:12px 24px;background:#007bff;color:white;border:none;border-radius:8px;cursor:pointer;font-weight:bold;transition:0.2s;}
button:hover{background:#0056b3;}
button:disabled{background:#a0c4ff;cursor:not-allowed;}
.instructions{background:#e8f4fd;border:1px solid #bee5eb;padding:15px;margin-bottom:20px;border-radius:8px;font-size:14px;color:#0c5460;}
</style><body><h1>Chatbot Médico GRD</h1>
<div class="instructions"><strong>Instrucciones:</strong> Saluda al bot o describe tus síntomas clínicos directamente. La IA evaluará tu solicitud y llamará al modelo de predicción ML si es necesario.</div>
<div class="chat-box" id="chat"></div>
<div class="input-container"><input type="text" id="input" placeholder="Escribe aquí tu mensaje..." onkeypress="if(event.key==='Enter')send()"><button id="sendBtn" onclick="send()">Enviar</button></div>
<script>
const ch=document.getElementById('chat'); let messages=[];
function am(t,u){const d=document.createElement('div');d.className='message '+(u?'user':'bot');d.textContent=t;ch.appendChild(d);ch.scrollTop=ch.scrollHeight;return d;}
function ap(d){const p=document.createElement('div');p.className='pred';p.innerHTML='<b>Predicción ML:</b> GRD '+d.grd_prediction+'<br><b>Confianza:</b> '+(d.confidence*100).toFixed(1)+'%';ch.appendChild(p);ch.scrollTop=ch.scrollHeight;}
async function send(){const i=document.getElementById('input');const btn=document.getElementById('sendBtn');const t=i.value.trim();if(!t)return;am(t,true);messages.push({role:'user',content:t});i.value='';i.disabled=true;btn.disabled=true;const d=document.createElement('div');d.className='message bot';d.textContent='Analizando...';ch.appendChild(d);try{const s=await fetch('/chat_stream',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({messages})});const reader=s.body.getReader();const decoder=new TextDecoder();d.textContent='';let full_response='';let buffer='';while(true){const {done,value}=await reader.read();if(done)break;buffer+=decoder.decode(value,{stream:true});let boundary=buffer.indexOf('\n\n');while(boundary!==-1){let chunkStr=buffer.substring(0,boundary);buffer=buffer.substring(boundary+2);if(chunkStr.startsWith('data: ')){try{let data=JSON.parse(chunkStr.substring(6));if(data.type==='chunk'){d.textContent+=data.text;full_response+=data.text;}else if(data.type==='prediction'){ap(data);ch.appendChild(d);}else if(data.type==='error'){d.textContent='Error: '+data.text;}}catch(err){console.error(err);}}boundary=buffer.indexOf('\n\n');}}messages.push({role:'model',content:full_response});}catch(e){d.textContent='Error en la conexión.';}finally{i.disabled=false;btn.disabled=false;i.focus();}}
</script></body></html>'''
    return render_template_string(h)

@app.route('/health')
def health():
    return jsonify({'status':'ok','model':model is not None,'gemini':gemini.available})

@app.route('/chat_stream', methods=['POST'])
def chat_stream():
    data = request.json
    messages = data.get('messages', [])
    if not messages:
        return jsonify({'error':'No messages'}), 400

    def generate():
        try:
            if not gemini.available:
                yield f"data: {json.dumps({'type':'error','text':'Gemini no disponible'})}\n\n"
                return
            history = gemini._validate_history(messages[:-1])
            last_msg = messages[-1].get('content', '')
            chat = gemini.model.start_chat(history=history)
            max_retries = 5
            retry_delay = 5

            def _execute_chat():
                response_stream = chat.send_message(last_msg, stream=True)
                fn_call = None
                for chunk in response_stream:
                    if chunk.parts and getattr(chunk.parts[0], 'function_call', None):
                        fn_call = chunk.parts[0].function_call
                    elif getattr(chunk, 'text', None):
                        yield f"data: {json.dumps({'type':'chunk','text':chunk.text})}\n\n"
                if fn_call and fn_call.name == 'predecir_grd':
                    args = dict(fn_call.args) if hasattr(fn_call.args, 'items') else {}
                    result = predecir_grd(args.get('posibles_icd10', []), args.get('posibles_icd9', []), args.get('edad'), args.get('sexo'))
                    yield f"data: {json.dumps({'type':'prediction','grd_prediction':result.get('grd_prediction',''),'confidence':result.get('confidence',0)})}\n\n"
                    response_stream2 = chat.send_message(genai.protos.Part(function_response=genai.protos.FunctionResponse(name=fn_call.name,response={"result":result})), stream=True)
                    for chunk2 in response_stream2:
                        if getattr(chunk2, 'text', None):
                            yield f"data: {json.dumps({'type':'chunk','text':chunk2.text})}\n\n"
                yield f"data: {json.dumps({'type':'done'})}\n\n"

            for attempt in range(max_retries):
                try:
                    yield from _execute_chat()
                    break
                except ResourceExhausted:
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        retry_delay *= 2
                    else:
                        yield f"data: {json.dumps({'type':'error','text':'Límite de peticiones alcanzado.'})}\n\n"
                except Exception as e:
                    logger.error(f"Error en chat: {e}")
                    yield f"data: {json.dumps({'type':'error','text':str(e)[:100]})}\n\n"
                    break
        except Exception as e:
            logger.error(f"Error general: {e}")
            yield f"data: {json.dumps({'type':'error','text':str(e)[:100]})}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')

if __name__=='__main__':
    print("Chatbot GRD con Streaming y Function Calling http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
