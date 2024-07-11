# Core C
## Table of Contents 
- [Introduction](#Introduction)
- [Key Features](#Key-Features)
- [Database Configuration](#database-configuration)

## Introduction
Advancements in flow cytometry technology have enabled a growing array of antibody and fluorochrome combinations for scientific inquiry. However, this expanded capability brings technical and financial challenges. The upfront investment in antibodies and panels can be prohibitive, discouraging experimentation. As more labs adopt flow cytometry, redundancy and waste in antibody use increase. Our solution, integrated within an immunophenotyping core facility, addresses these issues by facilitating cost-sharing and easing financial barriers. We have developed a user-friendly computer program tailored to our campus environment for antibody sharing and tracking.

## Key Features
- Antibodies
    - A comprehensive system designed to help users easily search for, filter, and collect detailed antibody data.
    - Gives users the ability to download a selection of antibodies
- Stock
    - A comprehensive system designed to help users easily track supplies in a lab

## Database Configuration
To ensure proper data manipulation, the database schema must adhere to the following structure:
##### Antibodies
``` sql
-- Antibodies table
CREATE TABLE Antibodies_Stock(
    Stock_ID INT AUTO_INCREMENT Primary key,
    Box_Name VARCHAR(64),
    Company_Name VARCHAR(64),
    Catalog_Num VARCHAR(64),
    Target_Name VARCHAR(64),
    Target_Species VARCHAR(64),
    Fluorophore VARCHAR(64),
    Clone_Name VARCHAR(64),
    Isotype VARCHAR(64),
    Size VARCHAR(64),
    Concentration VARCHAR(64),
    Expiration_Date DATE,
    Titration INT,
    Cost FLOAT,
    Cost_Per_Sample VARCHAR(64),
    Included TINYINT                        
) AUTO_INCREMENT = 1;
```
##### Stock
``` sql
-- ORDER INFORMATION TABLE
CREATE TABLE Order_Info(
    Product_Num INT AUTO_INCREMENT primary key,
    Company_Name VARCHAR(64),
    Catalog_Num VARCHAR(64),
    Unit_Price FLOAT(25),
    Product_Name VARCHAR(64)
);

-- STOCK INFORMATION TABLE
CREATE TABLE Stock_Info (
    Product_Num INT Primary key,
    Quantity INT,
    FOREIGN KEY (Product_Num) REFERENCES Order_info(Product_Num)
);
```
##### Panels
In Progress...
```sql
-- PANEL LIST TABLE
CREATE TABLE predefined_panels(
    Panel_id INT AUTO_INCREMENT Primary key,
    Panel_Name VARCHAR(64)          
) AUTO_INCREMENT = 1;

-- PANEL TABLE
CREATE TABLE panel_name(
    stock_id INT Primary key,
    FOREIGN KEY (stock_id) REFERENCES Antibodies_Stock(Stock_ID)
);
```