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

def index():
    registros = Log.query.all()
    registros_ordenados = ordenar_por_fecha_y_hora(registros)
    return render_template('index.html', registros=registros_ordenados);

mensajes_log = []
# Función para agregar mensajes y guardar en la base de datos
def agregar_mensajes_log(texto):
    mensajes_log.append(texto)
    nuevo_registro = Log(texto=texto) # Guardar el mensaje en la base de datos
    db.session.add(nuevo_registro)
    db.session.commit()
    
mensajes_log2 = []
number_log2 = []



# Token de verificación para la configuración
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

def agregar_txt_num_log(texto, number, flow = 1):
    mensajes_log2.append(texto)
    number_log2.append(number)
    nuevo_registro = Log(texto = texto, number = number, flow = flow) # Guardar el mensaje en la base de datos
    db.session.add(nuevo_registro)
    db.session.commit()

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
                        enviar_mensajes_wsp(texto, numero)
                    
                    elif tipo_interactivo == "list_reply":
                        texto = messages["interactive"]["list_reply"]["id"]
                        numero = messages["from"]
                        enviar_mensajes_wsp(texto, numero)
                    agregar_mensajes_log(json.dumps(messages))  #Guardar log en base de datos

                if "text" in messages:
                    texto = messages["text"]["body"]
                    numero = messages["from"]
                    enviar_mensajes_wsp(texto, numero)
                    agregar_txt_num_log(json.dumps(messages), numero)  #Guardar log en base de datos
        
        return jsonify({'message':'EVENT_RECEIVED'})
    except Exception as e:
        return jsonify({'message':'EVENT_RECEIVED'})

def enviar_mensajes_wsp(texto, numero):
    texto = texto.lower()

    if "hola" in texto:
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": numero,
            "text": {
                "preview_url": False,
                "body": "🤖 Hola, Washa."
            }
        }
    
    data = json.dumps(data) # Convertir el diccionario en formato JSON

    headers = {
        "Content-Type" : "application/json",
        "Authorization" : "Bearer EAAOdZCMIRR5IBOZBixtcILQQLVMkeH3UqUKu9rAKTZA0nCEpUePgoJLBYRv4ty7pxGzYGVe2A2jn5bl6XkRCXpHMQRNtTSNWjdKWxtZACtLj5w3mYM90Eq0rQp7CniRYhb71ZALgPH5tqVdErKKt7olPBzc3gS6RtBuDZA0xpwZCTsEM8qqyFwO3FJXr2kdiZAaYZArIWkPmJamsuykUIZBRQZD"
    }
    connection = http.client.HTTPSConnection("graph.facebook.com")

    try:
        connection.request("POST","/v19.0/378273298696469/messages", data, headers)
        response = connection.getresponse()
        print(response.status, response.reason)
    except Exception as e:
        agregar_mensajes_log(json.dumps(e))
    finally:
        connection.close()


if __name__=='__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
    #app.run(debug=True)

# Commands to push to production
# git add .
# git commit -m "xxx"
# git push