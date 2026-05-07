months = env['dl.salary.kpi.month'].search([('state', 'in', ['draft', 'lock_normal', 'lock_ot', 'lock_regime'])], limit=1)
if not months:
    print("No open salary month found.")
else:
    month = months[0]
    print(f"Testing on month: {month.name}")
    
    # Get some lines to test
    lines = month.line_ids.filtered(lambda l: l.payroll_internal_salary_minus_bonus > 0 and l.payroll_net_salary_base > 0)
    
    if not lines:
        print("No valid lines to test.")
    else:
        print(f"Found {len(lines)} lines to test KPI generation.")
        
        for line in lines[:20]: # Test first 20 lines
            line.action_generate_kpi_scores()
            
            base_salary = line.dl_tax_base_salary
            kpi_score = line.payroll_kpi_score
            
            expected_min = 0
            expected_max = 0
            
            if base_salary < 4500000:
                expected_min = 50.0
                expected_max = 55.0
            elif base_salary < 5000000:
                expected_min = 55.0
                expected_max = 60.0
            else:
                expected_min = 60.0
                expected_max = 70.0
                
            print(f"Line {line.employee_id.name} - Base Salary: {base_salary:,.0f} -> KPI Score: {kpi_score:.2f} (Expected: {expected_min}-{expected_max})")
            if kpi_score < expected_min and line.payroll_cash_amount > 0:
                print("  [WARNING] KPI score is BELOW minimum but cash > 0. This shouldn't happen.")
            if kpi_score > expected_max:
                print("  [ERROR] KPI score exceeds maximum!")

        # Rollback changes since this is just a test
        env.cr.rollback()
print('DONE_TESTING')
