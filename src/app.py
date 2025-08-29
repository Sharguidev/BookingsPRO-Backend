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
from models import db, User, Tenant, Service
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



@app.route('/login', methods=['POST'])
def login():
    
  email = request.json.get("email", None)
  password = request.json.get("password", None)

  if email == None or password == None:
    return jsonify ({"msg": "Missing email or password"}), 400

  user = User.query.filter_by(email=email).first()

  if not user:
    return jsonify({"msg": "Email not found"}), 404

  if check_password_hash(user.password, password):
    access_token = create_access_token(identity=email)
    return jsonify({
        "token": access_token,
        "user": user.serialize()
    }), 200
  else:
    return jsonify({"msg": "Password or email incorrect"}), 401

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

    acces_token = create_access_token(identity=user_data['email'])

    return jsonify({"msg": "User created successfully", "access_token": acces_token}), 200

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
@jwt_required()
def add_user():
    #Get the current user

    current_user_email = get_jwt_identity()
    current_user = User.query.filter_by(email=current_user_email).first()
    
    if not current_user:
        return jsonify ({"msg": "User not found"}), 404
    
    if current_user.role != 'Owner':
        return jsonify ({"msg": "You are not authorized to add users"}), 403

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
        is_active = user.get('is_active', True),
        tenant_id = current_user.tenant_id
    )

    #agregar el usuario a la base de datos
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"msg": "User created successfully"}), 200

#GET all users
@app.route('/users', methods=['GET'])
@jwt_required()
def get_all_users():
    user_logged_email = get_jwt_identity()
    user_logged = User.query.filter_by(email=user_logged_email).first()

    if not user_logged:
        return jsonify({"msg": "User not found"}), 404

    users = User.query.filter_by(tenant_id=user_logged.tenant_id).all();
    return jsonify([user.serialize() for user in users]), 200


#get user by id
@app.route('/user/<int:id>', methods=['GET'])
@jwt_required()
def get_user_by_id(id):
    current_user_email = get_jwt_identity()
    current_user = User.query.filter_by(email=current_user_email).first()
    
    if not current_user:
        return jsonify({"msg": "User not found"}), 404
    
    user = User.query.get(id)
    if not user or user.tenant_id != current_user.tenant_id:
        return jsonify({"msg": "User not found"}), 404
        
    return jsonify(user.serialize()), 200
#Edit user
@app.route('/user/<int:id>', methods=['PUT'])
@jwt_required()
def edit_user(id):
    current_user_email = get_jwt_identity()
    current_user = User.query.filter_by(email=current_user_email).first()
    
    if not current_user:
        return jsonify({"msg": "User not found"}), 404
    
    user = User.query.get(id)
    if not user or user.tenant_id != current_user.tenant_id:
        return jsonify({"msg": "User not found"}), 404

    data = request.get_json()
    
    user.name = data.get('name', user.name)
    user.email = data.get('email', user.email)
    user.role = data.get('role', user.role)
    user.cedula = data.get('cedula', user.cedula)
    user.address = data.get('address', user.address)
    user.phone = data.get('phone', user.phone)
    user.is_active = data.get('is_active', user.is_active)
    db.session.commit()
    return jsonify(user.serialize()), 200

#Delete user

@app.route('/user/<int:id>', methods=['DELETE'])   
@jwt_required()
def delete_user(id):
    #current user logged in
    current_user_email = get_jwt_identity()
    current_user = User.query.filter_by(email=current_user_email).first()

    #Id of the user to delete
    user = User.query.get(id)

    if not current_user:
        return jsonify({"msg" : "User not found"}), 404

    if not user:
        return jsonify({"msg" : "User not found"}), 404

    if current_user.role == "Owner":
        db.session.delete(user)
        db.session.commit()
        return jsonify({"msg": "User deleted successfully"}), 200
    else:
        return jsonify({"msg": "You are not authorized to delete users"}), 403


#Create Services

@app.route('/services', methods=['POST'])
@jwt_required()
def create_service():
    try:
        current_user_email = get_jwt_identity()
        current_user = User.query.filter_by(email=current_user_email).first()

        if not current_user:
            return jsonify({"msg": "User not found"}), 404
        
        data = request.get_json()
        if not data or 'services' not in data:
            return jsonify({"msg": "Missing services data"}), 400
            
        service_data = data.get('services')

        required_fields = ("name", "description", "duration_minutes", "price_cents", "currency", "active")
        missing_fields = [field for field in required_fields if field not in service_data or service_data[field] is None]

        if missing_fields:
            return jsonify({
                "msg": "Missing data",
                "missing_fields": missing_fields,
                "required_fields": required_fields
            }), 400

        new_service = Service(
            name=service_data['name'],
            description=service_data['description'],
            duration_minutes=service_data['duration_minutes'],
            price_cents=service_data['price_cents'],
            currency=service_data['currency'],
            active=service_data['active'],
            tenant_id=current_user.tenant_id
        )

        db.session.add(new_service)
        db.session.commit()

        return jsonify({
            "msg": "Service created successfully",
            "service": {
                "id": new_service.id,
                "name": new_service.name
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Error creating service", "error": str(e)}), 500


#Get services
@app.route('/services', methods=['GET'])
@jwt_required()
def get_all_services():
    user_logged_email = get_jwt_identity()
    user_logged = User.query.filter_by(email=user_logged_email).first()

    if not user_logged:
        return jsonify({"msg": "User not found"}), 404

    services = Service.query.filter_by(tenant_id=user_logged.tenant_id).all();
    return jsonify([service.serialize() for service in services]), 200  

#Get Service by id
@app.route('/service/<int:id>', methods=['GET'])
@jwt_required()
def get_service_by_id(id):
    current_user_email = get_jwt_identity()
    current_user = User.query.filter_by(email=current_user_email).first()
    
    if not current_user:
        return jsonify({"msg": "User not found"}), 404
    
    service = Service.query.get(id)
    if not service or service.tenant_id != current_user.tenant_id:
        return jsonify({"msg": "Service not found"}), 404
        
    return jsonify(service.serialize()), 200


#Edit Service
@app.route('/service/<int:id>', methods=['PUT'])
@jwt_required()
def edit_service(id):
    current_user_email = get_jwt_identity()
    current_user = User.query.filter_by(email=current_user_email).first()
    
    if not current_user:
        return jsonify({"msg": "User not found"}), 404
    
    service = Service.query.get(id)
    if not service or service.tenant_id != current_user.tenant_id:
        return jsonify({"msg": "Service not found"}), 404

    data = request.get_json()
    
    # Update only the fields that are provided in the request
    if 'name' in data:
        service.name = data['name']
    if 'description' in data:
        service.description = data['description']
    if 'duration_minutes' in data:
        service.duration_minutes = data['duration_minutes']
    if 'price_cents' in data:
        service.price_cents = data['price_cents']
    if 'currency' in data:
        service.currency = data['currency']
    if 'active' in data:
        service.active = data['active']
    
    db.session.commit()
    return jsonify(service.serialize()), 200


# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
