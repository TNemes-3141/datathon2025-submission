import pycountry
from countryinfo import CountryInfo
from functools import lru_cache

@lru_cache(maxsize=None)
def get_country_info(country_name):
    try:
        return CountryInfo(country_name).info()
    except Exception:
        return {}

def get_nationality_from_alpha3(alpha3_code):
    try:
        country = pycountry.countries.get(alpha_3=alpha3_code.upper())
        if not country:
            return "Unknown"
        
        country_info = get_country_info(country.name)
        demonyms = country_info.get("demonym", "Unknown")
        return demonyms
    except Exception as e:
        return f"Error: {e}"

# Examples
for i in range(0, 1000):
    get_nationality_from_alpha3("USA")