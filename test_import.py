import sys, os
sys.path.append(os.path.abspath('my_custom_addons'))
try:
    from dl_salary_kpi.models import dl_salary_kpi_month
    print("Import SUCCESS")
except Exception as e:
    import traceback
    traceback.print_exc()
