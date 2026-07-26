BookingsPRO Backend

Un backend en Flask + PostgreSQL para una plataforma de reservas multi-tenant.
Proporciona APIs REST para gestionar inquilinos, usuarios, servicios, disponibilidad, reservas y más.
Soporta configuración por entornos, Docker y despliegue en Render o Heroku.

🚀 Características

Arquitectura multi-tenant.

CRUD para inquilinos, usuarios y servicios.

Configuración local sencilla con pipenv.

Listo para desplegar en Render o Heroku.

Variables de entorno gestionadas mediante .env.

📦 Instalación

Puedes ejecutar este proyecto con Docker o con Python 3.13 instalado en tu sistema.

Clona el repositorio:

```sh
git clone https://github.com/Sharguidev/BookingsPRO-Backend.git
cd BookingsPRO-Backend
```

Instala las dependencias con pipenv:

```sh
pipenv install
psql -U root -c 'CREATE DATABASE example;'

```

Crea el archivo de migraciones:

```sh
pipenv run init
```

## Migraciones

```sh
pipenv run migrate
pipenv run upgrade
```

## Inicializa el entorno

```sh
pipenv shell
```

## Configura tus variables de entorno

```sh
cp .env.example .env

```

## Cómo empezar a codificar

Hay una API de ejemplo funcionando con una base de datos de ejemplo.
Todo tu código de aplicación debe escribirse dentro de la carpeta ./src/.

src/app.py (donde debes programar tus endpoints)

src/models.py (tus tablas de base de datos y lógica de serialización)

src/utils.py (clases y funciones reutilizables)

src/admin.py (añade tus modelos al admin y gestiona tus datos fácilmente)

## Ejecutar la aplicación

```sh
pipenv run start
```

## Generar un diagrama de la base de datos

```sh
pipenv run diagram
```

## ☁️ Despliegue

Este boilerplate está 100% listo para desplegarse con Render.com y Heroku en minutos. Por favor, lee la [documentación oficial sobre ello](https://start.4geeksacademy.com/deploy).

## 📜 Licencia

Ver el archivo LICENSE.md (in English) o LICENSE.es.md (en español) para más información.
