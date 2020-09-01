from jarbas_utils.location import geolocate, reverse_geolocate
from pprint import pprint


full_addr = "798 N 1415 Rd, Lawrence, KS 66049, United States"
vague_addr = "Lawrence Kansas"
country = "Portugal"

data = geolocate(country)
pprint(data)


lat = 38.9730682373638
lon = -95.2361831665156

data = reverse_geolocate(lat, lon)

pprint(data)