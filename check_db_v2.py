
import os
import sys

# Setup Odoo environment
# ... (assuming we can run a script that bootstraps Odoo)
# Since we are in a terminal, I'll just check if the column is in DB again but with a better method.

import psycopg2

try:
    conn = psycopg2.connect("dbname='odoo_db' user='sonzai' host='localhost'")
    cur = conn.cursor()
    
    # Check columns for dl_salary_kpi_attendance_type
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'dl_salary_kpi_attendance_type' AND column_name = 'company_id';")
    if cur.fetchone():
        print("DB CHECK: dl_salary_kpi_attendance_type.company_id EXISTS in DB")
    else:
        print("DB CHECK: dl_salary_kpi_attendance_type.company_id MISSING in DB")
        
    # Check columns for dl_tax_department
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'dl_tax_department' AND column_name = 'company_id';")
    if cur.fetchone():
        print("DB CHECK: dl_tax_department.company_id EXISTS in DB")
    else:
        print("DB CHECK: dl_tax_department.company_id MISSING in DB")
        
    cur.close()
    conn.close()
except Exception as e:
    print(f"DB CHECK FAILED: {e}")
