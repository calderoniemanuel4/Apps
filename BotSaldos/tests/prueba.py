from decimal import Decimal
try:
    print(Decimal('1.500.000'.replace('.','')))
except  Exception :
    print ('Error : no se pudo convertir')
