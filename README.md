#  Core Systems Application
[![][black-shield]][black]

[black]: https://www.lsuhs.edu/centers/center-for-applied-immunology-and-pathological-processes/bioinformatics-modeling-core
[black-shield]: https://img.shields.io/badge/LSUHS-CAIPP_Modelling_Core-FFBF00.svg?style=for-the-badge&labelColor=purple
[![PyPI - Implementation](https://img.shields.io/pypi/implementation/flask?logo=python)](https://pypi.org/project/Flask/) [![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pandas?logo=pandas&label=pandas)](https://pypi.org/project/pandas/) [![PyPI - Python Version](https://img.shields.io/pypi/pyversions/FuzzyWuzzy?logo=python&label=FuzzyWuzzy)](https://pypi.org/project/fuzzywuzzy/)
 [![GitHub commit activity](https://img.shields.io/github/commit-activity/t/LSUHSC-CAIPP-Core-B/CoreSystemsApp?logo=github)](https://github.com/LSUHSC-CAIPP-Core-B/CoreSystemsApp/commits/main/) 

![Title](docs/title.png)

A lightweight and highly cutomizable free web system using Flask. CoreSystemsApp is a comprehensive web application developed by the LSUHSC-CAIPP Core B team. It is designed to manage systems in Bioinformatics and Modeling Cores B and C, providing various core functionalities essential for these operations.

![System Design](docs/Core_Systems_App_Design.png)

Ensures that users have appropriate permissions and can perform operations on the database safely. It involves client-side application logic, server-side processing, and communication via APIs.

## Table of Contents 
- [Setup](#Setup) 
- [Web App](#Web-App) 
    - [Login](#Login) 
    - [Core B](#Core-B) 
    - [Core C](#Core-C)
- [Reader](#Reader)
- [PdfWriter](#PdfWriter)

##  Setup

Python version required: 3.9.*

Create environment with:

`python3 -m venv <venv_name>`

or this for specific version of python installed:

`python3.9 -m venv <venv_name>`

Activate the environment with:

`source <venv_name>/bin/activate`

Install requirements with:

`pip install -r requirements.txt`

  

###  Mac OS

`brew install redis`

`brew services start redis`

  

###  Ubuntu

`sudo apt-get install redis`

  

##  Web App

The app is divided into several sections based on required access levels and functionality.

###  Login

You must log in to your account to access the app. Each user has a specific role that grants them different levels of access.

The login system is implemented with *flask_Login* and includes custom roles. Roles:

- Admin

- User

- Core B

- Core C

Only super admins can add and delete users, including other admins, within the app. This functionality is available in the Authentication/Admin panel module.

  

####  Login access

![App flow](docs/Core_App_entry_flow.png)

###  Core B
For more details see [CoreB](app/CoreB/README.md)

###  Core C
Antibody sharing and tracking system

For more details see [CoreC](app/CoreC/README.md).

##  Reader

This extension reads specific .csv data files. It parses orders from the CAIPP request Google form, ensuring the data maintains the preferred format for editing and display. Additionally, it keeps the .csv files updatable by preserving the original format as downloaded from the Google form.

##  PdfWriter

This extension allows for editing invoice PDF files. It takes a dictionary of data and populates a predefined invoice template accordingly.