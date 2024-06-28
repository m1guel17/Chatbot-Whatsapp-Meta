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
    texto = db.Column(db.TEXT, default="x")
    number = db.Column(db.TEXT, default="x")
    dni = db.Column(db.TEXT, default="x")
    nombre = db.Column(db.TEXT, default="x")
    cliente = db.Column(db.TEXT, default="x")
    sucursal = db.Column(db.TEXT, default="x")
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

def check_flow(texto, number, dni, nombre, cliente, sucursal, flow = 0):
    check = db.session.query(Log).filter_by(number=number).order_by(Log.fecha_y_hora.desc()).first()
    if check:
        try:
            if int(dni) and len(dni) == 8:
                check.flow = check.flow + 1
                check.dni = dni
                db.session.commit()
        except Exception as e:
            check.flow = check.flow
            db.session.commit()
    else: 
        nuevo_registro = Log(number = number, flow = flow) # Guardar el mensaje en la base de datos
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
                        send_wsp(texto, numero)
                    
                    elif tipo_interactivo == "list_reply":
                        texto = messages["interactive"]["list_reply"]["id"]
                        numero = messages["from"]
                        send_wsp(texto, numero)
                if "text" in messages:
                    texto = messages["text"]["body"]
                    numero = messages["from"]
                    check_flow(texto, numero, texto, texto, texto, texto)  #Guardar log en base de datos
                    
                    flowx = db.session.query(Log).filter_by(number=numero).order_by(Log.fecha_y_hora.desc()).first()
                    latest_log = flowx.flow
                    
                    send_wsp(texto, numero, latest_log)
        
        return jsonify({'message':'EVENT_RECEIVED'})
    except Exception as e:
        return jsonify({'message':'EVENT_RECEIVED'})

def send_wsp(texto, numero, flow):
    texto = texto.lower()
    
    match flow:
        case 0:
            if "hola" in texto:
                data = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": numero,
                    "text": {
                        "preview_url": False,
                        "body": "Hola Te Saluda Robotín, asistente de G4S (...) \n para ayudarte mejor dame tu DNI: "
                    }
                }
        case 1:
            if int(texto) and len(texto) == 8:
                data = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": numero,
                    "text": {
                        "preview_url": False,
                        "body": "Así mismo dame tu nombre"
                    }
                }
            else:
                data = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": numero,
                    "text": {
                        "preview_url": False,
                        "body": "Parece que tu DNI no es válido pusiste: "+ texto
                    }
                }
        case 2:
            if texto:
                data = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": numero,
                    "text": {
                        "preview_url": False,
                        "body": " #nombre un gusto, dame tu cliente: "
                    }
                }
        case 3:
            if texto:
                data = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": numero,
                    "text": {
                        "preview_url": False,
                        "body": " finalmente tu sucursal "
                    }
                }
        case 4:
            if texto:
                data = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": numero,
                    "text": {
                        "preview_url": False,
                        "body": " Perfecto"
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
        check_flow(json.dumps(e), numero)
    finally:
        connection.close()


if __name__=='__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
    #app.run(debug=True)

# Commands to push to production
# git add .
# git commit -m "xxx"
# git push