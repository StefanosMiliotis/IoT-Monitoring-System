from fastapi import FastAPI
from psydantic import BaseModel #for data validation and settings management
import os 
import psycopg2 

app = FastAPI()  #δημιουργια αντικειμενου εφαρμογης fastapi , πανω του οριζονται τα endpoints 
# Database connection parameters from environment variables
DB_HOST = os.getenv("DB_HOST", "timescaledb") 
DB_NAME = os.getenv("DB_NAME", "iot_db") 
DB_USER = os.getenv("DB_USER", "user") 
DB_PASS = os.getenv("DB_PASS", "password") 

def get_db_connection(): 
#με docker-compose up , το docker προσπαθει να συνδεθει στην database ,
#αν δεν ειναι ετοιμη θα περιμενει και θα ξαναπροσπαθησει μετα απο 2 δευτερολεπτα
#fastapi ειναι πιο ελαφρυ απο timescaledb οποτε ξεκιναει πιο γρηγορα
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
#δημιουργια κλασης DataQuery που κληρονομει απο BaseModel της βιβλιοθηκης Pydantic
#για να ορισουμε το format των δεδομενων που θα λαμβανουμε απο τα αιτηματα στο endpoint /query
    device_name: str #ονομα της συσκευης που θελουμε να αναζητησουμε
    start_day: str #ημερομηνια εναρξης για την αναζητηση των δεδομενων 
    end_day: str #ημερομηνια ληξης για την αναζητηση των δεδομενων

@app.get("/") #root endpoint : http get endpoint στο root path ("/") που επιστρέφει ένα απλό μήνυμα
def read_root():
    return {"Project": "IoT Monitoring System", "Status": "Live"} 

# 1ο Endpoint: Επιστρέφει τα RAW data
@app.post("/raw/data")
def get_raw_data(query: DataQuery): 
    conn = get_db_connection() #συνδεση στην database με την συναρτηση get_db_connection() που ορισαμε παραπανω
    cur = conn.cursor(cursor_factory=RealDictCursor) #δημιουργια cursor για εκτελεση SQL queries , με RealDictCursor για να επιστρεφει τα αποτελεσματα ως λεξικα (dict) αντι για tuples
    
    # SQL query που φιλτράρει με βάση το JSON
    sql = """
        SELECT * FROM sensors_data 
        WHERE device_name = %s 
          AND timestamp >= %s 
          AND timestamp <= %s
        ORDER BY timestamp ASC;
    """ #επιλογη ολων των στηλων απο τον πινακα sensors_data που πληρουν τις συνθηκες φιλτραρισματος (device_name, start_day, end_day) και ταξινομηση με βαση το timestamp σε αυξουσα σειρα
    cur.execute(sql, (query.device_name, query.start_day, query.end_day)) #εκτελεση του SQL query με τα παραμετρους που λαμβανουμε απο το DataQuery αντικειμενο (query.device_name, query.start_day, query.end_day)
    results = cur.fetchall() #αποθηκευση ολων των αποτελεσματων του query σε μια μεταβλητη results (θα ειναι μια λιστα απο λεξικα, καθε λεξικο αντιπροσωπευει μια γραμμη απο τον πινακα sensors_data)
    
    cur.close() #κλεισιμο του cursor μετα την ολοκληρωση της εργασιας του
    conn.close() #κλεισιμο της συνδεσης με την database μετα την ολοκληρωση της εργασιας του
    return results 

# 2ο Endpoint: Επιστρέφει το Άθροισμα (SUM)
@app.post("/sum/data")
def get_sum_data(query: DataQuery):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # SQL query που υπολογίζει το άθροισμα απευθείας στη βάση
    sql = """
        SELECT SUM(value) as total_sum FROM sensors_data 
        WHERE device_name = %s 
          AND timestamp >= %s 
          AND timestamp <= %s;
    """ 
    #επιλογη του αθροισματος της στηλης value απο τον πινακα sensors_data που πληρουν τις συνθηκες φιλτραρισματος (device_name, start_day, end_day)
    cur.execute(sql, (query.device_name, query.start_day, query.end_day)) #εκτελεση του SQL query με τα παραμετρους που λαμβανουμε απο το DataQuery αντικειμενο (query.device_name, query.start_day, query.end_day)
    result = cur.fetchone() #αποθηκευση του αποτελεσματος του query σε μια μεταβλητη result (θα ειναι ενα λεξικο με το κλειδι 'total_sum' που αντιπροσωπευει το αθροισμα των τιμων που πληρουν τις συνθηκες φιλτραρισματος)
    
    cur.close()
    conn.close()
    
    # Αν δεν βρεθούν μετρήσεις, το sum είναι None, οπότε επιστρέφουμε 0
    total = result['total_sum'] if result['total_sum'] is not None else 0
    
    return {
        "device_name": query.device_name, #ονομα της συσκευης που ζητηθηκε
        "total_sum": total #το αθροισμα των τιμων που πληρουν τις συνθηκες φιλτραρισματος (ή 0 αν δεν βρεθηκαν μετρησεις)
    }