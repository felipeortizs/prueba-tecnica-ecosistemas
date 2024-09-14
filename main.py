import sqlite3
import pandas as pd
import os
import win32com.client as win32

# Ruta de la base de datos
db_path = r'C:\Users\Felipe Ortiz\Documents\Bancolombia\Prueba Bancolombia\database.sqlite'

# Conectar a la base de datos SQLite
conn = sqlite3.connect(db_path)

# Query para extraer los datos del CTE_FINAL, filtrando por commerce_status 'Active' y el rango de fechas
query = """
WITH CTE_APICALL AS (
    SELECT 
        date_api_call,
        commerce_id,
        ask_status,
        is_related
    FROM
        APICALL
),
CTE_COMMERCE AS (
    SELECT
        commerce_id,
        commerce_nit,
        commerce_name,
        commerce_status,
        commerce_email
    FROM
        COMMERCE
),
CTE_FINAL AS (
    SELECT
        AC.date_api_call, 
        AC.ask_status, 
        AC.is_related, 
        C.commerce_nit, 
        C.commerce_name, 
        C.commerce_status, 
        C.commerce_email
    FROM 
        CTE_APICALL AC
    LEFT JOIN
        CTE_COMMERCE C
        ON AC.commerce_id = C.commerce_id
    WHERE C.commerce_status = 'Active'  -- Solo registros activos
    AND DATE_API_CALL BETWEEN '2024-07-01' AND '2024-09-01'
)
SELECT * FROM CTE_FINAL
"""

# Ejecutar la consulta y cargar los datos en un DataFrame
df = pd.read_sql_query(query, conn)

# Cerrar la conexión
conn.close()

# Crear una columna 'month' con el formato 'YYYY-MM'
df['month'] = pd.to_datetime(df['date_api_call']).dt.to_period('M')

# Agrupar por comercio y mes, y contar las peticiones exitosas y no exitosas
df_final = df.groupby(['commerce_name', 'month', 'commerce_nit', 'commerce_email']).agg(
    successful_requests=pd.NamedAgg(column='ask_status', aggfunc=lambda x: (x == 'Successful').sum()),
    unsuccessful_requests=pd.NamedAgg(column='ask_status', aggfunc=lambda x: (x == 'Unsuccessful').sum())
).reset_index()

# Función para calcular la comisión según las reglas de negocio
def calcular_comision(row):
    successful = row['successful_requests']
    unsuccessful = row['unsuccessful_requests']
    commerce_nit = row['commerce_nit']
    
    if commerce_nit == 445470636:  # Innovexa Solutions
        return successful * 300
    elif commerce_nit == 198818316:  # QuantumLeap Inc
        return successful * 600
    elif commerce_nit == 452680670:  # NexaTech Industries
        if 0 <= successful <= 10000:
            return successful * 250
        elif 10001 <= successful <= 20000:
            return successful * 200
        elif successful > 20001:
            return successful * 170
    elif commerce_nit == 28960112:  # Zenith Corp
        commission = successful * (250 if successful <= 22000 else 130)
        if unsuccessful > 6000:
            commission *= 0.95  # Descuento del 5%
        return commission
    elif commerce_nit == 919341007:  # FusionWave Enterprises
        commission = successful * 300
        if 2500 <= unsuccessful <= 4500:
            commission *= 0.95  # Descuento del 5%
        elif unsuccessful > 4501:
            commission *= 0.92  # Descuento del 8%
        return commission
    return 0

# Aplicar la función de comisiones a cada fila del DataFrame
df_final['commission_amount'] = df_final.apply(calcular_comision, axis=1)

# Calcular IVA y valor total
df_final['valor_iva'] = df_final['commission_amount'] * 0.19
df_final['valor_total'] = df_final['commission_amount'] + df_final['valor_iva']

# Renombrar columnas para que coincidan con el formato solicitado
df_final.rename(columns={
    'month': 'FECHA_MES',
    'commerce_name': 'NOMBRE',
    'commerce_nit': 'NIT',
    'commission_amount': 'VALOR_COMISION',
    'valor_iva': 'VALOR_IVA',
    'valor_total': 'VALOR_TOTAL',
    'commerce_email': 'CORREO'
}, inplace=True)

# Asegurarse de que los valores de comisión e IVA estén en el formato adecuado
df_final['VALOR_COMISION'] = df_final['VALOR_COMISION'].map('{:,.2f}'.format)
df_final['VALOR_IVA'] = df_final['VALOR_IVA'].map('{:,.2f}'.format)
df_final['VALOR_TOTAL'] = df_final['VALOR_TOTAL'].map('{:,.2f}'.format)

# Ruta donde se guardarán los archivos .xlsx
output_dir = r'C:\Users\Felipe Ortiz\Documents\Bancolombia\Prueba Bancolombia'

# Crear un directorio para almacenar los archivos si no existe
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Función para enviar correo electrónico
def enviar_correo(destinatario, tabla_df, archivo_adjunto):
    # Crear el objeto Outlook
    outlook = win32.Dispatch('outlook.application')
    mail = outlook.CreateItem(0)
    
    # Configurar los detalles del correo
    mail.Subject = 'Resumen de Facturación - Julio y Agosto 2024'
    mail.To = destinatario
    
    # Convertir la tabla de pandas en HTML para el cuerpo del correo
    tabla_html = tabla_df.to_html(index=False, justify='center', border=1)
    
    # Cuerpo del mensaje con la tabla
    mail.HTMLBody = f"""
    <p>Estimado(a),</p>
    <p>A continuación, encontrará el resumen de las facturas correspondientes a los meses de julio y agosto de 2024.</p>
    {tabla_html}
    <p>En el archivo adjunto encontrará más detalles.</p>
    <p>Saludos cordiales,</p>
    """
    
    # Adjuntar el archivo .xlsx
    mail.Attachments.Add(archivo_adjunto)
    
    # Enviar el correo
    mail.Send()
    print(f'Correo enviado a {destinatario}')

# Agrupar los datos por cada cliente y generar el archivo Excel correspondiente
for nombre, group in df_final.groupby('NOMBRE'):
    # Crear un archivo .xlsx para cada cliente con los datos de dos meses
    file_name = os.path.join(output_dir, f'{nombre}_factura.xlsx')
    
    # Exportar los datos de los dos meses para el cliente
    group[['FECHA_MES', 'NOMBRE', 'NIT', 'successful_requests', 'unsuccessful_requests', 'VALOR_COMISION', 'VALOR_IVA', 'VALOR_TOTAL']].to_excel(file_name, index=False)
    
    print(f'Archivo generado para {nombre}: {file_name}')
    
    # Enviar correo con la tabla de pandas y el archivo adjunto
    destinatario = group['CORREO'].values[0]  # Obtener el correo del cliente
    enviar_correo(destinatario, group[['FECHA_MES', 'NOMBRE', 'NIT', 'VALOR_COMISION', 'VALOR_IVA', 'VALOR_TOTAL']], file_name)
