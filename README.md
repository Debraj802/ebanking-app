# ebanking-app
🏦 E-Banking System (Flask + MySQL)
A secure, feature-rich online banking web application built with Python Flask, MySQL database, and HTML/CSS/JavaScript frontend. This system allows users to create bank accounts, perform transactions, and manage their finances with a 6-digit security PIN.

https://img.shields.io/badge/Python-3.8%252B-blue
https://img.shields.io/badge/Flask-2.3.2-green
https://img.shields.io/badge/MySQL-8.0-orange
https://img.shields.io/badge/License-MIT-yellow

📋 Table of Contents
Features

Technology Stack

System Requirements

Installation Guide

Database Setup

Configuration

Running the Application

Project Structure

Screenshots

API Endpoints

Security Features

Testing

Contributing

License

Contact

Account Management :-
Create New Account: Users can create a bank account with personal details

Unique Account Number: System generates 10-digit unique account number

Security PIN: 6-digit PIN generated securely during account creation

Account Details: View account information, balance, and last transaction

Delete Account: Permanently delete account (with zero balance check)

Banking Operations:-
Balance Inquiry: Check current available balance

Deposit Money: Add funds to account (with validation)

Withdraw Money: Withdraw funds (with balance check and limits)

Fund Transfer: Transfer money to other accounts

Transaction History: View recent transactions

Security Features :- 
6-digit PIN Authentication: System-generated secure PIN

One-time PIN Display: PIN shown only once during account creation

Session Management: 30-minute session timeout

Login Attempt Logging: Tracks failed login attempts

Input Validation: Both client-side and server-side validation

SQL Injection Prevention: Parameterized queries

XSS Protection: Jinja2 autoescaping

Secure Headers: Cache control for sensitive pages

📱 User Interface
Responsive Design: Works on desktop, tablet, and mobile

Real-time Validation: Instant feedback on form inputs

Flash Messages: User-friendly notifications

Print & Download: Save account credentials

Copy to Clipboard: Easy account number copying

Technology Stack for Backend
Python 3.8+: Core programming language

Flask 2.3.2: Web framework

Flask-MySQLdb: MySQL database connector

Werkzeug: WSGI web application library

python-dotenv: Environment variable management

Database
MySQL 8.0: Relational database management system

SQLAlchemy (optional): ORM for database operations

Frontend
HTML5: Structure

CSS3: Styling and responsive design

JavaScript: Client-side interactivity and validation

Jinja2: Template engine

System Requirements and Prerequisites :-
Python 3.8 or higher

MySQL 8.0 or higher

pip (Python package manager)

virtualenv (recommended)

Supported Operating Systems
Windows 10/11

macOS 10.15+

Linux (Ubuntu 20.04+, CentOS 8+)

Feel Free to Contact:-
DEBRAJ MONDAL
debrajmondal3839@gmail.com
+91 8900399794
