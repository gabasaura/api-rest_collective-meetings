import random
import hashlib
import time


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

def generate_meeting_hash(title, creator_email):
    # Crear un hash único basado en el título de la reunión, correo del creador y timestamp
    unique_string = f"{title}-{creator_email}-{time.time()}"
    return hashlib.sha256(unique_string.encode()).hexdigest()

