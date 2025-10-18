"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""

from flask import Flask, request, jsonify, url_for, Blueprint
from src.models import db, User, Tenant, Service, Staff, StaffTimeOff, StaffWorkingHours, Plan, Payment, Booking
from src.utils import generate_sitemap, APIException
from flask_cors import CORS
from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

api = Blueprint('api', __name__)

# Allow CORS requests to this API
CORS(api)

#Create plan

@api.route('/plan', methods=['POST'])
def create_plan():
    
    data = request.get_json()

    if not data:
        return jsonify ({"msg": "Missing Data"}), 400
        
    required_fields = ["name", "price_cents", "currency", "max_staff", "max_bookings", "features"]

    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
     return jsonify({"msg": f"Missing {missing_fields}"}), 400


    if Plan.query.filter_by(name=data['name']).first():
        return jsonify({"msg" : "Plan already exists" }), 400

    new_plan = Plan(
        name = data['name'],
        price_cents = data['price_cents'],
        currency = data['currency'],
        max_staff = data['max_staff'],
        max_bookings = data['max_bookings'],
        features = data['features']
    )

    db.session.add(new_plan)
    db.session.commit()

    return jsonify({"msg": "Plan created successfully"}), 200

@api.route('/plan', methods=['GET'])
def get_plans():
    plans = Plan.query.all()

    if not plans:
        return jsonify ({"msg":"There are no plans register a new plan please"}), 404
    
    return jsonify([plan.serialize() for plan in plans]), 200

@api.route('/plan/<int:id>', methods=['GET'])
def get_plan_by_id(id):

    plan = Plan.query.get(id)

    if not plan:
        return jsonify({"msg": "This plan doesn't exist"}), 404


    return jsonify(plan.serialize()), 200

@api.route('/plan/<int:id>', methods=['PUT'])
def edit_plan(id):

    plan = Plan.query.get(id)

    if not plan:
        return jsonify({"msg": "This plan doesn't exist"}), 404

    data = request.get_json()

    plan.name = data.get('name', plan.name)
    plan.price_cents = data.get('price_cents', plan.price_cents)
    plan.currency = data.get('currency', plan.currency)
    plan.max_staff = data.get('max_staff', plan.max_staff)
    plan.max_bookings = data.get('max_bookings', plan.max_bookings)
    plan.features = data.get('features', plan.features)

    db.session.commit()
    return jsonify(plan.serialize()), 200

@api.route('/plan/<int:id>', methods=['DELETE'])
def delete_plan(id):

    plan = Plan.query.get(id)

    if not plan:
        return jsonify({"msg": "This plan doesn't exist"}), 404

    db.session.delete(plan)
    db.session.commit()

    return jsonify({"msg" : "Plan deleted successfully"}), 200

@api.route('/login', methods=['POST'])
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

#Create tenant and the owner user

@api.route('/register-tenant-owner', methods=['POST'])
def register_tenant_owner():
    data = request.get_json()
    tenant_data = data.get('tenants')
    user_data = data.get('user')

    #comprobamos que esten todos los campos

    if not all(tenant_data.get(key) for key in ("name", "dni", "subdomain")):
        return jsonify({"msg": "Missing data"}), 400

    if not all(user_data.get(key) for key in ("name", "email", "password", "role", "cedula", "address", "phone")):
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
        subdomain = tenant_data['subdomain'],
        country = tenant_data['country'],
        province = tenant_data['province'],
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
    )


    #agregar el usuario a la base de datos
    db.session.add(owner_user)
    db.session.commit()

    acces_token = create_access_token(identity=user_data['email'])

    return jsonify({"msg": "User created successfully", "access_token": acces_token}), 200

#Get all tenants
@api.route('/tenants', methods=['GET'])
def get_tenant():
    tenants = Tenant.query.all()
    return jsonify([tenant.serialize() for tenant in tenants]), 200


#get tenant by province or name tenant or either search services
@api.route('/public/search', methods=['GET'])
def get_tenant_by_id():
    
   query = request.args.get('query', '').strip()

   if not query:
    return jsonify ({
        "error": "Query parameter is required",
        "usage": "GET /public/search?query=<term>"
    }), 400
   #1 Priority 1 search a Tenant by name  
   tenant_results = Tenant.query.filter(Tenant.name.ilike(f'%{query}%')).all() 

   if tenant_results:
    return jsonify({
        "type": "tenant",
        "results": [
            {
                "tenant_id": tenant.tenant_id,
                "name": tenant.name,
                "description": tenant.description,
                "province": tenant.province,
                "subdomain": tenant.subdomain,
                "country": tenant.country
            }

            for tenant in tenant_results
        ]
    }), 200


    #2 Priority 2 search a Service by name
    
    service_results = db.session.query(Service, Tenant).join(
        Tenant, Service.tenant_id == Tenant.tenant_id
    ).filter(
        Service.name.ilike(f'%{query}%')
    ).all()

    if service_results:
        return jsonify({
            "type": "service",
            "results": [
                {
                    "service_id": service.id,
                    "name": service.name,
                    "price": float(service.price) if service.price else None,
                    "duration_minutes": service.duration_minutes,
                    "tenant_name": tenant.name,
                    "tenant_province": tenant.province,
                    "tenant_country": tenant.country
                }
                for service, tenant in service_results
            ]
        }), 200

    # priority 3 by province

    province_result = Tenant.query.filter(
        Tenant.province.ilike(f'%{query}%')
    ).all()


    if province_result:
        return jsonify ({
            "type": "tenant", 
            "results": [
                {
                   "tenant_id": tenant.tenant_id,
                   "name": tenant.name,
                   "description": tenant.description,
                   "province": tenant.province,
                   "subdomain": tenant.subdomain,
                   "country": tenant.country
                }
                for tenant, in province_results
            ]
        }), 200


    return jsonify ({
        "type": "none",
        "message": "Not service or Tenant found"
    }), 404    
    

#Update tenant
@api.route('/tenants/<int:id>', methods=['PUT'])
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
@api.route('/tenants/<int:id>', methods=['DELETE'])
def delete_tenant(id):
    tenant = Tenant.query.get(id)
    user = User.query.filter_by(tenant_id=id, role='Owner').first()
    user_staff = User.query.filter_by(tenant_id=id, role='Staff').all()
    service = Service.query.filter_by(tenant_id=id).all()
    staff = Staff.query.filter_by(tenant_id=id).all()
    customer = Customer.query.filter_by(tenant_id=id).all()
    booking = Booking.query.filter_by(tenant_id=id).all()
    payment = Payment.query.filter_by(tenant_id=id).all()
    email_logs = EmailLog.query.filter_by(tenant_id=id).all()
    staff_working_hours = StaffWorkingHours.query.filter_by(tenant_id=id).all()
    staff_time_off = StaffTimeOff.query.filter_by(tenant_id=id).all()
    plan = Plan.query.filter_by(tenant_id=id).all()

    


    if not tenant:
        return jsonify({"msg":"Tenant not found"}), 404
    if not user:
        return jsonify({"msg":"Owner not found for this tenant"}), 404
    if not user_staff:
        return jsonify({"msg " : "Staff not found for this tenant"}), 404
    if not service:
        return jsonify({"msg " : "Service not found for this tenant"}), 404
    if not staff:
        return jsonify({"msg " : "Staff not found for this tenant"}), 404
    if not customer:
        return jsonify({"msg " : "Customer not found for this tenant"}), 404
    if not booking:
        return jsonify({"msg " : "Booking not found for this tenant"}), 404
    if not payment:
        return jsonify({"msg " : "Payment not found for this tenant"}), 404
    if not email_logs:
        return jsonify({"msg " : "Email log not found for this tenant"}), 404
    if not staff_working_hours:
        return jsonify({"msg " : "Staff working hours not found for this tenant"}), 404
    if not staff_time_off:
        return jsonify({"msg " : "Staff time off not found for this tenant"}), 404
    if not plan:
        return jsonify({"msg " : "Plan not found for this tenant"}), 404

    db.session.delete(tenant)
    db.session.delete(user)
    db.session.delete(user_staff)
    db.session.delete(service)
    db.session.delete(staff)
    db.session.delete(customer)
    db.session.delete(booking)
    db.session.delete(payment)
    db.session.delete(email_logs)
    db.session.delete(staff_working_hours)
    db.session.delete(staff_time_off)
    db.session.delete(plan)
    db.session.commit()

    return jsonify({
        "msg":"Tenant and owner deleted successfully",
        "Deleted Tenant": tenant.id,
        "Deleted Owner": user.id,
        "Deleted Staff": user_staff.id,
        "Deleted Service": service.id,
        "Deleted Customer": customer.id,
        "Deleted Booking": booking.id,
        "Deleted Payment": payment.id,
        "Deleted Email Log": email_logs.id,
        "Deleted Staff Working Hours": staff_working_hours.id,
        "Deleted Staff Time Off": staff_time_off.id,
        "Deleted Plan": plan.id
        }), 200
    

#INSERT USER ENDPOINT
@api.route('/adduser', methods=['POST'])
@jwt_required()
def add_user():
    #Get the current user

    current_user_email = get_jwt_identity()
    current_user = User.query.filter_by(email=current_user_email).first()
    
    if not current_user:
        return jsonify ({"msg": "User not found"}), 404
    
    # First we get the payload json
    data = request.get_json()
    user = data.get('user')
    
    if not user:
        return jsonify({"msg": "Missing data"}), 400

    if current_user.role == 'Staff' and user.get('role') == 'Owner':
        return jsonify({"msg": "Staff can't create Owner Accounts."}), 403
        
    required_fields = ["name", "email", "password", "role", "cedula", "address", "phone"]

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
        tenant_id = current_user.tenant_id
    )

    #agregar el usuario a la base de datos
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"msg": "User created successfully"}), 200

#GET all users
@api.route('/users', methods=['GET'])
@jwt_required()
def get_all_users():
    user_logged_email = get_jwt_identity()
    user_logged = User.query.filter_by(email=user_logged_email).first()

    if not user_logged:
        return jsonify({"msg": "User not found"}), 404

    users = User.query.filter_by(tenant_id=user_logged.tenant_id).all();
    return jsonify([user.serialize() for user in users]), 200


#get user by id
@api.route('/user/<int:id>', methods=['GET'])
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
@api.route('/user/<int:id>', methods=['PUT'])
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
    db.session.commit()
    return jsonify(user.serialize()), 200

#Delete user

@api.route('/user/<int:id>', methods=['DELETE'])   
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
@api.route('/services', methods=['POST'])
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

        required_fields = ("name", "description", "duration_minutes", "price_cents", "currency")
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
@api.route('/services', methods=['GET'])
@jwt_required()
def get_all_services():
    user_logged_email = get_jwt_identity()
    user_logged = User.query.filter_by(email=user_logged_email).first()

    if not user_logged:
        return jsonify({"msg": "User not found"}), 404

    services = Service.query.filter_by(tenant_id=user_logged.tenant_id).all();
    return jsonify([service.serialize() for service in services]), 200  

#Get Service by id
@api.route('/service/<int:id>', methods=['GET'])
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
@api.route('/service/<int:id>', methods=['PUT'])
@jwt_required()
def edit_service(id):
    current_user_email = get_jwt_identity()
    current_user = User.query.filter_by(email=current_user_email).first()
    
    if not current_user:
        return jsonify({"msg": "User not found"}), 404
    
    service = Service.query.get(id)
    if not service or service.tenant_id != current_user.tenant_id:
        return jsonify({"msg": "Service not found"}), 404

    try:
        data = request.get_json()
        if not data:
            return jsonify({"msg": "Missing data"}), 400
        
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
        
        
        db.session.commit()
        return jsonify(service.serialize()), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Error updating service", "error": str(e)}), 500

#Delete Service
@api.route('/service/<int:id>', methods=['DELETE'])
@jwt_required()

def delete_service(id):
    current_user_email = get_jwt_identity()
    current_user = User.query.filter_by(email=current_user_email).first()
    
    if not current_user:
        return jsonify({"msg": "User not found"}), 404
    
    service = Service.query.get(id)
    
    if not service or service.tenant_id != current_user.tenant_id:
    
        return jsonify({"msg": "Service not found"}), 404

    try: 
        bookings = Booking.query.filter_by(service_id=id, tenant_id=current_user.tenant_id).all()
        for booking in bookings: 
            db.session.delete(booking)

        db.session.delete(service)
        db.session.commit()
        return jsonify({"msg": "Service deleted successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Error deleting service", "error": str(e)}), 500

#STAFF CRUD

#create Staff
@api.route('/staff', methods=['POST'])
@jwt_required()
def create_staff():
    user_logged_email = get_jwt_identity()
    user_logged = User.query.filter_by(email=user_logged_email).first()


    if not user_logged:
        return jsonify({"msg": "User not found"}), 404

    data = request.get_json()

    if not data or 'staff' not in data:
        return jsonify({"msg": "Missing data"}), 400
        
    staff_data = data.get('staff')

    required_fields = ("dni", "name", "email", "phone_number", "specialty", "role", "is_active", "hire_date")
    missing_fields = [field for field in required_fields if field not in staff_data or staff_data[field] is None]
    
    if missing_fields:
        return jsonify ({
            "msg":"You are forgetting some fields",
            "missing_fields": missing_fields,
            "required_fields": required_fields
        }), 400

    if Staff.query.filter_by(dni=staff_data['dni']).first():
        return jsonify({"msg": "Staff already exists"}), 400
    
    new_staff = Staff(
        dni=staff_data['dni'],
        name = staff_data['name'],
        email = staff_data['email'],
        phone_number = staff_data['phone_number'],
        medic_license = staff_data.get('medic_license'),
        specialty = staff_data['specialty'],
        role = staff_data['role'],
        is_active = staff_data['is_active'],
        hire_date = staff_data['hire_date'],
        tenant_id = user_logged.tenant_id,
        created_at = datetime.utcnow(),
        updated_at = datetime.utcnow()
    )
    
    db.session.add(new_staff)
    db.session.commit()

    return jsonify({
        "msg": "Staff created successfully",
        "data": new_staff.serialize()
        }), 201
    

#get Staff
@api.route('/staff', methods=['GET'])
@jwt_required()
def get_all_staff():
    user_logged_email = get_jwt_identity()
    user_logged = User.query.filter_by(email=user_logged_email).first()

    if not user_logged:
        return jsonify({"msg": "User not found"}), 404

    staff = Staff.query.filter_by(tenant_id=user_logged.tenant_id).all();
    return jsonify([staff.serialize() for staff in staff]), 200

#get Staff by ID
@api.route('/staff/<int:id>', methods=['GET'])
@jwt_required()
def get_staff_by_id(id):
    user_logged_email = get_jwt_identity()
    user_logged = User.query.filter_by(email=user_logged_email).first()

    if not user_logged:
        return jsonify({"msg": "User not found"}), 404

    staff = Staff.query.get(id)
    if not staff or staff.tenant_id != user_logged.tenant_id:
        return jsonify({"msg": "Staff not found"}), 404

    return jsonify(staff.serialize()), 200


#update Staff 
@api.route('/staff/<int:id>', methods=['PUT'])
@jwt_required()
def update_staff(id):
    user_logged_email = get_jwt_identity()
    user_logged = User.query.filter_by(email=user_logged_email).first()

    if not user_logged:
        return jsonify({"msg": "User not found"}), 404

    staff = Staff.query.get(id)
    if not staff or staff.tenant_id != user_logged.tenant_id:
        return jsonify({"msg": "Staff not found"}), 404

    data = request.get_json()
    
    # Update only the fields that are provided in the request
    if 'name' in data:
        staff.name = data['name']
    if 'email' in data:
        staff.email = data['email']
    if 'phone_number' in data:
        staff.phone_number = data['phone_number']
    if 'specialty' in data:
        staff.specialty = data['specialty']
    if 'role' in data:
        staff.role = data['role']
    if 'is_active' in data:
        staff.is_active = data['is_active']
    if 'medic_license' in data:
        staff.medic_license = data.get('medic_license')

    from datetime import datetime
    staff.update_at = datetime.utcnow()
    
    db.session.commit()
    return jsonify(staff.serialize()), 200

#Delete Staff
@api.route('/staff/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_staff(id):
    user_logged_email = get_jwt_identity()
    user_logged = User.query.filter_by(email=user_logged_email).first()

    if not user_logged:
        return jsonify({"msg": "User not found"}), 404

    staff = Staff.query.get(id)
    if not staff or staff.tenant_id != user_logged.tenant_id:
        return jsonify({"msg": "Staff not found"}), 404

    try:
        bookings = Booking.query.filter_by(staff_id=id, tenant_id= user_logged.tenant_id).all()
        staff_working_hours = StaffWorkingHours.query.filter_by(staff_id=staff.id).all()
        staff_time_off = StaffTimeOff.query.filter_by(staff_id=staff.id).all()
        
        for booking in bookings: 
            db.session.delete(booking)

        for staff_time_off in staff_time_off:
            db.session.delete(staff_time_off)
            
        for staff_working_hour in staff_working_hours:
            db.session.delete(staff_working_hours)
        
        db.session.delete(staff)
        db.session.commit()
        return jsonify({"msg": "Staff deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Error deleting staff", "error": str(e)}), 500


#insert Staff working hours
@api.route('/staff-working', methods=['POST'])
def insert_work_hours():
    user_logged_email = get_jwt_identity()
    user_logged = User.query.filter_by(email=user_logged_email).first()

    staff_id = Staff.query.get(id)

    if user_logged.tenant_id == staff_id.tenant_id:
        try:

            data = request.get_json()

            if not data:
                return jsonify({"msg": "Missing data"}), 400

            required_fields = ["staff_id","work_days", "start_time", "end_time"]

            if not all:
                return jsonify({"msg": "Missing some fields"}), 400

            staff = Staff.query.get(data['staff_id'])

            new_working_schedule = StaffWorkingHours(
                work_days = data['work_days'],
                start_time = data['start_time'],
                end_time = data ['end_time'],
                staff_id = staff.id
            )

            db.session.add(new_working_schedule)
            db.session.commit()
            return jsonify({"msg": "Staff schedule registered successfully"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"msg": "Error registering Staff schedule"}), 200
    
#create customer & booking
@api.route('/booking', methods=['POST'])
def create_booking_customer():

   #request the tenant Id
   subdomain = request.host.split('.')[0]
   tenant = Tenant.query.filter_by(subdomain=subdomain).first() 

   if not tenant:
    return jsonify ({"msg": "Tenant not found"}), 404

   tenant_id = tenant.id 

   data = request.get_json()
   
   service_id = data.get("service_id")
   staff_id = data.get("staff_id")
   start_time = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
   end_time = start_time + timedelta(minutes=service.duration_minutes)
   payment_method = data.get("payment_method")

   # Validate the service belong to the tenant

   service = Service.query.filter_by(id=service_id, tenant_id=tenant_id).first()
   if not service:
    return jsonify ({
        "msg": "Service not found"
    }), 404 

    #Validate Staff belong to the tenant
    staff = Staff.query.filter_by(id=staff_id, tenant_id=tenant_id).first()
    if not staff:
      return jsonify ({
        "msg": "Staff not found"
    }), 404  
    

    #customer Data
    customer_data = data.get("customer")
    if not customer_data:
      return jsonify ({
        "msg": "Customer data is required"
    }), 400


    #filter if create or not
    customer = Customer.query.filter_by(email=customer_data["email"], tenant_id=tenant_id).first()
    if not customer:
      customer = Customer(
        email=customer_data["email"],
        tenant_id=tenant_id,
        name=customer_data["name"],
        phone=customer_data["phone"],
        dni=customer_data["dni"],
        is_active=customer_data["is_active"],
      )
      db.session.add(customer)
      db.session.flush()

    #Booking status 

    status = "pending_payment" if payment_method == "online" else "confirmed"
      
    booking = Booking(
        tenant_id=tenant_id,
        customer_id=customer.id,
        service_id=service_id,
        staff_id=staff_id,
        start_time=start_time,
        end_time=end_time,
        status=status,
        created_at=datetime.utcnow(),
    )
    db.session.add(booking)
    db.session.commit()
    

    return jsonify ({
        "msg": "Booking created successfully",
        "data": booking.serialize()
    }), 201


@api.route('/available-time-slots', methods=['GET'])
def get_available_time_slots():
    staff_id = request.args.get('staff_id')
    service_id = request.args.get('service_id')
    date = request.args.get('date')  # Format: YYYY-MM-DD
    default_timezone = 'America/Costa_Rica'

    if not all([staff_id, service_id, date]):
        return jsonify({"error": "Missing required parameters"}), 400
        
        try:
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            today = datetime.now().date()

            if date_obj.date < today:
                return jsonify({"error": "Cannot book appointments in the past"}), 400


            # Get service to get duration
            service = Service.query.get(service_id)
            if not service:
                return jsonify({"error": "Service not found"}), 404


            # Get staff working hours for the selected day
            target_date = datetime.strptime(date, '%Y-%m-%d')
            day_of_week = target_date.weekday()  # 0 = Monday, 6 = Sunday   

            working_hours = StaffWorkingHours.query.filter_by(
                staff_id=staff_id,
                work_days=day_of_week
            ).first()    


            if not working_hours:
                return jsonify({"available_slots": []})
            # Get existing bookings for the day
            start_of_day = datetime.strptime(date, '%Y-%m-%d')
            end_of_day = start_of_day.replace(hour=23, minute=59, second=59)
            
            existing_bookings = Booking.query.filter(
                Booking.staff_id == staff_id,
                Booking.start_time >= start_of_day,
                Booking.start_time <= end_of_day,
                Booking.status != 'cancelled'
            ).all()    


            # Generate time slots
            slot_duration = 30  # minutes between slots
            buffer_minutes = 15
            current_time = datetime.combine(target_date, working_hours.start_time)
            end_working_time = datetime.combine(target_date, working_hours.end_time)
            available_slots = []
            
            while current_time + timedelta(minutes=service.duration_minutes) <= end_working_time:
                #calculate slot end time
                slot_end = current_time + timedelta(minutes=service.duration_minutes)
                
                is_during_lunch = False
                if working_hours.lunch_start and working_hours.lunch_end:
                    lunch_start_dt = datetime.combine(target_date, working_hours.lunch_start)
                    lunch_end_dt = datetime.combine(target_date, working_hours.lunch_end)    

                    if not (slot_end <= lunch_start_dt or current_time >= lunch_end_dt):
                        is_during_lunch = True    

                if not is_during_lunch:
                #calculate buffer Zone 15 minutes
                    slot_start_with_buffer = current_time - timedelta(minutes=buffer_minutes)
                    slot_end_with_buffer = current_time + timedelta(minutes=buffer_minutes)    
                    # Check if this slot is available
                    is_available = not any(
                        not (booking.end_time <= slot_start_with_buffer or booking.start_time >= slot_end_with_buffer)
                        for booking in existing_bookings
                    )
                    
                    if is_available:
                        available_slots.append({
                            'start': current_time.strftime('%H:%M')
                        })
                    
                    # Move to next slot (30-minute intervals)
                    current_time += timedelta(minutes=slot_duration)
                return jsonify({
                    "available_slots": available_slots,
                    "service_duration": service.duration_minutes
                })
        except Exception as e:
            return jsonify({"error": str(e)}), 500