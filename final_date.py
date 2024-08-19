from collections import defaultdict
from models import Timeslot

def calculate_final_date(timeslot):
    """
    Calcula la fecha final según las disponibilidades.

    :param available_dates: Lista de fechas disponibles por cada usuario.
    :return: La fecha final que tiene más coincidencias.
    """
    date_counter = defaultdict(int)

    # Contar cuántas veces aparece cada fecha
    for date in timeslot:
        date_counter[date] += 1

    # Ordenar las fechas por número de coincidencias (de mayor a menor)
    sorted_dates = sorted(date_counter.items(), key=lambda x: x[1], reverse=True)

    # Retornar la fecha con más coincidencias (o la primera en caso de empate)
    if sorted_dates:
        return sorted_dates[0][0]

    return None
