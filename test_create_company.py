try:
    company = env['res.company'].create({
        'name': 'Test Company 123'
    })
    print("Company created:", company.id)
    env.cr.rollback()
except Exception as e:
    import traceback
    traceback.print_exc()
