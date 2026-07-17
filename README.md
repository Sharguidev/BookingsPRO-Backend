# BookingsPRO Backend

A Flask + PostgreSQL backend for a multi-tenant booking platform.
It provides REST APIs to manage tenants, users, services, availability, bookings, and more.
Supports environment-based configuration, Docker, and deployment to Render or Heroku.

## 🚀 Features

Multi-tenant architecture.

CRUD for tenants, users, and services.

Easy local setup with pipenv.

Ready-to-deploy with Render or Heroku.

Environment variables managed via .env.

## 📦 Installation

You can run this project with Docker or Python 3.13 installed on your system.

Clone the repository:

```sh
git clone https://github.com/Sharguidev/BookingsPRO-Backend.git
cd BookingsPRO-Backend

```

Install dependencies with pipenv 


```sh
pipenv install
psql -U root -c 'CREATE DATABASE example;'

```

> Note: Codespaces users can connect to psql by typing: `psql -h localhost -U gitpod example`



Create the migrations file:
```sh
pipenv run init
```

## Migrations commands

```sh
pipenv run migrate
pipenv run upgrade
```

# Initilize the enviroment

```sh
pipenv shell
```

## Configure your enviroment variables

```sh
cp .env.example .env
```

## How to Start coding

There is an example API working with an example database. All your application code should be written inside the `./src/` folder.

- src/main.py (it's where your endpoints should be coded)
- src/models.py (your database tables and serialization logic)
- src/utils.py (some reusable classes and functions)
- src/admin.py (add your models to the admin and manage your data easily)

## ▶️ Running the App

Start the backend with:
```sh
pipenv run start
```

## Generate a database diagram

If you want to visualize the structure of your database in the form of a diagram, you can generate it with the following command:

```bash
$ pipenv run diagram
```

## ☁️ Deployment
This boilerplate it's 100% read to deploy with Render.com and Herkou in a matter of minutes. Please read the [official documentation about it](https://start.4geeksacademy.com/deploy).

##License Repo
Check the LICENSE.md or LICENSE.es.md for more information.


## 🗺️ Roadmap

### 🏢 Multi-Tenancy
- [ ] Tenant registration / onboarding
- [ ] Tenant-aware request routing
- [ ] Tenant-level configuration & branding

### 👤 Users & Auth
- [ ] User registration & login
- [ ] Role-based access (admin, staff, customer)
- [ ] JWT / session authentication
- [ ] Password reset flow

### 🧑‍💼 Staff Management
- [ ] CRUD for staff members
- [ ] Assign staff to services
- [ ] Staff working hours / schedules

### 🛎️ Services
- [ ] CRUD for services (name, duration, price, description)
- [ ] Categorize services

### 📅 Availability
- [ ] Define staff/tenant availability
- [ ] Block off unavailable dates/times
- [ ] Conflict detection (no double-booking)

### 📖 Bookings
- [ ] Create / update / cancel bookings
- [ ] Booking confirmation flow
- [ ] Booking history per customer
- [ ] Booking status tracking (pending, confirmed, completed, cancelled)

### 💳 Payments
- [ ] Stripe integration
- [ ] Charge on booking / deposit support
- [ ] Payment status tracking
- [ ] Refunds & cancellations

### 📧 Notifications
- [ ] Email confirmation on booking
- [ ] Reminder emails before appointment
- [ ] Cancellation/status update emails

### ⚙️ Infrastructure
- [x] Environment-based configuration (`.env`)
- [x] Database migrations
- [x] Docker support
- [x] Deployment-ready (Render / Heroku)
