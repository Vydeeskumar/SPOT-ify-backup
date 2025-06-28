def calculate_points(time_taken):
    if time_taken <= 10:
        return 8
    elif time_taken <= 20:
        return 5
    elif time_taken <= 30:
        return 4
    elif time_taken <= 45:
        return 3
    elif time_taken <= 60:
        return 2
    else:
        return 1