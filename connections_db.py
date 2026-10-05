import pyodbc

CONNECTION_STRING = "Driver={SQL Server};Server=primno4;Database=Robbyson;Trusted_Connection=yes;"
CONN = pyodbc.connect(CONNECTION_STRING)

def insert_logger(relatorio, inicio, fim, status, erro):
    cur = CONN.cursor()
    cur.execute("insert into dbo.pbi_logger (logger_time, report, start_att, end_att, status_att, error) values (getdate(), ?, ?, ?, ?, ?)", (relatorio, inicio, fim, status, erro,))
    cur.close()
    return
    
def truncate_logger():
    cur = CONN.cursor()
    cur.execute("truncate table dbo.pbi_logger")
    cur.close()
    return

def close_connection():
    CONN.close()