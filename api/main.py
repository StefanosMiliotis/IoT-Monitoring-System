from fastapi import FastAPI
from pydantic import BaseModel 
import os 
import psycopg2 
from psycopg2.extras import RealDictCursor 
import time

app = FastAPI() #δημιουργια αντικειμενου εφαρμογης fastapi , πανω του οριζονται τα endpoints 
# Database connection parameters from environment variables
DB_HOST = os.getenv("DB_HOST", "db") 
DB_NAME = os.getenv("DB_NAME", "foo") 
DB_USER = os.getenv("DB_USER", "postgres") 
DB_PASS = os.getenv("DB_PASS", "postgres") 

def get_db_connection(): 
# #με docker-compose up , το docker προσπαθει να συνδεθει στην database ,
# #αν δεν ειναι ετοιμη θα περιμενει και θα ξαναπροσπαθησει μετα απο 2 δευτερολεπτα
# #fastapi ειναι πιο ελαφρυ απο timescaledb οποτε ξεκιναει πιο γρηγορα
    while True:
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASS
            )
            return conn
        except Exception as e:
            print(f"Waiting for database... {e}")
            time.sleep(2)

class DataQuery(BaseModel): 
# #δημιουργια κλασης DataQuery που κληρονομει απο BaseModel της βιβλιοθηκης Pydantic
# #για να ορισουμε το format των δεδομενων που θα λαμβανουμε απο τα αιτηματα στο endpoint /query
    device_name: str #ονομα της συσκευης που θελουμε να αναζητησουμε
    start_day: str #ημερομηνια εναρξης για την αναζητηση των δεδομενων
    end_day: str #ημερομηνια ληξης για την αναζητηση των δεδομενων

@app.get("/")  #root endpoint : http get endpoint στο root path ("/") που επιστρέφει ένα απλό μήνυμα
def read_root():
    return {"Project": "IoT Monitoring System", "Status": "Live"} 

# 1ο endpoint επιστρεφει RAW data
@app.post("/raw/data")
def get_raw_data(query: DataQuery): 
    conn = get_db_connection()  #συνδεση στην database με την συναρτηση get_db_connection() που ορισαμε παραπανω
    cur = conn.cursor(cursor_factory=RealDictCursor) #δημιουργια cursor για εκτελεση SQL queries , με RealDictCursor για να επιστρεφει τα αποτελεσματα ως λεξικα (dict) αντι για tuples
    
    #fix : payload αντί για * 
    sql = """
        SELECT timestamp, device_name, payload FROM sensors_data 
        WHERE device_name = %s 
          AND timestamp >= %s 
          AND timestamp <= %s
        ORDER BY timestamp ASC;
    """ #επιλογη στηλων timestamp, device_name, payload απο τον πινακα sensors_data που πληρουν τις συνθηκες φιλτραρισματος (device_name, start_day, end_day) και ταξινομηση με βαση το timestamp σε αυξουσα σειρα
     #εκτελεση του SQL query με τα παραμετρους που λαμβανουμε απο το DataQuery αντικειμενο (query.device_name, query.start_day, query.end_day)
    cur.execute(sql, (query.device_name, query.start_day, query.end_day)) 
    results = cur.fetchall() #αποθηκευση ολων των αποτελεσματων του query σε μια μεταβλητη results 
    
    cur.close() 
    conn.close() 
    return results 

# 2ο endpoint sum data 
@app.post("/sum/data")
def get_sum_data(query: DataQuery):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Χρησιμοποιούμε ->> για να πάρουμε το 'value' μέσα από το payload
    # και το μετατρέπουμε σε numeric για να γίνει το SUM
    sql = """
        SELECT SUM((payload->>'value')::numeric) as total_sum FROM sensors_data 
        WHERE device_name = %s 
          AND timestamp >= %s 
          AND timestamp <= %s;
    """ 
    cur.execute(sql, (query.device_name, query.start_day, query.end_day)) 
    result = cur.fetchone() 
    
    cur.close()
    conn.close()
    
    total = result['total_sum'] if result['total_sum'] is not None else 0
    
    return {
        "device_name": query.device_name,
        "total_sum": total 
    }
