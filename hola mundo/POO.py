"""
Concepto    Qué hace

__init__    inicializa variables
self.x      variable de instancia
_x          “protegida” (convención)
getter      leer valor
setter      modificar con control
@property   getter elegante
@x.setter   setter elegante
"""

print("\033c") # borra pantalla
class Wizard: # Nombres con mayuscula
    def __init__(self,name) -> None:
        if not name :
            raise ValueError('Missing name')
        self.name = name
    def __str__(self):
        return f'Name {self.name}'
    @classmethod
    def get(cls): # este metodo se puede usar en las subclases
        name = input ('Nombre: ')
        return cls(name,'-') # el segundo argumento lo paso porque las subclases lo piden
    
## HERENCIA
class Student(Wizard):
    def __init__(self, name, house) -> None:
        super().__init__(name)
        self.house = house

class Professor(Wizard):
    def __init__(self, name,subject) -> None:
        super().__init__(name)
        self.subject = subject

class Usuario:
    def __init__(self, nombre, edad):
        self.nombre = nombre
        self._edad = edad

    @property # Getter Elegante
    def edad(self):
        return self._edad

    @edad.setter # Setter elegante
    def edad(self, valor):
        if valor <= 0:
            raise ValueError("Edad inválida")
        self._edad = valor

def main ():
    student = Student.get()  # usa metodo de la clase
    student.house = 'Pellegrini' # usa metodo de instancia
    professor = Professor( # usa inicializador de la por defecto
        input('Nombre profesor: '),
        input('Subject')
    )
    print (student, professor) # usa metodo de clase __str__
    print(f'{student.name,student.house}\n\n{professor.name,professor.subject}') 
            # accede a las variables de instancia

if __name__ == '__main__':
    main()