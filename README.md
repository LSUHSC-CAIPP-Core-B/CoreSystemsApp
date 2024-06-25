#  Core Systems Application
[![][black-shield]][black]

[black]: https://www.lsuhs.edu/centers/center-for-applied-immunology-and-pathological-processes/bioinformatics-modeling-core
[black-shield]: https://img.shields.io/badge/LSUHS-CAIPP_Modelling_Core-FFBF00.svg?style=for-the-badge&labelColor=purple
[![PyPI - Implementation](https://img.shields.io/pypi/implementation/flask?logo=python)](https://pypi.org/project/Flask/) [![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pandas?logo=pandas&label=pandas)](https://pypi.org/project/pandas/) [![PyPI - Python Version](https://img.shields.io/pypi/pyversions/FuzzyWuzzy?logo=python&label=FuzzyWuzzy)](https://pypi.org/project/fuzzywuzzy/)
 [![GitHub commit activity](https://img.shields.io/github/commit-activity/t/LSUHSC-CAIPP-Core-B/CoreSystemsApp?logo=github)](https://github.com/LSUHSC-CAIPP-Core-B/CoreSystemsApp/commits/main/) [![GitHub last commit](https://img.shields.io/github/last-commit/LSUHSC-CAIPP-Core-B/CoreSystemsApp?logo=github)](https://github.com/LSUHSC-CAIPP-Core-B/CoreSystemsApp/commits/main/)

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

The app is separated into a few parts based on access level required and functionality.

###  Login

You have to login into your account the access the app. Each user have different roles that grant specific access.

Login system is implemented with *flask_login* with added custom roles. The roles are:

- Admin

- User

- Core B

- Core C

Only super admins can add and delete users and other admins to the app. It can be done in the Authentication/Admin panel module.

  

####  Login access

![App flow](docs/Core_App_entry_flow.png)

###  Core B
For more details see [CoreB](app/CoreB/README.md)

###  Core C
For more details see [CoreC](app/CoreC/README.md).

##  Reader

Extension to read specific .csv data files. Orders from the CAIPP request Google form are parsed byt his module to keep the prefered format for data edition and display and to keep the .csv updatable by keeping it in the same format as it is downloaded from the Google form.

  

##  PdfWriter

Extension to edit invoice PDF files. It gets a dictionary and puts the data to predefined invoice template.