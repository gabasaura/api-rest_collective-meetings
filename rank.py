from models import Timeslot, db  # Importa desde models

def calculate_rankings(meeting_id):
    """
    Calcula el ranking de los slots basándose en las coincidencias.
    """
    # Obtener todos los timeslots para la reunión
    timeslots = Timeslot.query.filter_by(meeting_id=meeting_id).all()
    
    # Inicializar un diccionario para contar coincidencias
    slot_counts = {}
    
    # Contar las coincidencias para cada slot
    for slot in timeslots:
        key = (slot.day, slot.block)
        if key not in slot_counts:
            slot_counts[key] = 0
        if slot.available:
            slot_counts[key] += 1
    
    # Ordenar los slots por el número de coincidencias, de mayor a menor
    sorted_slots = sorted(slot_counts.items(), key=lambda x: x[1], reverse=True)
    
    # Crear un ranking con los 3 mejores slots
    rankings = [{'day': day, 'block': block, 'count': count} for (day, block), count in sorted_slots[:3]]
    
    return rankings
