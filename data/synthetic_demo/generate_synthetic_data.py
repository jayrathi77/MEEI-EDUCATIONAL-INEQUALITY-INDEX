"""
Synthetic Demo Data Generator
==============================
PURPOSE : Produce clearly-labelled DEMO data for testing the MEEI pipeline.
WARNING : All numbers are randomly generated. They are NOT government statistics,
          NOT NAS scores, NOT UDISE+ observations, and NOT valid research findings.
          A prominent SYNTHETIC DATA banner is displayed in the dashboard whenever
          this dataset is active.

Run:
    python generate_synthetic_data.py
"""

import numpy as np
import pandas as pd
import json
import os
from pathlib import Path
from datetime import datetime, timezone

SEED = 42
rng = np.random.default_rng(SEED)

OUTPUT_DIR = Path(__file__).parent
PROCESSED_DIR = OUTPUT_DIR.parent / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# ── Indian states and Union Territories with all districts ──────────────────
STATES = {
    "Andhra Pradesh": [
        "Alluri Sitharama Raju", "Anakapalli", "Ananthapuramu", "Annamayya", "Bapatla",
        "Chittoor", "Dr. B.R. Ambedkar Konaseema", "East Godavari", "Eluru", "Guntur",
        "Kakinada", "Krishna", "Kurnool", "Nandyal", "NTR", "Palnadu",
        "Parvathipuram Manyam", "Prakasam", "Sri Potti Sriramulu Nellore", "Sri Sathya Sai",
        "Srikakulam", "Tirupati", "Visakhapatnam", "Vizianagaram", "West Godavari", "YSR Kadapa"
    ],
    "Arunachal Pradesh": [
        "Anjaw", "Changlang", "Dibang Valley", "East Kameng", "East Siang",
        "Itanagar Capital Complex", "Kamle", "Kra Daadi", "Kurung Kumey", "Lepa Rada",
        "Lohit", "Longding", "Lower Dibang Valley", "Lower Siang", "Lower Subansiri",
        "Namsai", "Pakke Kessang", "Papum Pare", "Shi Yomi", "Siang",
        "Tawang", "Tirap", "Upper Siang", "Upper Subansiri", "West Kameng", "West Siang"
    ],
    "Assam": [
        "Bajali", "Baksa", "Barpeta", "Biswanath", "Bongaigaon",
        "Cachar", "Charaideo", "Chirang", "Darrang", "Dhemaji",
        "Dhubri", "Dibrugarh", "Dima Hasao", "Goalpara", "Golaghat",
        "Hailakandi", "Hojai", "Jorhat", "Kamrup", "Kamrup Metropolitan",
        "Karbi Anglong", "Karimganj", "Kokrajhar", "Lakhimpur", "Majuli",
        "Morigaon", "Nagaon", "Nalbari", "Sivasagar", "Sonitpur",
        "South Salmara-Mankachar", "Tamulpur", "Tinsukia", "Udalguri", "West Karbi Anglong"
    ],
    "Bihar": [
        "Araria", "Arwal", "Aurangabad", "Banka", "Begusarai",
        "Bhagalpur", "Bhojpur", "Buxar", "Darbhanga", "East Champaran",
        "Gaya", "Gopalganj", "Jamui", "Jehanabad", "Kaimur",
        "Katihar", "Khagaria", "Kishanganj", "Lakhisarai", "Madhepura",
        "Madhubani", "Munger", "Muzaffarpur", "Nalanda", "Nawada",
        "Patna", "Purnia", "Rohtas", "Saharsa", "Samastipur",
        "Saran", "Sheikhpura", "Sheohar", "Sitamarhi", "Siwan",
        "Supaul", "Vaishali", "West Champaran"
    ],
    "Chhattisgarh": [
        "Balod", "Baloda Bazar", "Balrampur", "Bastar", "Bemetara",
        "Bijapur", "Bilaspur", "Dantewada", "Dhamtari", "Durg",
        "Gariaband", "Gaurela-Pendra-Marwahi", "Janjgir-Champa", "Jashpur", "Kabirdham",
        "Kanker", "Khairagarh-Chhuikhadan-Gandai", "Kondagaon", "Korba", "Koriya",
        "Mahasamund", "Manendragarh-Chirmiri-Bharatpur", "Mohla-Manpur-Ambagarh Chouki",
        "Mungeli", "Narayanpur", "Raigarh", "Raipur", "Rajnandgaon",
        "Sakti", "Sarangarh-Bilaigarh", "Sukma", "Surajpur", "Surguja"
    ],
    "Goa": ["North Goa", "South Goa"],
    "Gujarat": [
        "Ahmedabad", "Amreli", "Anand", "Aravalli", "Banaskantha",
        "Bharuch", "Bhavnagar", "Botad", "Chhota Udaipur", "Dahod",
        "Dang", "Devbhumi Dwarka", "Gandhinagar", "Gir Somnath", "Jamnagar",
        "Junagadh", "Kheda", "Kutch", "Mahisagar", "Mehsana",
        "Morbi", "Narmada", "Navsari", "Panchmahal", "Patan",
        "Porbandar", "Rajkot", "Sabarkantha", "Surat", "Surendranagar",
        "Tapi", "Vadodara", "Valsad"
    ],
    "Haryana": [
        "Ambala", "Bhiwani", "Charkhi Dadri", "Faridabad", "Fatehabad",
        "Gurugram", "Hisar", "Jhajjar", "Jind", "Kaithal",
        "Karnal", "Kurukshetra", "Mahendragarh", "Nuh", "Palwal",
        "Panchkula", "Panipat", "Rewari", "Rohtak", "Sirsa",
        "Sonipat", "Yamunanagar"
    ],
    "Himachal Pradesh": [
        "Bilaspur", "Chamba", "Hamirpur", "Kangra", "Kinnaur",
        "Kullu", "Lahaul and Spiti", "Mandi", "Shimla", "Sirmaur",
        "Solan", "Una"
    ],
    "Jharkhand": [
        "Bokaro", "Chatra", "Deoghar", "Dhanbad", "Dumka",
        "East Singhbhum", "Garhwa", "Giridih", "Godda", "Gumla",
        "Hazaribagh", "Jamtara", "Khunti", "Koderma", "Latehar",
        "Lohardaga", "Pakur", "Palamu", "Ramgarh", "Ranchi",
        "Sahebganj", "Seraikela Kharsawan", "Simdega", "West Singhbhum"
    ],
    "Karnataka": [
        "Bagalkote", "Ballari", "Belagavi", "Bengaluru Rural", "Bengaluru Urban",
        "Bidar", "Chamarajanagara", "Chikkaballapura", "Chikkamagaluru", "Chitradurga",
        "Dakshina Kannada", "Davanagere", "Dharwad", "Gadag", "Hassan",
        "Haveri", "Kalaburagi", "Kodagu", "Kolar", "Koppal",
        "Mandya", "Mysuru", "Raichur", "Ramanagara", "Shivamogga",
        "Tumakuru", "Udupi", "Uttara Kannada", "Vijayanagara", "Vijayapura", "Yadgir"
    ],
    "Kerala": [
        "Alappuzha", "Ernakulam", "Idukki", "Kannur", "Kasaragod",
        "Kollam", "Kottayam", "Kozhikode", "Malappuram", "Palakkad",
        "Pathanamthitta", "Thiruvananthapuram", "Thrissur", "Wayanad"
    ],
    "Madhya Pradesh": [
        "Agar Malwa", "Alirajpur", "Anuppur", "Ashoknagar", "Balaghat",
        "Barwani", "Betul", "Bhind", "Bhopal", "Burhanpur",
        "Chhatarpur", "Chhindwara", "Damoh", "Datia", "Dewas",
        "Dhar", "Dindori", "Guna", "Gwalior", "Harda",
        "Hoshangabad (Narmadapuram)", "Indore", "Jabalpur", "Jhabua", "Katni",
        "Khandwa", "Khargone", "Maihar", "Mandla", "Mandsaur",
        "Mauganj", "Morena", "Narsinghpur", "Neemuch", "Niwari",
        "Pandhurna", "Panna", "Raisen", "Rajgarh", "Ratlam",
        "Rewa", "Sagar", "Satna", "Sehore", "Seoni",
        "Shahdol", "Shajapur", "Sheopur", "Shivpuri", "Sidhi",
        "Singrauli", "Tikamgarh", "Ujjain", "Umaria", "Vidisha"
    ],
    "Maharashtra": [
        "Ahmednagar", "Akola", "Amravati", "Aurangabad (Chhatrapati Sambhaji Nagar)", "Beed",
        "Bhandara", "Buldhana", "Chandrapur", "Dhule", "Gadchiroli",
        "Gondia", "Hingoli", "Jalgaon", "Jalna", "Kolhapur",
        "Latur", "Mumbai City", "Mumbai Suburban", "Nagpur", "Nanded",
        "Nandurbar", "Nashik", "Osmanabad (Dharashiv)", "Palghar", "Parbhani",
        "Pune", "Raigad", "Ratnagiri", "Sangli", "Satara",
        "Sindhudurg", "Solapur", "Thane", "Wardha", "Washim", "Yavatmal"
    ],
    "Manipur": [
        "Bishnupur", "Chandel", "Churachandpur", "Imphal East", "Imphal West",
        "Jiribam", "Kakching", "Kamjong", "Kangpokpi", "Noney",
        "Pherzawl", "Senapati", "Tamenglong", "Tengnoupal", "Thoubal", "Ukhrul"
    ],
    "Meghalaya": [
        "East Garo Hills", "East Jaintia Hills", "East Khasi Hills",
        "Eastern West Khasi Hills", "North Garo Hills", "Ri Bhoi",
        "South Garo Hills", "South West Garo Hills", "South West Khasi Hills",
        "West Garo Hills", "West Jaintia Hills", "West Khasi Hills"
    ],
    "Mizoram": [
        "Aizawl", "Champhai", "Hnahthial", "Khawzawl", "Kolasib",
        "Lawngtlai", "Lunglei", "Mamit", "Saitual", "Serchhip", "Siaha"
    ],
    "Nagaland": [
        "Chumoukedima", "Dimapur", "Kiphire", "Kohima", "Longleng",
        "Mokokchung", "Mon", "Niuland", "Noklak", "Peren",
        "Phek", "Shamator", "Tseminyu", "Tuensang", "Wokha", "Zunheboto"
    ],
    "Odisha": [
        "Angul", "Balangir", "Balasore", "Bargarh", "Bhadrak",
        "Boudh", "Cuttack", "Deogarh", "Dhenkanal", "Gajapati",
        "Ganjam", "Jagatsinghpur", "Jajpur", "Jharsuguda", "Kalahandi",
        "Kandhamal", "Kendrapara", "Kendujhar", "Khordha", "Koraput",
        "Malkangiri", "Mayurbhanj", "Nabarangpur", "Nayagarh", "Nuapada",
        "Puri", "Rayagada", "Sambalpur", "Subarnapur", "Sundargarh"
    ],
    "Punjab": [
        "Amritsar", "Barnala", "Bathinda", "Faridkot", "Fatehgarh Sahib",
        "Fazilka", "Ferozepur", "Gurdaspur", "Hoshiarpur", "Jalandhar",
        "Kapurthala", "Ludhiana", "Malerkotla", "Mansa", "Moga",
        "Mohali (SAS Nagar)", "Muktsar", "Pathankot", "Patiala", "Rupnagar",
        "Sangrur", "Shaheed Bhagat Singh Nagar", "Tarn Taran"
    ],
    "Rajasthan": [
        "Ajmer", "Alwar", "Anupgarh", "Balotra", "Banswara",
        "Baran", "Barmer", "Beawar", "Bharatpur", "Bhilwara",
        "Bikaner", "Bundi", "Chittorgarh", "Churu", "Dausa",
        "Deeg", "Dholpur", "Didwana-Kuchaman", "Dudu", "Dungarpur",
        "Ganganagar", "Gangapur City", "Hanumangarh", "Jaipur", "Jaipur Rural",
        "Jaisalmer", "Jalore", "Jhalawar", "Jhunjhunu", "Jodhpur",
        "Jodhpur Rural", "Karauli", "Kekri", "Khairthal-Tijara", "Kota",
        "Kotputli-Behror", "Nagaur", "Neem Ka Thana", "Pali", "Phalodi",
        "Pratapgarh", "Rajsamand", "Salumbar", "Sanchore", "Sawai Madhopur",
        "Shahpura", "Sikar", "Sirohi", "Tonk", "Udaipur"
    ],
    "Sikkim": [
        "Gangtok", "Gyalshing", "Mangan", "Namchi", "Pakyong", "Soreng"
    ],
    "Tamil Nadu": [
        "Ariyalur", "Chengalpattu", "Chennai", "Coimbatore", "Cuddalore",
        "Dharmapuri", "Dindigul", "Erode", "Kallakurichi", "Kancheepuram",
        "Karur", "Krishnagiri", "Madurai", "Mayiladuthurai", "Nagapattinam",
        "Namakkal", "Nilgiris", "Perambalur", "Pudukkottai", "Ramanathapuram",
        "Ranipet", "Salem", "Sivaganga", "Tenkasi", "Thanjavur",
        "Theni", "Thoothukudi", "Tiruchirappalli", "Tirunelveli", "Tirupathur",
        "Tiruppur", "Tiruvallur", "Tiruvannamalai", "Tiruvarur", "Vellore",
        "Viluppuram", "Virudhunagar"
    ],
    "Telangana": [
        "Adilabad", "Bhadradri Kothagudem", "Hanumakonda", "Hyderabad", "Jagtial",
        "Jangaon", "Jayashankar Bhupalpally", "Jogulamba Gadwal", "Kamareddy", "Karimnagar",
        "Khammam", "Komaram Bheem Asifabad", "Mahabubabad", "Mahbubnagar", "Mancherial",
        "Medak", "Medchal-Malkajgiri", "Mulugu", "Nagarkurnool", "Nalgonda",
        "Narayanpet", "Nirmal", "Nizamabad", "Peddapalli", "Rajanna Sircilla",
        "Rangareddy", "Sangareddy", "Siddipet", "Suryapet", "Vikarabad",
        "Wanaparthy", "Warangal", "Yadadri Bhuvanagiri"
    ],
    "Tripura": [
        "Dhalai", "Gomati", "Khowai", "North Tripura", "Sepahijala",
        "South Tripura", "Unakoti", "West Tripura"
    ],
    "Uttar Pradesh": [
        "Agra", "Aligarh", "Ambedkar Nagar", "Amethi", "Amroha",
        "Auraiya", "Ayodhya", "Azamgarh", "Baghpat", "Bahraich",
        "Ballia", "Balrampur", "Banda", "Barabanki", "Bareilly",
        "Basti", "Bhadohi", "Bijnor", "Budaun", "Bulandshahr",
        "Chandauli", "Chitrakoot", "Deoria", "Etah", "Etawah",
        "Farrukhabad", "Fatehpur", "Firozabad", "Gautam Buddha Nagar", "Ghaziabad",
        "Ghazipur", "Gonda", "Gorakhpur", "Hamirpur", "Hapur",
        "Hardoi", "Hathras", "Jalaun", "Jaunpur", "Jhansi",
        "Kannauj", "Kanpur Dehat", "Kanpur Nagar", "Kasganj", "Kaushambi",
        "Kushinagar", "Lakhimpur Kheri", "Lalitpur", "Lucknow", "Maharajganj",
        "Mahoba", "Mainpuri", "Mathura", "Mau", "Meerut",
        "Mirzapur", "Moradabad", "Muzaffarnagar", "Pilibhit", "Pratapgarh",
        "Prayagraj", "Raebareli", "Rampur", "Saharanpur", "Sambhal",
        "Sant Kabir Nagar", "Shahjahanpur", "Shamli", "Shravasti", "Siddharthnagar",
        "Sitapur", "Sonbhadra", "Sultanpur", "Unnao", "Varanasi"
    ],
    "Uttarakhand": [
        "Almora", "Bageshwar", "Chamoli", "Champawat", "Dehradun",
        "Haridwar", "Nainital", "Pauri Garhwal", "Pithoragarh", "Rudraprayag",
        "Tehri Garhwal", "Udham Singh Nagar", "Uttarkashi"
    ],
    "West Bengal": [
        "Alipurduar", "Bankura", "Birbhum", "Cooch Behar", "Dakshin Dinajpur",
        "Darjeeling", "Hooghly", "Howrah", "Jalpaiguri", "Jhargram",
        "Kalimpong", "Kolkata", "Malda", "Murshidabad", "Nadia",
        "North 24 Parganas", "Paschim Bardhaman", "Paschim Medinipur", "Purba Bardhaman", "Purba Medinipur",
        "Purulia", "South 24 Parganas", "Uttar Dinajpur"
    ],
    "Andaman and Nicobar Islands": [
        "Nicobar", "North and Middle Andaman", "South Andaman"
    ],
    "Chandigarh": ["Chandigarh"],
    "Dadra and Nagar Haveli and Daman and Diu": [
        "Dadra and Nagar Haveli", "Daman", "Diu"
    ],
    "Delhi": [
        "Central Delhi", "East Delhi", "New Delhi", "North Delhi", "North East Delhi",
        "North West Delhi", "Shahdara", "South Delhi", "South East Delhi", "South West Delhi", "West Delhi"
    ],
    "Jammu and Kashmir": [
        "Anantnag", "Bandipora", "Baramulla", "Budgam", "Doda",
        "Ganderbal", "Jammu", "Kathua", "Kishtwar", "Kulgam",
        "Kupwara", "Poonch", "Pulwama", "Rajouri", "Ramban",
        "Reasi", "Samba", "Shopian", "Srinagar", "Udhampur"
    ],
    "Ladakh": ["Kargil", "Leh"],
    "Lakshadweep": ["Lakshadweep"],
    "Puducherry": ["Karaikal", "Mahe", "Puducherry", "Yanam"]
}

# Development index proxy: affects base score generation (higher = better baseline)
STATE_DEVELOPMENT = {
    "Kerala": 0.85, "Goa": 0.84, "Chandigarh": 0.84, "Delhi": 0.83,
    "Himachal Pradesh": 0.80, "Tamil Nadu": 0.78, "Punjab": 0.77,
    "Puducherry": 0.77, "Sikkim": 0.76, "Haryana": 0.75,
    "Lakshadweep": 0.75, "Andaman and Nicobar Islands": 0.74,
    "Maharashtra": 0.73, "Gujarat": 0.72, "Karnataka": 0.71,
    "Uttarakhand": 0.70, "Dadra and Nagar Haveli and Daman and Diu": 0.70,
    "Telangana": 0.68, "Andhra Pradesh": 0.67, "Jammu and Kashmir": 0.66,
    "Ladakh": 0.65, "Mizoram": 0.65, "West Bengal": 0.63,
    "Manipur": 0.62, "Meghalaya": 0.61, "Tripura": 0.61,
    "Nagaland": 0.60, "Arunachal Pradesh": 0.58, "Rajasthan": 0.56,
    "Odisha": 0.55, "Chhattisgarh": 0.54, "Assam": 0.53,
    "Madhya Pradesh": 0.50, "Jharkhand": 0.49, "Uttar Pradesh": 0.48,
    "Bihar": 0.45,
}


def make_districts() -> pd.DataFrame:
    records = []
    dist_id = 1
    for state, districts in STATES.items():
        base = STATE_DEVELOPMENT.get(state, 0.60)
        for district in districts:
            records.append({"district_id": f"D{dist_id:03d}",
                            "district_name": district,
                            "state_name": state,
                            "_base": base})
            dist_id += 1
    return pd.DataFrame(records)


def add_performance(df: pd.DataFrame) -> pd.DataFrame:
    b = df["_base"].values
    noise = rng.normal(0, 0.08, len(df))
    df["nas_math_cl3"] = np.clip(b * 100 + noise * 100 + rng.normal(0, 5, len(df)), 20, 100)
    df["nas_lang_cl3"] = np.clip(b * 100 + noise * 100 + rng.normal(0, 5, len(df)), 20, 100)
    df["nas_math_cl5"] = np.clip(b * 95 + noise * 95 + rng.normal(0, 6, len(df)), 15, 100)
    df["nas_lang_cl5"] = np.clip(b * 95 + noise * 95 + rng.normal(0, 6, len(df)), 15, 100)
    df["nas_math_cl8"] = np.clip(b * 90 + noise * 90 + rng.normal(0, 7, len(df)), 10, 100)
    df["nas_lang_cl8"] = np.clip(b * 90 + noise * 90 + rng.normal(0, 7, len(df)), 10, 100)
    return df


def add_infrastructure(df: pd.DataFrame) -> pd.DataFrame:
    b = df["_base"].values
    df["pct_schools_electricity"] = np.clip(b * 100 + rng.normal(0, 10, len(df)), 20, 100)
    df["pct_schools_drinking_water"] = np.clip(b * 100 + rng.normal(0, 8, len(df)), 30, 100)
    df["pct_schools_toilets"] = np.clip(b * 100 + rng.normal(0, 9, len(df)), 25, 100)
    df["pct_schools_computers"] = np.clip(b * 80 + rng.normal(0, 12, len(df)), 5, 100)
    df["pct_schools_library"] = np.clip(b * 75 + rng.normal(0, 12, len(df)), 5, 100)
    df["pct_schools_permanent_building"] = np.clip(b * 95 + rng.normal(0, 7, len(df)), 40, 100)
    df["pupil_teacher_ratio"] = np.clip(40 - b * 20 + rng.normal(0, 4, len(df)), 15, 60)
    df["pct_schools_medical_checkup"] = np.clip(b * 70 + rng.normal(0, 15, len(df)), 5, 100)
    df["pct_govt_schools"] = np.clip(rng.uniform(40, 90, len(df)), 20, 100)
    return df


def add_equity(df: pd.DataFrame) -> pd.DataFrame:
    # Gap = male_score - female_score (positive => boys ahead)
    df["gender_gap_math_cl5"] = np.clip(rng.normal(3, 4, len(df)), -10, 20)
    df["gender_gap_lang_cl5"] = np.clip(rng.normal(-1, 3, len(df)), -15, 10)
    df["rural_urban_gap_math"] = np.clip(rng.normal(8, 5, len(df)), -5, 30)
    df["sc_gap_math_cl5"] = np.clip(rng.normal(6, 4, len(df)), -5, 25)
    df["st_gap_math_cl5"] = np.clip(rng.normal(9, 5, len(df)), -5, 30)
    return df


def add_circumstances(df: pd.DataFrame) -> pd.DataFrame:
    b = df["_base"].values
    df["pct_literate_parents"] = np.clip(b * 100 + rng.normal(0, 10, len(df)), 20, 100)
    df["pct_urban_hh"] = np.clip(rng.uniform(10, 80, len(df)), 5, 95)
    df["pct_sc_st_population"] = np.clip(rng.uniform(10, 50, len(df)), 5, 60)
    df["pct_professional_occupation"] = np.clip(b * 40 + rng.normal(0, 8, len(df)), 2, 60)
    df["hdi_proxy"] = np.clip(b + rng.normal(0, 0.05, len(df)), 0.3, 0.95)
    return df


def add_data_quality(df: pd.DataFrame) -> pd.DataFrame:
    n = len(df)
    # ~15 % missingness on some indicators to reflect real-world incompleteness
    mask = rng.random(n) < 0.15
    df.loc[mask, "pct_schools_medical_checkup"] = np.nan
    mask2 = rng.random(n) < 0.10
    df.loc[mask2, "st_gap_math_cl5"] = np.nan
    df["data_completeness_pct"] = (~df.isna()).mean(axis=1) * 100
    df["is_synthetic"] = True
    df["data_source"] = "SYNTHETIC_DEMO"
    df["generated_at"] = datetime.now(timezone.utc).isoformat()
    return df


def build_dataset() -> pd.DataFrame:
    df = make_districts()
    df = add_performance(df)
    df = add_infrastructure(df)
    df = add_equity(df)
    df = add_circumstances(df)
    df = add_data_quality(df)
    df = df.drop(columns=["_base"])
    return df


def main():
    print("=" * 60)
    print("SYNTHETIC DEMO DATA GENERATOR")
    print("WARNING: Output is NOT real government data.")
    print("=" * 60)
    df = build_dataset()
    out_csv = OUTPUT_DIR / "synthetic_districts.csv"
    out_parquet = PROCESSED_DIR / "districts_demo.parquet"
    df.to_csv(out_csv, index=False)
    df.to_parquet(out_parquet, index=False)

    manifest = {
        "data_type": "SYNTHETIC_DEMO",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "num_districts": len(df),
        "num_states": df["state_name"].nunique(),
        "seed": SEED,
        "warning": "All values are randomly generated. Do NOT use for research conclusions.",
        "columns": list(df.columns),
    }
    with open(OUTPUT_DIR / "synthetic_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"[OK] Districts : {len(df)}")
    print(f"[OK] States    : {df['state_name'].nunique()}")
    print(f"[OK] CSV       : {out_csv}")
    print(f"[OK] Parquet   : {out_parquet}")
    print("DONE -- Remember: this is DEMO data only.")


if __name__ == "__main__":
    main()
