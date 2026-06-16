from geopy.distance import geodesic

def impossible_travel(prev_location, new_location, time_diff_hours):

    if not prev_location or not new_location:
        return False

    distance_km = geodesic(prev_location, new_location).km

    if time_diff_hours == 0:
        return False

    speed = distance_km / time_diff_hours

    print("Travel speed:", speed)

    if speed > 900:   # airplane speed threshold
        return True

    return False
