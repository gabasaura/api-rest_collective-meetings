import random
import hashlib

def generate_random_color():
    """
    Genera un código de color hexadecimal aleatorio, excluyendo negro y blanco.
    Este color se usará dentro del contexto de una reunión.
    """
    excluded_colors = ['#FFFFFF', '#000000']
    color = None

    while not color or color in excluded_colors:
        color = "#{:06x}".format(random.randint(0, 0xFFFFFF))

    return color

def generate_password_hash(title):
    """
    Genera un hash SHA-256 del título de la reunión que se usará como hash de la contraseña.
    """
    return hashlib.sha256(title.encode()).hexdigest()
