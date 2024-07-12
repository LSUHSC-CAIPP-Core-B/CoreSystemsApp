# App

## Table of Contents 
- [Introduction](#Introduction)
- [Key Features](#Key-Features)
- [Database Configuration](#database-configuration)

## Introduction
The ```routes.py``` files is where the GET and POST request are handled in the API. Whenever adding a new ```routes.py``` ir needs to be registered in the [__init__.py](app/__init__.py) file. Like this:

```py
from app.CoreB.orders import bp as main_bp
app.register_blueprint(main_bp)
```