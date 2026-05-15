
import psycopg2
import sys

try:
    conn = psycopg2.connect("dbname='odoo_db' user='sonzai' host='localhost'")
    cur = conn.cursor()
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'dl_salary_kpi_attendance_type';")
    columns = [row[0] for row in cur.fetchall()]
    print(f"Columns in dl_salary_kpi_attendance_type: {columns}")
    
    if 'company_id' in columns:
        print(">>> SUCCESS: company_id column exists in database.")
    else:
        print(">>> ERROR: company_id column NOT found in database.")
        
    cur.close()
    conn.close()
except Exception as e:
    print(f"Connection failed: {e}")
