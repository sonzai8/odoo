import xmlrpc.client
url = 'http://localhost:8069'
common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
print(common.version())
