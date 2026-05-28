import requests
import json

session = requests.Session()
login_res = session.post("http://localhost:8069/web/session/authenticate", json={
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "db": "odoo_db_production",
        "login": "admin",
        "password": "1"
    }
})
print("Login:", login_res.json())

rules_res = session.post("http://localhost:8069/api/misa_bridge/validation_rules", json={
    "jsonrpc": "2.0",
    "method": "call",
    "params": {}
})
print("Rules:", rules_res.json())
