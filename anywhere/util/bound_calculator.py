from math import radians, asin, cos, sin, atan2, degrees


def destination(lat, lon, bearing, distance):
    radius = 6378.137
    r_lat = radians(lat)
    r_lon = radians(lon)
    r_bearing = radians(bearing)
    r_ang_dist = distance / radius

    r_lat_bound = asin(sin(r_lat) * cos(r_ang_dist) +
                       cos(r_lat) * sin(r_ang_dist) * cos(r_bearing))

    r_lon_bound = r_lon + atan2(sin(r_bearing) * sin(r_ang_dist) * cos(r_lat),
                                cos(r_ang_dist) - sin(r_lat) * sin(r_lat_bound))

    return {"lat": degrees(r_lat_bound), "lon": degrees(r_lon_bound)}


def get_bound(lat, lon, distance):
    north = destination(lat, lon, 0, distance)
    east = destination(lat, lon, 90, distance)
    south = destination(lat, lon, 180, distance)
    west = destination(lat, lon, 270, distance)
    return dict(lon_upper_bound=east['lon'], lon_lower_bound=west['lon'], lat_upper_bound=north['lat'],
                lat_lower_bound=south['lat'])
