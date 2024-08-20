from collections import defaultdict
from models import Timeslot  # Asegúrate de importar tu modelo Timeslot

def calculate_final_date(meeting_id):
    """
    Calcula la fecha final según las disponibilidades de los participantes en una reunión.

    :param meeting_id: ID de la reunión para la que se están calculando las fechas.
    :return: La fecha final que tiene más coincidencias (y el bloque), o None si no hay coincidencias.
    """
    date_counter = defaultdict(int)

    # Recuperar todos los bloques de tiempo (timeslots) asociados a la reunión
    timeslots = Timeslot.query.filter_by(meeting_id=meeting_id).all()

    # Contar cuántas veces aparece cada fecha en los bloques de tiempo
    for timeslot in timeslots:
        date_key = (timeslot.date, timeslot.block)  # Agrupar por fecha y bloque
        date_counter[date_key] += 1

    # Ordenar las fechas por número de coincidencias (de mayor a menor)
    sorted_dates = sorted(date_counter.items(), key=lambda x: x[1], reverse=True)

    # Retornar la fecha y bloque con más coincidencias (o la primera en caso de empate)
    if sorted_dates:
        return sorted_dates[0][0]  # Retorna una tupla (fecha, bloque)

    return None
