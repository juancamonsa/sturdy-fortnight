#!/usr/bin/env python3
"""MisFlujos — Servidor para Render.com"""

import json, os, uuid
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data", "db.json")

DEFAULT = {
  "categorias":[
    {"id":"c1","nombre":"🏠 Casa","subs":["Crédito hipotecario","Internet","Netflix","Amazon","HBO","Youtube","Gemini","Claude","Otros"]},
    {"id":"c2","nombre":"🌿 Bienestar","subs":["Seguro de vida Juan","Seguro de vida Alex","Clases","Otros"]},
    {"id":"c3","nombre":"🍽️ Alimentación","subs":["Mercado","Domicilios","Otros"]},
    {"id":"c4","nombre":"💳 Créditos","subs":["Hipotecario Itaú","Banco de Bogotá Moto","Banco de Bogotá Carro","Otros"]},
    {"id":"c5","nombre":"👨‍👩‍👧 Familia","subs":["Luze","Nico","Alex","Otros"]},
    {"id":"c6","nombre":"🚗 Transporte","subs":["Gasolina","SOAT","Reparaciones","Peajes & Parqueaderos","Seguros","Otros"]},
    {"id":"c7","nombre":"💊 Salud","subs":["Citas Nico","Citas Alex","Citas Juan","Medicamentos","Otros"]},
    {"id":"c8","nombre":"🎓 Educación","subs":["Pago Universidad","Útiles","Cuotas","Otros"]},
    {"id":"c9","nombre":"🎬 Ocio y cultura","subs":["Restaurantes","Entretenimiento","Salidas varias","Otros"]},
    {"id":"c10","nombre":"🐾 Mascota","subs":["Veterinario","Baño","Medicamentos","Paseador","Otros"]},
    {"id":"c11","nombre":"🛍️ Compras y regalos","subs":["Compras","Domicilios","Otros"]},
    {"id":"c12","nombre":"📦 Imprevistos","subs":["Imprevistos","Otros"]},
    {"id":"c13","nombre":"💰 Ahorro/Inversión","subs":["Ahorro","Inversiones"]},
    {"id":"c14","nombre":"💵 Ingreso","subs":["Salario","Honorarios","Transferencias","Otros"]},
  ],
  "cuentas":[
    {"id":"ct1","nombre":"Cuenta Nómina Bancolombia","tipo":"Debito","banco":"Bancolombia","limite":0},
    {"id":"ct2","nombre":"Mastercard Falabella","tipo":"Credito","banco":"Falabella","limite":41000000},
    {"id":"ct3","nombre":"Crédito Davivienda","tipo":"Credito","banco":"Davivienda","limite":13000000},
    {"id":"ct4","nombre":"Crédito Banco de Bogotá","tipo":"Credito","banco":"Banco de Bogotá","limite":40000000},
    {"id":"ct5","nombre":"TC Adicional 1","tipo":"Credito","banco":"","limite":0},
    {"id":"ct6","nombre":"TC Adicional 2","tipo":"Credito","banco":"","limite":0},
    {"id":"ct7","nombre":"TC Adicional 3","tipo":"Credito","banco":"","limite":0},
    {"id":"ct8","nombre":"Efectivo / Cartera","tipo":"Efectivo","banco":"","limite":0},
  ],
  "medios":["Transferencia Bancaria","Tarjeta Débito","Tarjeta Crédito","Efectivo","PSE","Otro"],
  "presupuestos":{
    "c1":{"Crédito hipotecario":3000000,"Internet":100000,"Netflix":30000,"Amazon":30000,"HBO":15000,"Youtube":40000,"Gemini":80000,"Claude":80000,"Otros":0},
    "c2":{"Seguro de vida Juan":550000,"Seguro de vida Alex":500000,"Clases":0,"Otros":0},
    "c3":{"Mercado":1500000,"Domicilios":500000,"Otros":500000},
    "c4":{"Hipotecario Itaú":900000,"Banco de Bogotá Moto":1650000,"Banco de Bogotá Carro":2230000,"Otros":0},
    "c5":{"Luze":1150000,"Nico":300000,"Alex":200000,"Otros":0},
    "c6":{"Gasolina":500000,"SOAT":0,"Reparaciones":0,"Peajes & Parqueaderos":0,"Seguros":350000,"Otros":0},
    "c7":{"Citas Nico":200000,"Citas Alex":0,"Citas Juan":0,"Medicamentos":200000,"Otros":0},
    "c8":{"Pago Universidad":4000000,"Útiles":0,"Cuotas":0,"Otros":0},
    "c9":{"Restaurantes":1000000,"Entretenimiento":1000000,"Salidas varias":1000000,"Otros":0},
    "c10":{"Veterinario":0,"Baño":100000,"Medicamentos":0,"Paseador":100000,"Otros":0},
    "c11":{"Compras":0,"Domicilios":0,"Otros":0},
    "c12":{"Imprevistos":1500000,"Otros":0},
    "c13":{"Ahorro":3000000,"Inversiones":1000000},
    "c14":{"Salario":27450000,"Honorarios":0,"Transferencias":0,"Otros":0},
  },
  "presupuestos_mensual":{},
  "presupuestos_fijo":{},
  "movimientos":[]
}

def load():
    if not os.path.exists(DATA):
        os.makedirs(os.path.dirname(DATA), exist_ok=True)
        save(DEFAULT); return DEFAULT
    with open(DATA, encoding="utf-8") as f: return json.load(f)

def save(d):
    os.makedirs(os.path.dirname(DATA), exist_ok=True)
    with open(DATA, "w", encoding="utf-8") as f: json.dump(d, f, ensure_ascii=False, indent=2)

HTML_FILE = os.path.join(BASE, "misflujos_app.html")

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,DELETE,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def json_response(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(status)
        self.cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200); self.cors(); self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path

        # Serve the app
        if path in ["/", "/index.html", "/app", ""]:
            with open(HTML_FILE, "rb") as f: body = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", len(body))
            self.end_headers()
            self.wfile.write(body); return

        # API
        if path == "/api/data":
            self.json_response(load()); return

        if path == "/api/movimientos":
            qs = parse_qs(urlparse(self.path).query)
            d = load(); movs = d["movimientos"]
            if "mes"   in qs: movs = [m for m in movs if str(m.get("mes",""))  == qs["mes"][0]]
            if "anio"  in qs: movs = [m for m in movs if str(m.get("anio","")) == qs["anio"][0]]
            if "cat"   in qs: movs = [m for m in movs if m.get("categoria","") == qs["cat"][0]]
            self.json_response(movs); return

        self.send_error(404)

    def do_POST(self):
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}

        if path == "/api/movimientos":
            d = load()
            fecha = body.get("fecha", datetime.now().strftime("%Y-%m-%d"))
            dt = datetime.strptime(fecha, "%Y-%m-%d")
            mov = {
                "id":           str(uuid.uuid4())[:8],
                "fecha":        fecha,
                "tipo":         body.get("tipo","Gasto"),
                "monto":        float(body.get("monto",0)),
                "descripcion":  body.get("descripcion",""),
                "categoria":    body.get("categoria",""),
                "subcategoria": body.get("subcategoria",""),
                "medio":        body.get("medio",""),
                "cuenta":       body.get("cuenta",""),
                "notas":        body.get("notas",""),
                "mes":          dt.month - 1,
                "anio":         dt.year,
            }
            d["movimientos"].insert(0, mov)
            save(d)
            self.json_response({"ok": True, "id": mov["id"]}); return

        if path == "/api/config":
            d = load()
            for k in ["categorias","cuentas","medios","presupuestos","presupuestos_mensual","presupuestos_fijo"]:
                if k in body: d[k] = body[k]
            save(d); self.json_response({"ok": True}); return

        if path == "/api/presupuesto":
            d = load(); d["presupuestos"] = body; save(d)
            self.json_response({"ok": True}); return

        self.send_error(404)

    def do_DELETE(self):
        parts = urlparse(self.path).path.split("/")
        if len(parts) >= 4 and parts[2] == "movimientos":
            d = load()
            d["movimientos"] = [m for m in d["movimientos"] if m["id"] != parts[3]]
            save(d); self.json_response({"ok": True}); return
        self.send_error(404)

PORT = int(os.environ.get("PORT", 5000))
print(f"MisFlujos corriendo en puerto {PORT}")
HTTPServer(("0.0.0.0", PORT), H).serve_forever()
