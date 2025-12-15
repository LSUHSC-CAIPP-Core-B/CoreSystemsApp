# CoreB
## Table of Contents 
- [Introduction](#Introduction)
- [Key Features](#Key-Features)
- [Database Configuration](#database-configuration)

## Introduction
In progress...
## Key Features

This section highlights every system that Core B uses which includes the following:

#####  Orders

This module oversees the management of service orders specific to Core B. It includes functionalities to display a comprehensive list of current orders along with various filtering options. Each order is editable and can be deleted as needed. Additionally, the module offers the capability to generate invoices for individual orders.

#####  Invoices

This page presents a history of invoices, consolidating records of past services into a single location. It provides users with filtering capabilities and options for deleting records as necessary.

#####  PI list

Section dedicated to showcasing Principal Investigator (PI) information. Users can add new PIs and edit existing ones. The section also includes filtering and deletion functionalities.

## Database Configuration
To ensure proper data manipulation, the database schema must adhere to the following structure:

#### Orders
```sql
CREATE TABLE `CoreB_Order` (
  `Index` text,
  `Project ID` text,
  `Responsible Person` text,
  `Complete status` text,
  `Bill` text,
  `Paid` text,
  `Authoship Disclosure Agreement` text,
  `Request Date` text,
  `If it is an existing project` text,
  `PI Name` text,
  `Funding Source` text,
  `Account number and billing contact person` text,
  `Project title` text,
  `Project Description` text,
  `Service Type` text,
  `RNA Analysis Service Type` text,
  `DNA Analysis Service Type` text,
  `Protein Analysis Service Type` text,
  `Metabolite Analysis Service Type` text,
  `Organism and Species` text,
  `Data Type` text,
  `Library Preparation` text,
  `Expected sample#` text,
  `Please list all comparisons` text,
  `Expected Completion Time` text,
  `Questions and Special Requirments` text
);
```
#### Invoice
```sql
CREATE TABLE `Invoice` (
  `id` int NOT NULL AUTO_INCREMENT,
  `project_id` text,
  `service_type` text,
  `service_sample_number` bigint DEFAULT NULL,
  `service_sample_price` double DEFAULT NULL,
  `total_price` double DEFAULT NULL,
  `discount_sample_number` bigint DEFAULT NULL,
  `discount_sample_amount` double DEFAULT NULL,
  `discount_reason` text,
  `total_discount` double DEFAULT NULL,
  PRIMARY KEY (`id`)
) AUTO_INCREMENT=300;
```

#### PI Information
```sql
CREATE TABLE `pi_info` (
  `index` bigint NOT NULL AUTO_INCREMENT,
  `PI full name` text,
  `PI ID` text,
  `email` text,
  `Department` text,
  KEY `ix_CoreB_pi_info_index` (`index`)
) AUTO_INCREMENT=61;
```
