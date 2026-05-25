# Odoo

[![Build Status](https://runbot.odoo.com/runbot/badge/flat/1/master.svg)](https://runbot.odoo.com/runbot)
[![Tech Doc](https://img.shields.io/badge/master-docs-875A7B.svg?style=flat&colorA=8F8F8F)](https://www.odoo.com/documentation/master)
[![Help](https://img.shields.io/badge/master-help-875A7B.svg?style=flat&colorA=8F8F8F)](https://www.odoo.com/forum/help-1)
[![Nightly Builds](https://img.shields.io/badge/master-nightly-875A7B.svg?style=flat&colorA=8F8F8F)](https://nightly.odoo.com/)

Odoo is a suite of web based open source business apps.

The main Odoo Apps include an [Open Source CRM](https://www.odoo.com/page/crm),
[Website Builder](https://www.odoo.com/app/website),
[eCommerce](https://www.odoo.com/app/ecommerce),
[Warehouse Management](https://www.odoo.com/app/inventory),
[Project Management](https://www.odoo.com/app/project),
[Billing &amp; Accounting](https://www.odoo.com/app/accounting),
[Point of Sale](https://www.odoo.com/app/point-of-sale-shop),
[Human Resources](https://www.odoo.com/app/employees),
[Marketing](https://www.odoo.com/app/social-marketing),
[Manufacturing](https://www.odoo.com/app/manufacturing),
[...](https://www.odoo.com/)

Odoo Apps can be used as stand-alone applications, but they also integrate seamlessly so you get
a full-featured [Open Source ERP](https://www.odoo.com) when you install several Apps.

## Getting started with Odoo

For a standard installation please follow the [Setup instructions](https://www.odoo.com/documentation/master/administration/install/install.html)
from the documentation.

To learn the software, we recommend the [Odoo eLearning](https://www.odoo.com/slides),
or [Scale-up, the business game](https://www.odoo.com/page/scale-up-business-game).
Developers can start with [the developer tutorials](https://www.odoo.com/documentation/master/developer/howtos.html).

## Security

If you believe you have found a security issue, check our [Responsible Disclosure page](https://www.odoo.com/security-report)
for details and get in touch with us via email.


# Activate the virtual environment
source venv/bin/activate

# Run odoo
python odoo-bin -c odoo.conf --dev=all

# Update module
python odoo-bin -c odoo.conf -u simple_module -d odoo_db --stop-after-init
python odoo-bin -c odoo.conf -u task_manager -d odoo_db --stop-after-init
python odoo-bin -c odoo.conf -u dl_wood_payroll -d odoo_db --stop-after-init

# Create new module
python odoo-bin scaffold task_manager my_custom_addons
python odoo-bin scaffold dl_wood_payroll my_custom_addons

Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
pip install -r requirements.txt

#
python odoo-bin -c odoo.conf -u dl_salary_kpi -d odoo_db_production --stop-after-init
python odoo-bin -c odoo.conf --dev=all

python odoo-bin -c odoo.conf -u dl_wood_traceability -d odoo_db --stop-after-init
python odoo-bin -c odoo.conf --dev=all

./venv/bin/python odoo-bin -c odoo.conf -u dl_wood_traceability -d odoo_db_production --stop-after-init