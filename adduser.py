import sqlite3
from werkzeug.security import generate_password_hash,check_password_hash
DATABASE = 'instance/database.db'
con= sqlite3.connect(DATABASE)    
cur = con.cursor() 
username = "admin"
password = 'Radiosystem2023!'
hashed_password = generate_password_hash(password)
con.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
con.commit()
cur.close()
print("OK")