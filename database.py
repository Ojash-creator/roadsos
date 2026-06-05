"""
RoadSoS Database Setup
Creates and populates the SQLite database with emergency services data.
"""
import sqlite3
import math
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "roadsos.db")


def create_tables(conn):
    cur = conn.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS countries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        emergency_number TEXT,
        ambulance_number TEXT,
        police_number TEXT,
        fire_number TEXT
    );

    CREATE TABLE IF NOT EXISTS states (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        country_code TEXT NOT NULL,
        code TEXT NOT NULL,
        name TEXT NOT NULL,
        UNIQUE(country_code, code)
    );

    CREATE TABLE IF NOT EXISTS emergency_services (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        country_code TEXT NOT NULL,
        state_code TEXT,
        city TEXT NOT NULL,
        name TEXT NOT NULL,
        service_type TEXT NOT NULL,  -- hospital | ambulance | police | fire | towing | puncture | rescue
        address TEXT,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        phone TEXT,
        phone_alt TEXT,
        is_24x7 INTEGER DEFAULT 1,
        has_trauma_centre INTEGER DEFAULT 0,
        has_icu INTEGER DEFAULT 0,
        distance_km REAL,            -- populated at query time
        rating REAL,
        notes TEXT
    );

    CREATE INDEX IF NOT EXISTS idx_service_type ON emergency_services(service_type);
    CREATE INDEX IF NOT EXISTS idx_country ON emergency_services(country_code);
    CREATE INDEX IF NOT EXISTS idx_city ON emergency_services(city);
    """)
    conn.commit()


def seed_data(conn):
    cur = conn.cursor()

    # ── Countries ──────────────────────────────────────────────────────────────
    countries = [
        ("IN", "India",         "112", "108", "100", "101"),
        ("US", "United States", "911", "911", "911", "911"),
        ("GB", "United Kingdom","999", "999", "999", "999"),
        ("AU", "Australia",     "000", "000", "000", "000"),
        ("SG", "Singapore",     "995", "995", "999", "995"),
    ]
    cur.executemany(
        "INSERT OR IGNORE INTO countries VALUES (NULL,?,?,?,?,?,?)", countries
    )

    # ── States ─────────────────────────────────────────────────────────────────
    states = [
        ("IN","TN","Tamil Nadu"),("IN","MH","Maharashtra"),("IN","DL","Delhi"),
        ("IN","KA","Karnataka"),("IN","TS","Telangana"),("IN","KL","Kerala"),
        ("IN","AP","Andhra Pradesh"),("IN","GJ","Gujarat"),("IN","RJ","Rajasthan"),
        ("IN","WB","West Bengal"),
    ]
    cur.executemany("INSERT OR IGNORE INTO states VALUES (NULL,?,?,?)", states)

    # ── Emergency Services ─────────────────────────────────────────────────────
    services = [
        # ── Chennai ──────────────────────────────────────────────────────────
        ("IN","TN","Chennai","Government Royapettah Hospital","hospital",
         "Royapettah High Rd, Chennai","13.0543","80.2635","044-28193333",None,1,1,1,None,4.1,"Level-1 Trauma Centre"),
        ("IN","TN","Chennai","STANLEY Medical College Hospital","hospital",
         "Old Jail Rd, Chennai","13.1024","80.2787","044-25281435",None,1,1,1,None,4.0,"Govt trauma centre"),
        ("IN","TN","Chennai","Apollo Hospitals Greams Road","hospital",
         "21 Greams Lane, Chennai","13.0603","80.2499","044-28290200",None,1,1,1,None,4.5,"Private trauma centre"),
        ("IN","TN","Chennai","GEM Hospital","hospital",
         "45 Pankaja Mill Rd, Chennai","13.0068","80.2206","044-45458585",None,1,1,1,None,4.3,"Multispecialty"),
        ("IN","TN","Chennai","Tamil Nadu Ambulance Service (108)","ambulance",
         "Chennai Central","13.0827","80.2707","108",None,1,0,0,None,4.5,"State emergency ambulance"),
        ("IN","TN","Chennai","Chennai Police Control Room","police",
         "Commissioner's Office, Vepery","13.0871","80.2656","100","044-28447777",1,0,0,None,4.2,"24x7 PCR"),
        ("IN","TN","Chennai","V4U Vehicle Recovery & Towing","towing",
         "Poonamallee High Rd, Chennai","13.0565","80.1986","9841012345",None,1,0,0,None,4.0,"Flatbed & crane"),
        ("IN","TN","Chennai","Kumar Tyre & Puncture Shop","puncture",
         "Anna Salai, Chennai","13.0514","80.2590","9841055678",None,0,0,0,None,3.8,"Tyre repair & vulcanising"),

        # ── Hyderabad ─────────────────────────────────────────────────────────
        ("IN","TS","Hyderabad","NIMS Hospital (Nizam's Institute)","hospital",
         "Punjagutta, Hyderabad","17.4284","78.4497","040-23360026",None,1,1,1,None,4.4,"Premier trauma & neuro"),
        ("IN","TS","Hyderabad","Osmania General Hospital","hospital",
         "Afzalgunj, Hyderabad","17.3793","78.4743","040-24600007",None,1,1,1,None,4.0,"Govt Level-2 trauma"),
        ("IN","TS","Hyderabad","Apollo Hospitals Jubilee Hills","hospital",
         "Jubilee Hills Rd No. 59, Hyderabad","17.4239","78.4088","040-23607777",None,1,1,1,None,4.5,"Private trauma centre"),
        ("IN","TS","Hyderabad","EMRI 108 Ambulance – Telangana","ambulance",
         "Khairatabad, Hyderabad","17.4230","78.4574","108",None,1,0,0,None,4.6,"EMRI Emergency ambulance"),
        ("IN","TS","Hyderabad","Hyderabad City Police – PCR","police",
         "Basheerbagh, Hyderabad","17.4090","78.4710","100","040-27852435",1,0,0,None,4.1,"City PCR"),
        ("IN","TS","Hyderabad","Falcon Towing Services","towing",
         "Secunderabad, Hyderabad","17.4399","78.4983","9000123456",None,1,0,0,None,4.2,"24x7 vehicle towing"),

        # ── Mumbai ────────────────────────────────────────────────────────────
        ("IN","MH","Mumbai","KEM Hospital","hospital",
         "Acharya Donde Marg, Parel, Mumbai","18.9978","72.8432","022-24107000",None,1,1,1,None,4.3,"Govt trauma centre"),
        ("IN","MH","Mumbai","Lilavati Hospital","hospital",
         "Bandra Reclamation, Mumbai","19.0596","72.8295","022-26751000",None,1,1,1,None,4.5,"Private multispecialty"),
        ("IN","MH","Mumbai","EMRI 108 – Maharashtra","ambulance",
         "Mumbai","18.9388","72.8354","108",None,1,0,0,None,4.4,"State ambulance service"),
        ("IN","MH","Mumbai","Mumbai Police Control Room","police",
         "Crawford Market, Mumbai","18.9440","72.8342","100","022-22621855",1,0,0,None,4.3,"PCR Mumbai"),
        ("IN","MH","Mumbai","Quick Tow Mumbai","towing",
         "Andheri West, Mumbai","19.1182","72.8464","9820012345",None,1,0,0,None,4.0,"Highway breakdown"),

        # ── Bengaluru ─────────────────────────────────────────────────────────
        ("IN","KA","Bengaluru","Victoria Hospital","hospital",
         "K R Market, Bengaluru","12.9669","77.5737","080-26703000",None,1,1,1,None,4.0,"Govt trauma & burns"),
        ("IN","KA","Bengaluru","Manipal Hospitals (Old Airport Rd)","hospital",
         "98 HAL Airport Rd, Bengaluru","12.9592","77.6482","080-25024444",None,1,1,1,None,4.5,"Private trauma"),
        ("IN","KA","Bengaluru","EMRI 108 Karnataka","ambulance",
         "Bengaluru Central","12.9716","77.5946","108",None,1,0,0,None,4.5,"EMRI ambulance"),
        ("IN","KA","Bengaluru","Bengaluru City Police","police",
         "Infantry Road, Bengaluru","12.9812","77.6054","100","080-22942222",1,0,0,None,4.1,"PCR Bengaluru"),

        # ── Delhi ─────────────────────────────────────────────────────────────
        ("IN","DL","Delhi","AIIMS Trauma Centre","hospital",
         "Ansari Nagar, New Delhi","28.5672","77.2100","011-26588500",None,1,1,1,None,4.8,"Premier national trauma"),
        ("IN","DL","Delhi","Safdarjung Hospital","hospital",
         "Ansari Nagar West, New Delhi","28.5685","77.2080","011-26165060",None,1,1,1,None,4.3,"Govt multispecialty"),
        ("IN","DL","Delhi","Delhi Ambulance Service (102/108)","ambulance",
         "New Delhi","28.6139","77.2090","108","102",1,0,0,None,4.4,"Delhi govt ambulance"),
        ("IN","DL","Delhi","Delhi Police PCR","police",
         "ITO, New Delhi","28.6271","77.2421","100","011-23490000",1,0,0,None,4.2,"PCR Delhi"),
        ("IN","DL","Delhi","Highway Rescue Towing – NH44","towing",
         "NH44 Service Road, Delhi","28.6800","77.2300","9811200200",None,1,0,0,None,4.1,"NH towing & rescue"),

        # ── Kolkata ───────────────────────────────────────────────────────────
        ("IN","WB","Kolkata","SSKM Hospital (PG Hospital)","hospital",
         "AJC Bose Road, Kolkata","22.5448","88.3426","033-22041734",None,1,1,1,None,4.1,"Govt trauma Level-1"),
        ("IN","WB","Kolkata","Apollo Gleneagles Kolkata","hospital",
         "Canal Circular Rd, Kolkata","22.5741","88.3989","033-23203040",None,1,1,1,None,4.4,"Private trauma"),
        ("IN","WB","Kolkata","EMRI 108 West Bengal","ambulance",
         "Kolkata","22.5726","88.3639","108",None,1,0,0,None,4.3,"EMRI ambulance"),
        ("IN","WB","Kolkata","Kolkata Police Control Room","police",
         "Lalbazar, Kolkata","22.5794","88.3525","100","033-22141312",1,0,0,None,4.1,"PCR Kolkata"),

        # ── Pune ──────────────────────────────────────────────────────────────
        ("IN","MH","Pune","Sassoon General Hospital","hospital",
         "Near Pune Station, Pune","18.5236","73.8737","020-26128000",None,1,1,1,None,4.0,"Govt Level-1 trauma"),
        ("IN","MH","Pune","Ruby Hall Clinic","hospital",
         "Sassoon Rd, Pune","18.5195","73.8841","020-66455555",None,1,1,1,None,4.5,"Private trauma"),
        ("IN","MH","Pune","EMRI 108 – Pune","ambulance",
         "Pune","18.5204","73.8567","108",None,1,0,0,None,4.3,"EMRI ambulance"),
        ("IN","MH","Pune","Pune City Police Control Room","police",
         "Shivajinagar, Pune","18.5308","73.8474","100","020-26123346",1,0,0,None,4.0,"PCR Pune"),

        # ── International ─────────────────────────────────────────────────────
        ("US","","New York City","Bellevue Hospital Center","hospital",
         "462 First Ave, New York, NY","40.7397","-73.9754","212-562-4141",None,1,1,1,None,4.3,"Level-1 Trauma NYC"),
        ("US","","New York City","NYC Emergency Services","ambulance",
         "New York","40.7128","-74.0060","911",None,1,0,0,None,4.7,"FDNY/NYPD EMS"),
        ("GB","","London","St Thomas' Hospital","hospital",
         "Westminster Bridge Rd, London","51.4990","-0.1188","020-7188-7188",None,1,1,1,None,4.5,"Major trauma centre"),
        ("GB","","London","London Ambulance Service","ambulance",
         "London","51.5074","-0.1278","999",None,1,0,0,None,4.7,"NHS Ambulance London"),
        ("AU","","Sydney","Royal Prince Alfred Hospital","hospital",
         "Missenden Rd, Camperdown, Sydney","-33.8890","151.1877","02-9515-6111",None,1,1,1,None,4.4,"Level-1 Trauma Sydney"),
        ("AU","","Sydney","NSW Ambulance","ambulance",
         "Sydney","-33.8688","151.2093","000",None,1,0,0,None,4.6,"NSW Ambulance service"),
        ("SG","","Singapore","Singapore General Hospital","hospital",
         "Outram Rd, Singapore","1.2793","103.8354","6321-4311",None,1,1,1,None,4.5,"Major trauma centre SG"),
        ("SG","","Singapore","SCDF Ambulance","ambulance",
         "Singapore","1.3521","103.8198","995",None,1,0,0,None,4.8,"Singapore Civil Defence"),
    ]

    cur.executemany("""
        INSERT OR IGNORE INTO emergency_services
        (country_code,state_code,city,name,service_type,address,latitude,longitude,
         phone,phone_alt,is_24x7,has_trauma_centre,has_icu,distance_km,rating,notes)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, services)
    conn.commit()
    print(f"✅ Seeded {len(services)} emergency service records.")


def haversine(lat1, lon1, lat2, lon2):
    """Return distance in km between two lat/lon points."""
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2*R*math.asin(math.sqrt(a))


def find_nearby(lat: float, lon: float, service_type: str = None,
                country_code: str = None, radius_km: float = 50, limit: int = 5):
    """Query nearby emergency services sorted by distance."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    query = "SELECT * FROM emergency_services WHERE 1=1"
    params = []
    if service_type:
        query += " AND service_type = ?"
        params.append(service_type)
    if country_code:
        query += " AND country_code = ?"
        params.append(country_code)

    rows = cur.execute(query, params).fetchall()
    conn.close()

    results = []
    for row in rows:
        dist = haversine(lat, lon, float(row["latitude"]), float(row["longitude"]))
        if dist <= radius_km:
            r = dict(row)
            r["distance_km"] = round(dist, 2)
            results.append(r)

    results.sort(key=lambda x: x["distance_km"])
    return results[:limit]


def get_emergency_numbers(country_code: str):
    """Return national emergency numbers for a country."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    row = cur.execute(
        "SELECT * FROM countries WHERE code = ?", (country_code.upper(),)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


if __name__ == "__main__":
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    create_tables(conn)
    seed_data(conn)
    conn.close()
    print(f"✅ Database ready at {DB_PATH}")
