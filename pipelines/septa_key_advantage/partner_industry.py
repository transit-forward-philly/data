"""Hand-coded industry (NAICS sector, matching LODES CNS columns) and ownership for each SEPTA Key Advantage partner.

Keys are SEPTA's partner labels. Ownership: public, nonprofit, business. `checked` marks ownership confirmed from a
filing or the org's own site; the rest are inferred from what the org does. Unidentified partners map to None.
"""

# LODES CNS column -> NAICS sector label (Census LODES technical documentation)
CNS = {
    "CNS01": "Agriculture", "CNS02": "Mining", "CNS03": "Utilities", "CNS04": "Construction", "CNS05": "Manufacturing",
    "CNS06": "Wholesale trade", "CNS07": "Retail trade", "CNS08": "Transportation and warehousing", "CNS09": "Information",
    "CNS10": "Finance and insurance", "CNS11": "Real estate", "CNS12": "Professional, scientific and technical services",
    "CNS13": "Management of companies", "CNS14": "Administrative and support services", "CNS15": "Educational services",
    "CNS16": "Health care and social assistance", "CNS17": "Arts, entertainment and recreation",
    "CNS18": "Accommodation and food services", "CNS19": "Other services (unions, associations, civic groups)",
    "CNS20": "Public administration",
}

# Short labels shown on the site (sector filter, tables, charts)
SHORT = {
    "CNS01": "Agriculture", "CNS02": "Mining", "CNS03": "Utilities", "CNS04": "Construction", "CNS05": "Manufacturing",
    "CNS06": "Wholesale trade", "CNS07": "Retail", "CNS08": "Transportation and warehousing", "CNS09": "Information and software",
    "CNS10": "Finance and insurance", "CNS11": "Real estate", "CNS12": "Professional services", "CNS13": "Corporate offices",
    "CNS14": "Administrative services", "CNS15": "Education", "CNS16": "Health care and social assistance",
    "CNS17": "Arts and entertainment", "CNS18": "Hotels and food", "CNS19": "Unions, associations and civic groups",
    "CNS20": "Government",
}
STUDENTS, UNKNOWN = "College students", "Not identified"


def industry_label(partner: str) -> str:
    cns, own, _ = INDUSTRY[partner]
    return STUDENTS if own == "students" else SHORT[cns] if cns else UNKNOWN


# partner label -> (CNS column, ownership, checked)
INDUSTRY = {
    "ABC Seniors": ("CNS16", "business", True),  # Always Best Care franchise, home care
    "Arcadium Lithium (fmr Livent)": ("CNS05", "business", True),
    "Brandywine": ("CNS11", "business", True),  # Brandywine Realty Trust
    "Center City District": ("CNS19", "nonprofit", True),  # business improvement district
    "Center City Legal Reproductions, Inc.": ("CNS14", "business", True),  # litigation copying and document services
    "City of Philadelphia": ("CNS20", "public", True),
    "City Year": ("CNS15", "nonprofit", True),
    "County of Delaware": ("CNS20", "public", True),
    "Curtis Institute of Music": ("CNS15", "nonprofit", True),
    "Defender Association of Philadelphia": ("CNS12", "nonprofit", True),  # public defender, legal services
    "Dywer": (None, None, False),
    "FMC": ("CNS05", "business", True),
    "Four Seasons": ("CNS18", "business", True),
    "Health Verity": ("CNS09", "business", True),  # health data software
    "Inspiritec": ("CNS14", "nonprofit", True),  # 501(c)(3) contact center
    "Integral Molecular": ("CNS12", "business", True),  # biotech research
    "IONOS": ("CNS09", "business", True),  # web hosting
    "Launch Philly": ("CNS15", "nonprofit", True),  # Communities In Schools
    "Moravia": ("CNS16", "business", True),  # home care agency
    "PA House of Representatives": ("CNS20", "public", True),
    "PHDC": ("CNS20", "public", True),  # quasi-public housing corporation
    "PPA": ("CNS20", "public", True),
    "Stateside": ("CNS05", "business", True),  # beverage maker
    "Swarthmore Employee": ("CNS15", "nonprofit", True),
    "UPHS - Penn": ("CNS16", "nonprofit", True),
    "Arcadia Land Company": ("CNS11", "business", True),
    "Artist Year": ("CNS15", "nonprofit", True),
    "BOK Condo Association": ("CNS19", "nonprofit", False),  # condo association
    "Busy Bees": ("CNS16", "business", False),  # child care center
    "Campus ESP": ("CNS09", "business", True),  # software
    "Catalyst Group": (None, None, False),
    "City Ave": ("CNS19", "nonprofit", True),  # special services district
    "Clean Air Council": ("CNS19", "nonprofit", True),
    "College Together - Employees": ("CNS15", "nonprofit", True),
    "Disciplinary Board SCOP": ("CNS20", "public", True),
    "DYAD": (None, None, False),
    "Econsult": ("CNS12", "business", True),
    "En Route Consulting LLC": ("CNS12", "business", False),
    "FatBall Therapeutics": ("CNS12", "business", False),  # name only; biotech research assumed
    "Green Building United": ("CNS19", "nonprofit", True),
    "Henry & Grogan, LLC": ("CNS12", "business", True),  # law firm
    "Hofstein Weiner & Meyer": ("CNS12", "business", True),  # law firm
    "HVLAW": ("CNS12", "business", False),  # law firm
    "International Raw Materials LTD": ("CNS06", "business", True),  # chemical distributor
    "KMKM Law Group, P.C.": ("CNS12", "business", False),
    "L. Priori Jewelry": ("CNS07", "business", True),
    "Malooga Catering": ("CNS18", "business", True),  # restaurant and catering
    "Metropolitan Acoustics": ("CNS12", "business", True),
    "Mt. Vernon Manor": ("CNS11", "nonprofit", True),  # affordable housing CDC
    "Noble Dental": ("CNS16", "business", True),
    "Nochumson PC": ("CNS12", "business", True),  # law firm
    "Permit Philly LLC": ("CNS12", "business", True),  # permit expediting
    "PHENND": ("CNS15", "nonprofit", True),
    "Philadelphia Council AFL-CIO": ("CNS19", "nonprofit", True),  # labor council
    "Primrose School": ("CNS16", "business", True),  # franchise preschool (child day care)
    "Remark Glass": ("CNS05", "business", False),  # glass studio and maker
    "Rock to the Future": ("CNS15", "nonprofit", True),
    "Saint Mary's Nursery School": ("CNS16", "nonprofit", False),  # church nursery school
    "TAUP - Temple Assn. of Univ. Prof.": ("CNS19", "nonprofit", True),  # faculty union
    "Tempest": ("CNS12", "business", True),  # digital agency
    "The Welcoming Center": ("CNS16", "nonprofit", True),  # immigrant workforce services
    "Thomas Center for Learning": ("CNS16", "business", False),  # licensed child care center
    "Vetigenics": ("CNS12", "business", True),  # veterinary biotech
    "Visit Philadelphia": ("CNS14", "nonprofit", True),  # tourism marketing (visitors bureau)
    "Voith & Mactavish": ("CNS12", "business", True),  # architects
    "World Affairs Council of Philadelphia": ("CNS19", "nonprofit", True),
    # college student programs: not jobs
    "Bryn Mawr College": (None, "students", True),
    "Community College of Philadelphia": (None, "students", True),
    "College Together": (None, "students", True),
    "Swarthmore College": (None, "students", True),
}
