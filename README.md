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
