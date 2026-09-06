# crear_excel_prueba.py — correr una sola vez para generar el archivo de test
import pandas as pd

data = [
    {
        "Nombre": "Juan", "Apellidos": "Pérez", "Rut": "12345678-9",
        "Genero": "M", "Fecha_Nacimiento": "2010-05-14", "Comuna": "Temuco",
        "Telefono": "912345678", "Correo_Electronico": "juan@test.cl",
        "N°Prueba": "50L", "tiempo": "28,45",
        "N°Prueba.1": "100L", "tiempo.1": "1'02,10",
        "N°Prueba.2": "", "tiempo.2": "",
    },
    {
        "Nombre": "María", "Apellidos": "Soto", "Rut": "98765432-1",
        "Genero": "F", "Fecha_Nacimiento": "2011-08-20", "Comuna": "Padre Las Casas",
        "Telefono": "987654321", "Correo_Electronico": "maria@test.cl",
        "N°Prueba": "100P", "tiempo": "1'15.30",
        "N°Prueba.1": "", "tiempo.1": "",
        "N°Prueba.2": "", "tiempo.2": "",
    },
    {
        "Nombre": "Diego", "Apellidos": "Muñoz", "Rut": "",
        "Genero": "M", "Fecha_Nacimiento": "2009-03-02", "Comuna": "Temuco",
        "Telefono": "911223344", "Correo_Electronico": "diego@test.cl",
        "N°Prueba": "200L", "tiempo": "2:15.00",
        "N°Prueba.1": "50E", "tiempo.1": "35.20",
        "N°Prueba.2": "100M", "tiempo.2": "1\"12.50",
    },
]

df = pd.DataFrame(data)
df.to_excel("excel_prueba_roster.xlsx", index=False)
print("Excel de prueba creado: excel_prueba_roster.xlsx")