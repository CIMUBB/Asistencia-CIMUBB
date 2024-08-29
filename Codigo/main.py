import cv2
import requests
import time
from pyzbar.pyzbar import decode
from urllib.parse import urlparse, parse_qs

# URL de tu aplicación web de Google Apps Script
web_app_url = 'https://script.google.com/macros/s/AKfycbx50YUb6m-niROa5dBVo9UixE9EFHNkl7H5NC-MPSuf4cfJ5eETcAQaDiq5Wd1LZdXS/exec'

# Inicia la captura de video
cap = cv2.VideoCapture(0)
def get_parameters(url):
    parsed_url = urlparse(url)
    parameters = parse_qs(parsed_url.query)
    return parameters

def validar_run(run):
    # utilizar API para validar RUN
    return "NO"


def scan_qr_code():
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error al acceder a la cámara.")
            break
        
        # Decodifica el código QR
        for barcode in decode(frame):
            qr_data = barcode.data.decode("utf-8")
            
            if qr_data != "":
                print(f"Datos del QR: {qr_data}")
                
                urlparameters = get_parameters(qr_data)
                run = urlparameters['RUN'][0]
                validacion = validar_run(run)
                time.sleep(1)
                # Enviar los datos a la aplicación web de Google Apps Script
                response = requests.post(web_app_url, data={'RUN': run, 'VALIDACION': validacion})
                
                if response.status_code == 200:
                    print("Datos enviados a la aplicación web")
                else:
                    print("Error al enviar los datos a la aplicación web")

        # Muestra el video
        cv2.imshow("QR Code Scanner", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    scan_qr_code()