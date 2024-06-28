from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import http.client

app = Flask(__name__)

#Configuración de la base de datos SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///metapython.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Modelo de la tabla log
class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha_y_hora = db.Column(db.DateTime, default = datetime.utcnow)
    texto = db.Column(db.TEXT)
    number = db.Column(db.TEXT)
    flow = db.Column(db.Integer, default=0)

with app.app_context():   # Crear la tabla si no existe
    db.create_all()

def ordenar_por_fecha_y_hora(registros):
    return sorted(registros, key = lambda x: x.fecha_y_hora, reverse = True)

@app.route('/')

def index(): #ORDENAR LISTA
    registros = Log.query.all()
    registros_ordenados = ordenar_por_fecha_y_hora(registros)
    return render_template('index.html', registros=registros_ordenados);

# Función para agregar mensajes y guardar en la base de datos
def sen2db(texto, number, flow = 0):
    nuevo_registro = Log(texto = texto, number = number, flow = flow) # Guardar el mensaje en la base de datos
    db.session.add(nuevo_registro)
    db.session.commit()

TOKEN = "TOKENX"

@app.route('/webhook', methods=['GET','POST'])

def webhook():
    if request.method == 'GET':
        challenge = verificar_token(request)
        return challenge
    elif request.method == 'POST':
        response = recibir_mensajes(request)
        return response

def verificar_token(req):
    token = req.args.get('hub.verify_token')
    challenge = req.args.get('hub.challenge')
    if challenge and token == TOKEN:
        return challenge
    else:
        return jsonify({'error':'Token Invalido'}),401

def get_flow(numero):
    latest_log = db.session.query(Log).filter_by(number = numero).order_by(Log.fecha_y_hora.desc()).first()
    return latest_log.flow

def recibir_mensajes(req):
    try:
        req = request.get_json()
        entry = req['entry'][0]
        changes = entry['changes'][0]
        value = changes['value']
        objeto_mensaje = value['messages']

        if objeto_mensaje:
            messages = objeto_mensaje[0]
            
            if  "type" in messages:
                tipo = messages["type"]                
                if tipo == "interactive":
                    tipo_interactivo  = messages["interactive"]["type"]
                    
                    if tipo_interactivo == "button_reply":
                        texto = messages["interactive"]["button_reply"]["id"]
                        numero = messages["from"]
                        flowx = get_flow(numero)
                        send_wsp(texto, numero, flowx)
                    
                    elif tipo_interactivo == "list_reply":
                        texto = messages["interactive"]["list_reply"]["id"]
                        numero = messages["from"]
                        flowx = get_flow(numero)
                        send_wsp(texto, numero, flowx)

                if "text" in messages:
                    texto = messages["text"]["body"]
                    numero = messages["from"]
                    flowx = get_flow(numero)
                    send_wsp(texto, numero, flowx)
            
            sen2db(json.dumps(messages), numero)  #Guardar log en base de datos
        
        return jsonify({'message':'EVENT_RECEIVED'})
    except Exception as e:
        return jsonify({'message':'EVENT_RECEIVED'})

def send_wsp(texto, numero, flow):
    texto = texto.lower()
    flowx = flow
    
    data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": numero,
            "text": {
                    "preview_url": False,
                    "body": "Danasaoa" + str(flowx)
                    }
            }
    sen2db(texto, numero, 1)
    
    match flowx:
        case 0:
            if "hola" in texto:
                data = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": numero,
                    "text": {
                        "preview_url": False,
                        "body": "🤖 Hola, Washa. dame tu dni"
                    }
                }
                sen2db(texto, numero, 1)
        
        case 1:
            if int(texto) and len(texto) == 8:
                data = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": numero,
                    "text": {
                        "preview_url": False,
                        "body": "bien tu dni es" + texto
                    }
                }
                sen2db(texto, numero, 2)
            else:
                data = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": numero,
                    "text": {
                        "preview_url": False,
                        "body": "Tu dni no es correcto, pusiste" + texto + "serio pe cholo. Escribe nuevamente tu dni"
                    }
                }
                sen2db(texto, numero, 1)
    sen2db(texto, numero, flowx)
    data = json.dumps(data) # Convertir el diccionario en formato JSON

    headers = {
        "Content-Type" : "application/json",
        "Authorization" : "EAAOdZCMIRR5IBO4JHRJASC5ux6aPT4z0xQycPx319k1nApsZCZCWRhLK4vn25Sw7VO5CZBvwKiIMgJrqYDjZAZBDh5yYRlBJQo6AAiZACMFO3bYm8DfLLHgflOCQoAs9OzlgpZBCN3rrBnT4IoqfrkgEW0TbjLnjiUPGhWPt7nBmbFA9QZAOOqQvzapdc07OLvRfI9r8LGlU3RynZCIAnuZCvMZD"
    }
    connection = http.client.HTTPSConnection("graph.facebook.com")

    try:
        connection.request("POST","/v19.0/378273298696469/messages", data, headers)
        response = connection.getresponse()
        print(response.status, response.reason)
    except Exception as e:
        sen2db(json.dumps(e), "")
    finally:
        connection.close()


if __name__=='__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
    #app.run(debug=True)

# Commands to push to production
# git add .
# git commit -m "xxx"
# git push