import qrcode

def create_qr_code(url, filename="qrcode.png"):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill="black", back_color="white")
    img.save(filename)
    print(f"QR code saved as {filename}")

# Παράδειγμα χρήσης
url = input("Δώσε το URL: ")
create_qr_code(url)
