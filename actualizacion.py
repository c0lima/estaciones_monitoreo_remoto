'''utilities'''

from ftplib import FTP
from datetime import datetime

'''variables'''

file_name = 'main.py'

'''code'''

def obtenerFecha():
    fecha = datetime.now()
    fecha = fecha.strftime('%d.%m.%Y-%H:%M:%S')
    return str(fecha)

def run():
    
    fecha = obtenerFecha()
        
    ftp = FTP(host = 'ftp.factoriaccp.cl', user = 'colima@factoriaccp.cl', passwd = 'cupcake12345*')
    ftp.cwd('/calidad_de_agua/raspberry/5.2-1/')
    try:
        list = ftp.nlst()
        print(list)
        if "main.py" in list:
            localfile = open(file_name, 'wb')
            ftp.retrbinary('RETR ' + file_name, localfile.write, 1024)
            localfile.close()
            ftp.mkd(fecha)
            ftp.rename(file_name, fecha + '/' + file_name)
        else:
            print("No existe el archivo")

    except:
        print('No existe el archivo')
    
    print("Fin Code")
    ftp.quit()

if __name__ == "__main__":
    run()    
