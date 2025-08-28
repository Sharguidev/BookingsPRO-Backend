from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, Boolean
from datetime import datetime, time
from sqlalchemy import String, Boolean, Integer, DateTime, ForeignKey, Text, Time
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
db = SQLAlchemy()


class Plan(db.Model):
    __tablename__ = "plans"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    price_cents: Mapped[int]
    currency: Mapped[str] = mapped_column(String(3), default="CRC")
    max_staff: Mapped[int]
    max_bookings: Mapped[int]
    features: Mapped[str] = mapped_column(Text)

    tenants: Mapped[list["Tenant"]] = relationship(back_populates="plan")

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "price_cents": self.price_cents,
            "currency": self.currency,
            "max_staff": self.max_staff,
            "max_bookings": self.max_bookings,
            "features": self.features
        }

class Tenant(db.Model):
    __tablename__: "tenants"
    id: Mapped[int] = mapped_column(primary_key=True, unique=True)
    name: Mapped[str] = mapped_column(String(120),  nullable=False)
    dni: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    subdomain: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    create_at: Mapped[datetime ] = mapped_column(DateTime, default=datetime.utcnow)
    plan_id: Mapped[int] = mapped_column(ForeignKey(Plan.id), nullable=False, default=1)
    users: Mapped[list["User"]] = relationship(back_populates="tenant")
    services: Mapped[list["Service"]] = relationship(back_populates="tenant")
    staff: Mapped[list["Staff"]] = relationship(back_populates="tenant")
    customers: Mapped[list["Customer"]] = relationship(back_populates="tenant")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="tenant")
    email_logs: Mapped[list["EmailLog"]] = relationship(back_populates="tenant")

    plan: Mapped["Plan"] = relationship(back_populates="tenants")

    def serialize(self):
        return {
            "id": self.id, 
            "name": self.name, 
            "dni": self.dni,
            "subdomain": self.subdomain, 
            "create_at": self.create_at,
            }


class User(db.Model):
    __tablename__= "user"
    tenant_id: Mapped[int] = mapped_column(ForeignKey(Tenant.id), nullable=False, default=6)
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    cedula: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    address: Mapped[str] = mapped_column(String(50), nullable=False)
    phone: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False)

    tenant: Mapped["Tenant"] = relationship(back_populates="users")

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "cedula": self.cedula,
            "address": self.address,
            "phone": self.phone,
            "is_active": self.is_active    
            # do not serialize the password, its a security breach
        }

class Service(db.Model):
    __tablename__="services"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey(Tenant.id), nullable=False, default=5)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)
    duration_minutes: Mapped[int]
    price_cents: Mapped[int]
    currency: Mapped[str] = mapped_column(String(3), default= "CRC")
    active: Mapped[bool] = mapped_column(Boolean, default= True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    tenant: Mapped["Tenant"] = relationship(back_populates="services")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="service")

    def serialize(self):
        return{
                "id":self.id,
                "name": self.name, 
                "price_cents": self.price_cents, 
                "currency": self.currency
             }

class Staff(db.Model):
    __tablename__="staff"
    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey(Tenant.id), nullable=False)
    dni: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100))
    medic_license: Mapped[str] = mapped_column(String(120), unique=True, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False)

    tenant: Mapped["Tenant"] = relationship(back_populates="staff")
    working_hours: Mapped[list["StaffWorkingHours"]] = relationship(back_populates="staff")
    time_off: Mapped[list["StaffTimeOff"]] = relationship(back_populates="staff")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="staff")

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "dni": self.dni,
            "medic_license": self.medic_license,
                
            # do not serialize the password, its a security breach
        }


class StaffWorkingHours(db.Model):
    __tablename__="staff_working_hours"
    id: Mapped[int] = mapped_column(primary_key=True)
    staff_id: Mapped[int] = mapped_column(ForeignKey(Staff.id), nullable=False)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    
    staff: Mapped["Staff"] = relationship(back_populates="working_hours")   

    def serialize(self):
        return {
            "id": self.id,
            "staff_id": self.staff_id,
            "day_of_week": self.day_of_week,
            "start_time": self.start_time,
            "end_time": self.end_time
        }

class StaffTimeOff(db.Model):
    __tablename__="staff_time_off"
    id: Mapped[int] = mapped_column(primary_key=True)
    staff_id: Mapped[int] = mapped_column(ForeignKey(Staff.id), nullable=False)
    start_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    staff: Mapped["Staff"] = relationship("Staff", back_populates="time_off")
    

    
    def serialize(self):
        return {
            "id": self.id,
            "staff_id": self.staff_id,
            "start_date": self.start_date,
            "end_date": self.end_date
        }

class Customer(db.Model):
    __tablename__="customers"
    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey(Tenant.id), nullable=False)
    dni: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    phone: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False)

    tenant: Mapped["Tenant"] = relationship(back_populates="customers")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="customer")

    def serialize(self):
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "dni": self.dni,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "is_active": self.is_active
        }

class Booking(db.Model):
    __tablename__="bookings"
    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey(Tenant.id), nullable=False)
    customer_id: Mapped[int] = mapped_column(ForeignKey(Customer.id), nullable=False)
    service_id: Mapped[int] = mapped_column(ForeignKey(Service.id), nullable=False)
    staff_id: Mapped[int] = mapped_column(ForeignKey(Staff.id), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False)

    tenant: Mapped["Tenant"] = relationship(back_populates="bookings")
    customer: Mapped["Customer"] = relationship(back_populates="bookings")
    service: Mapped["Service"] = relationship(back_populates="bookings")
    staff: Mapped["Staff"] = relationship(back_populates="bookings")
    payments: Mapped[list["Payment"]] = relationship(back_populates="booking")
    email_logs: Mapped[list["EmailLog"]] = relationship(back_populates="booking")

    def serialize(self):
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "customer_id": self.customer_id,
            "service_id": self.service_id,
            "staff_id": self.staff_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "status": self.status,
            "created_at": self.created_at,
            "is_active": self.is_active
        }
class Payment(db.Model):
    __tablename__="payments"
    id: Mapped[int] = mapped_column(primary_key=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey(Booking.id), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    stripe_payment_id: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False)

    booking: Mapped["Booking"] = relationship(back_populates="payments")

    def serialize(self):
        return {
            "id": self.id,
            "booking_id": self.booking_id,
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status,
            "stripe_payment_id": self.stripe_payment_id,
            "created_at": self.created_at,
            "is_active": self.is_active
        }

class EmailLog(db.Model):
    __tablename__="email_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey(Tenant.id), nullable=False)
    booking_id: Mapped[int] = mapped_column(ForeignKey(Booking.id), nullable=False)
    recepient_email: Mapped[str] = mapped_column(String(120), nullable=False)
    subject: Mapped[str] = mapped_column(String(120), nullable=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    tenant: Mapped["Tenant"] = relationship(back_populates="email_logs")
    booking: Mapped["Booking"] = relationship(back_populates="email_logs")
    
    def serialize(self):
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "booking_id": self.booking_id,
            "recepient_email": self.recepient_email,
            "subject": self.subject,
            "sent_at": self.sent_at
        }
    