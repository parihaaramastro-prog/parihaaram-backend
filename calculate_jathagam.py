import swisseph as swe
import json
import sys
from datetime import datetime, timedelta

# Constants for Vedic Astrology
RASHI_NAMES = [
    {"en": "Aries", "ta": "மேஷம்"},
    {"en": "Taurus", "ta": "ரிஷபம்"},
    {"en": "Gemini", "ta": "மிதுனம்"},
    {"en": "Cancer", "ta": "கடகம்"},
    {"en": "Leo", "ta": "சிம்மம்"},
    {"en": "Virgo", "ta": "கன்னி"},
    {"en": "Libra", "ta": "துலாம்"},
    {"en": "Scorpio", "ta": "விருச்சிகம்"},
    {"en": "Sagittarius", "ta": "தனுசு"},
    {"en": "Capricorn", "ta": "மகரம்"},
    {"en": "Aquarius", "ta": "கும்பம்"},
    {"en": "Meena", "ta": "மீனம்"}
]

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta",
    "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

DASHA_LORDS = [
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"
]

DASHA_YEARS = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7, 
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17
}

SOLAR_YEAR_DAYS = 365.2425

def calculate_navamsa_sign_from_degree(longitude):
    total_longitude = float(longitude) % 360
    base_sign_idx = int(total_longitude / 30)
    rem_deg = total_longitude % 30
    nav_idx = int(rem_deg / (3.3333333333333335))
    
    if base_sign_idx in [0, 3, 6, 9]:
        offset = 0
    elif base_sign_idx in [1, 4, 7, 10]:
        offset = 8
    else:
        offset = 4
        
    nav_sign_idx = (base_sign_idx + offset + nav_idx) % 12
    return nav_sign_idx

def calculate_vimshottari_hierarchy(birth_dt, moon_long):
    """
    4-level hierarchical Vimshottari Dasha
    Output: JSON with mahadashas list
    """
    naks_len = 13.333333333333334
    naks_idx = int(moon_long / naks_len)
    start_lord_idx = naks_idx % 9
    
    rem_deg_in_naks = naks_len - (moon_long % naks_len)
    fraction_left = rem_deg_in_naks / naks_len
    
    mahadashas = []
    current_start = birth_dt
    now = datetime.now()
    
    for i in range(9):
        idx = (start_lord_idx + i) % 9
        m_lord = DASHA_LORDS[idx]
        m_years = DASHA_YEARS[m_lord]
        
        actual_m_years = m_years * (fraction_left if i == 0 else 1.0)
        m_duration_days = actual_m_years * SOLAR_YEAR_DAYS
        m_end = current_start + timedelta(days=m_duration_days)
        
        m_entry = {
            "planet": m_lord,
            "start_date": current_start.strftime("%Y-%m-%d"),
            "end_date": m_end.strftime("%Y-%m-%d"),
            "is_current": current_start <= now <= m_end,
            "bhuktis": []
        }
        
        # Calculate all Bhuktis for this Mahadasha
        b_start_lord_idx = idx
        # Internal time precision: use a full 120-year relative start for Bhuktis
        b_rel_start = current_start
        if i == 0:
            # For the first mahadasha, the bhuktis also need to be balanced
            # Standard way: calculate all bhuktis of this lord and filter
            pass

        # To keep it consistently hierarchical:
        # Calculate 9 bhuktis starting from mahadasha lord
        total_m_years = m_years
        for j in range(9):
            b_idx = (b_start_lord_idx + j) % 9
            b_lord = DASHA_LORDS[b_idx]
            b_years = DASHA_YEARS[b_lord]
            b_duration_days = (total_m_years * b_years / 120.0) * SOLAR_YEAR_DAYS
            b_end = b_rel_start + timedelta(days=b_duration_days)
            
            # Intersection with Mahadasha actual period
            if b_end > current_start:
                actual_b_start = max(b_rel_start, current_start)
                actual_b_end = min(b_end, m_end)
                
                if actual_b_start < actual_b_end:
                    b_entry = {
                        "planet": b_lord,
                        "start_date": actual_b_start.strftime("%Y-%m-%d"),
                        "end_date": actual_b_end.strftime("%Y-%m-%d"),
                        "is_current": actual_b_start <= now <= actual_b_end,
                        "pratyantardashas": []
                    }
                    
                    # Calculate Pratyantardashas
                    p_start_lord_idx = b_idx
                    p_rel_start = actual_b_start
                    # Bhukti duration used for proportion
                    b_days_total = b_duration_days 
                    
                    for k in range(9):
                        p_idx = (p_start_lord_idx + k) % 9
                        p_lord = DASHA_LORDS[p_idx]
                        p_years = DASHA_YEARS[p_lord]
                        # P duration = (B_duration * P_years) / 120
                        p_duration_days = (b_days_total * p_years) / 120.0
                        p_end = p_rel_start + timedelta(days=p_duration_days)
                        
                        actual_p_start = max(p_rel_start, actual_b_start)
                        actual_p_end = min(p_end, actual_b_end)
                        
                        if actual_p_start < actual_p_end:
                            p_entry = {
                                "planet": p_lord,
                                "start_date": actual_p_start.strftime("%Y-%m-%d"),
                                "end_date": actual_p_end.strftime("%Y-%m-%d"),
                                "is_current": actual_p_start <= now <= actual_p_end,
                                "sookshma_dashas": []
                            }
                            
                            # Sookshma Dashas
                            s_start_lord_idx = p_idx
                            s_rel_start = actual_p_start
                            p_days_total = p_duration_days
                            
                            for l in range(9):
                                s_idx = (s_start_lord_idx + l) % 9
                                s_lord = DASHA_LORDS[s_idx]
                                s_years = DASHA_YEARS[s_lord]
                                s_duration_days = (p_days_total * s_years) / 120.0
                                s_end = s_rel_start + timedelta(days=s_duration_days)
                                
                                actual_s_start = max(s_rel_start, actual_p_start)
                                actual_s_end = min(s_end, actual_p_end)
                                
                                if actual_s_start < actual_s_end:
                                    p_entry["sookshma_dashas"].append({
                                        "planet": s_lord,
                                        "start_date": actual_s_start.strftime("%Y-%m-%d"),
                                        "end_date": actual_s_end.strftime("%Y-%m-%d"),
                                        "is_current": actual_s_start <= now <= actual_s_end
                                    })
                                s_rel_start = s_end
                            
                            b_entry["pratyantardashas"].append(p_entry)
                        p_rel_start = p_end
                        
                    m_entry["bhuktis"].append(b_entry)
            b_rel_start = b_end
            
        mahadashas.append(m_entry)
        current_start = m_end
        if (current_start - birth_dt).days / 365.25 > 105: break
        
    return mahadashas

def calculate_jathagam(y, m, d, h, mn, lat, lon):
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    jd = swe.julday(y, m, d, h + mn/60.0)
    flags = swe.FLG_SIDEREAL | swe.FLG_SPEED
    
    bodies = {
        "Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS, 
        "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER, 
        "Venus": swe.VENUS, "Saturn": swe.SATURN, "Rahu": swe.TRUE_NODE
    }
    
    planet_positions = []
    navamsa_planets = []
    for name, bid in bodies.items():
        res, ret_flags = swe.calc_ut(jd, bid, flags)
        long = res[0]
        planet_positions.append({"name": name, "longitude": long, "rasi_idx": int(long / 30) % 12, "degrees": long % 30})
        n_sign_idx = calculate_navamsa_sign_from_degree(long)
        navamsa_planets.append({"planet": name, "rasi_idx": n_sign_idx, "sign": RASHI_NAMES[n_sign_idx]["en"]})
        if name == "Rahu":
            k_long = (long + 180) % 360
            planet_positions.append({"name": "Ketu", "longitude": k_long, "rasi_idx": int(k_long / 30) % 12, "degrees": k_long % 30})
            kn_sign_idx = calculate_navamsa_sign_from_degree(k_long)
            navamsa_planets.append({"planet": "Ketu", "rasi_idx": kn_sign_idx, "sign": RASHI_NAMES[kn_sign_idx]["en"]})

    houses, ascmc = swe.houses_ex(jd, lat, lon, b'W', flags)
    lagna_long = ascmc[0]
    nav_lagna_idx = calculate_navamsa_sign_from_degree(lagna_long)
    for p in navamsa_planets:
        p["house"] = (p["rasi_idx"] - nav_lagna_idx + 12) % 12 + 1

    moon = next(p for p in planet_positions if p["name"] == "Moon")
    naks_len = 13.333333333333334
    naks_idx = int(moon["longitude"] / naks_len)
    
    birth_dt = datetime(y, m, d, int(h), int(mn))
    mahadashas = calculate_vimshottari_hierarchy(birth_dt, moon["longitude"])

    return {
        "metadata": {
            "type": "Vimshottari Dasha Hierarchy",
            "system": "South Indian Vedic Astrology",
            "ayanamsa": "Lahiri",
            "precision": "Time-based internal, date-based output"
        },
        "lagna": {"idx": int(lagna_long / 30) % 12, "name": RASHI_NAMES[int(lagna_long / 30) % 12]["en"], "name_ta": RASHI_NAMES[int(lagna_long / 30) % 12]["ta"]},
        "navamsa_chart": {
            "lagna": {"rasi_idx": nav_lagna_idx, "sign": RASHI_NAMES[nav_lagna_idx]["en"], "house": 1},
            "planets": navamsa_planets
        },
        "moon_sign": {"idx": int(moon["longitude"] / 30) % 12, "name": RASHI_NAMES[int(moon["longitude"] / 30) % 12]["en"], "name_ta": RASHI_NAMES[int(moon["longitude"] / 30) % 12]["ta"]},
        "nakshatra": {"name": NAKSHATRAS[naks_idx], "idx": naks_idx, "padam": int((moon["longitude"] % naks_len) / (naks_len / 4.0)) + 1},
        "planets": planet_positions,
        "mahadashas": mahadashas,
        "predictions": [] # Predictions can be derived from lords
    }

if __name__ == "__main__":
    try:
        args = sys.argv[1:]
        y, m, d, h, mn, lat, lon = map(float, args)
        result = calculate_jathagam(int(y), int(m), int(d), int(h), int(mn), lat, lon)
        print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
