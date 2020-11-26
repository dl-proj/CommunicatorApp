# KivyApp

## Overview
This project is to communicate with some sensors called client and display the necessary information to analyze from the database that client 
saves the data from the machine.
The Kivy framework is used for GUI and SQLite3 is used as a database.

## Structure

- src

    The source code for database management, GUI and communication

- utils

    The source code for folder/file management, calender show, data process

- app

    The main execution file
    
- requirements

    All the dependencies for this project
    
- settings
    
    Several settings including database file
    
## Installation

- Environment
    
    Ubuntu 18.04, Windows 10, Python 3.6

- Dependency Installation

    Please run the following command in this project directory in the terminal.
    ```
    pip3 install -r requirements.txt
    ```
  
- Extra Installation for kivy

    Please run the following command in the terminal.
    ```
    sudo apt-get install xclip xsel    
    ``` 

## Execution

- Please run the following command in the terminal

    ```
    python3 app.py
    ```
