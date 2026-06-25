# Convenience file for creating the sqlite3 database
import sqlite3

connection = sqlite3.connect("stock.db")
cursor = connection.cursor()

with open("schema.sql", "r") as file:
    schema_script = file.read()

cursor.executescript(schema_script)

connection.commit()
connection.close()