"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Tenant
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, JWTManager
#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False

app.config["JWT_SECRET_KEY"] = "2313231@!@##$@#%@!!@$!nfgbihgns"
jwt = JWTManager(app)

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)




# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

@app.route('/user', methods=['GET'])
def handle_hello():

    response_body = {
        "msg": "Hello, this is your GET /user response "
    }

    return jsonify(response_body), 200

#Create tenant and the owner user

@app.route('/register-tenant-owner', methods=['POST'])
def register_tenant_owner():
    data = request.get_json()
    tenant_data = data.get('tenants')
    user_data = data.get('user')

    #comprobamos que esten todos los campos

    if not all(tenant_data.get(key) for key in ("name", "dni", "subdomain")):
        return jsonify({"msg": "Missing data"}), 400

    if not all(user_data.get(key) for key in ("name", "email", "password", "role", "cedula", "address", "phone", "is_active")):
        return jsonify({"msg": "Missing data"}), 400

    #verificar si el usuario existe
    if User.query.filter_by(email=user_data['email']).first():
        return jsonify({"msg": "User already exists"}), 400
    
    #verificar si el tenant existe
    if Tenant.query.filter_by(subdomain=tenant_data['subdomain']).first():
        return jsonify({"msg": "Tenant already exists"}), 400


    new_tenant = Tenant(
        name = tenant_data['name'],
        dni = tenant_data['dni'],
        subdomain = tenant_data['subdomain']
    )

    db.session.add(new_tenant)
    db.session.flush() # get tenant.id without committing yet

    #hashear la contraseña
    pass_hashed = generate_password_hash(user_data['password'])

    #crear el usuario
    owner_user = User(
        name = user_data['name'],
        email = user_data['email'],
        password = pass_hashed,
        role = user_data.get('role', 'Owner'),
        cedula = user_data['cedula'],   
        address = user_data['address'],
        phone = user_data['phone'],
        tenant_id = new_tenant.id,
        is_active = user_data.get('is_active', True)
    )


    #agregar el usuario a la base de datos
    db.session.add(owner_user)
    db.session.commit()

    return jsonify({"msg": "User created successfully"}), 200

#Get all tenants
@app.route('/tenants', methods=['GET'])
def get_tenant():
    tenants = Tenant.query.all()
    return jsonify([tenant.serialize() for tenant in tenants]), 200


#get tenant by id
@app.route('/tenants/<int:id>', methods=['GET'])
def get_tenant_by_id(id):
    tenant = Tenant.query.get(id)
    if not tenant:
        return jsonify({"msg":"Tenant not found"}), 404
    return jsonify(tenant.serialize()), 200
    

#Update tenant
@app.route('/tenants/<int:id>', methods=['PUT'])
def update_tenant(id):
    data = request.get_json()
    tenant = Tenant.query.get(id)
    if not tenant:
        return jsonify({"msg":"Tenant not found"}), 404
    tenant.name = data.get('name', tenant.name)
    tenant.dni = data.get('dni', tenant.dni)
    tenant.subdomain = data.get('subdomain', tenant.subdomain)
    db.session.commit()
    return jsonify(tenant.serialize()), 200

#Delete tenant/ modify tomorrow 
@app.route('/tenants-user/<int:id>', methods=['DELETE'])
def delete_tenant(id):
    tenant = Tenant.query.get(id)
    user = User.query.filter_by(tenant_id=id, role='Owner').first()
    if not tenant:
        return jsonify({"msg":"Tenant not found"}), 404
    if not user:
        return jsonify({"msg":"Owner not found for this tenant"}), 404
    db.session.delete(tenant)
    db.session.delete(user)
    db.session.commit()
    return jsonify({
        "msg":"Tenant and owner deleted successfully",
        "Deleted Tenant": tenant.id,
        "Deleted Owner": user.id
        }), 200
    

#INSERT USER ENDPOINT
@app.route('/adduser', methods=['POST'])
def add_user():
    # First we get the payload json
    data = request.get_json()
    user = data.get('user')

    if not user:
        return jsonify({"msg": "Missing data"}), 400

    required_fields = ["name", "email", "password", "role", "cedula", "address", "phone", "is_active"]
    if not all(user.get(field) for field in required_fields):
        return jsonify({"msg": "Missing required data " + str(required_fields)}), 400

    #verificar si el usuario existe
    if User.query.filter_by(email=user['email']).first():
        return jsonify({"msg": "User already exists"}), 400

    #hashear la contraseña
    pass_hashed = generate_password_hash(user['password'])

    #crear el usuario
    new_user = User(
        name = user['name'],
        email = user['email'],
        password = pass_hashed,
        role = user.get('role', 'Staff'),
        cedula = user['cedula'],
        address = user['address'],
        phone = user['phone'],
        is_active = user.get('is_active', True)
    )

    #agregar el usuario a la base de datos
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"msg": "User created successfully"}), 200
    

# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
