"""
inject_manual_coords.py
-----------------------
Injects hard-coded coordinates for known Ontario public sector employers
that Nominatim can't find by name.

Run this, then rebuild:
    python inject_manual_coords.py --coords employer_coords.json
    python build_map_data.py --input sunshine2025.csv --coords employer_coords.json --output sunshine_map.json
"""

import json, argparse

# Hard-coded coords for known Ontario public sector orgs
# Format: "Exact name from CSV": (lat, lon)
MANUAL = {
    # ── Hospitals / Health ─────────────────────────────────────────────────
    "University Health Network":                                        (43.6590, -79.3876),
    "Trillium Health Partners":                                         (43.5890, -79.6441),
    "The Hospital For Sick Children":                                   (43.6566, -79.3902),
    "Sinai Health System":                                              (43.6572, -79.4007),
    "Niagara Health System":                                            (43.1594, -79.2469),
    "Oak Valley Health":                                                (43.8561, -79.3370),
    "Lakeridge Health":                                                 (43.8979, -78.8443),
    "Mackenzie Health":                                                 (43.8359, -79.5003),
    "Southlake Regional Health Centre":                                 (44.0562, -79.4617),
    "Scarborough Health Network":                                       (43.7764, -79.2318),
    "William Osler Health System":                                      (43.7315, -79.7624),
    "Baycrest Health Sciences":                                         (43.7298, -79.4499),
    "St. Joseph's Health Care London":                                  (42.9849, -81.2745),
    "London Health Sciences Centre":                                    (43.0113, -81.2737),
    "Kingston Health Sciences Centre":                                  (44.2312, -76.4862),
    "Hamilton Health Sciences":                                         (43.2609, -79.8729),
    "St. Joseph's Healthcare Hamilton":                                 (43.2490, -79.8880),
    "The Ottawa Hospital":                                              (45.3960, -75.7178),
    "Queensway Carleton Hospital":                                      (45.3414, -75.8037),
    "Montfort Hospital":                                                (45.4477, -75.6201),
    "Sunnybrook Health Sciences Centre":                                (43.7234, -79.3771),
    "North York General Hospital":                                      (43.7676, -79.4066),
    "Michael Garron Hospital":                                          (43.6908, -79.3303),
    "St. Michael's Hospital":                                           (43.6529, -79.3787),
    "Unity Health Toronto":                                             (43.6529, -79.3787),
    "Humber River Hospital":                                            (43.7385, -79.5540),
    "Markham Stouffville Hospital":                                     (43.8813, -79.3010),
    "Peel Regional Police":                                             (43.6894, -79.7417),
    "Workplace Safety And Insurance Board":                             (43.6453, -79.3806),
    "Cancer Care Ontario":                                              (43.6532, -79.3832),
    "Centre for Addiction and Mental Health":                           (43.6444, -79.4155),
    "CAMH":                                                             (43.6444, -79.4155),
    "Holland Bloorview Kids Rehabilitation Hospital":                   (43.7234, -79.3701),
    "Osler Health System":                                              (43.7315, -79.7624),
    "Niagara Falls Memorial Medical Center":                            (43.1059, -79.0740),
    "Health Sciences North":                                            (46.4870, -80.9930),
    "Sault Area Hospital":                                              (46.5210, -84.3430),
    "Thunder Bay Regional Health Sciences Centre":                      (48.3809, -89.2477),
    "Timmins and District Hospital":                                    (48.4758, -81.3305),
    "North Bay Regional Health Centre":                                 (46.3091, -79.4608),
    "Muskoka Algonquin Healthcare":                                     (45.1167, -79.3667),
    "Bluewater Health":                                                 (42.9945, -82.4049),
    "Chatham-Kent Health Alliance":                                     (42.4048, -82.1910),
    "Erie Shores HealthCare":                                           (42.0354, -82.7121),
    "Guelph General Hospital":                                          (43.5448, -80.2482),
    "Grand River Hospital":                                             (43.4516, -80.4925),
    "St. Mary's General Hospital":                                      (43.4478, -80.5108),
    "Cambridge Memorial Hospital":                                      (43.3700, -80.3123),
    "Brant Community Healthcare System":                                (43.1394, -80.2644),
    "Norfolk General Hospital":                                         (42.8420, -80.3165),
    "Woodstock Hospital":                                               (43.1302, -80.7474),
    "Stratford General Hospital":                                       (43.3700, -81.0000),
    "Listowel Wingham Hospitals Alliance":                              (43.7315, -80.9576),
    "Collingwood General and Marine Hospital":                          (44.5001, -80.2171),
    "Georgian Bay General Hospital":                                    (44.7501, -79.8833),
    "Royal Victoria Regional Health Centre":                            (44.3667, -79.6921),
    "Orillia Soldiers Memorial Hospital":                               (44.6071, -79.4202),
    "Peterborough Regional Health Centre":                              (44.2998, -78.3197),
    "Lakeridge Health Oshawa":                                          (43.8979, -78.8443),
    "Ross Memorial Hospital":                                           (44.5360, -78.7416),
    "Haliburton Highlands Health Services":                             (45.0501, -78.5001),
    "Pembroke Regional Hospital":                                       (45.8167, -77.1000),
    "Renfrew Victoria Hospital":                                        (45.4734, -76.6877),
    "Brockville General Hospital":                                      (44.5895, -75.6832),
    "Perth and Smiths Falls District Hospital":                         (44.9001, -76.2501),
    "Kemptville District Hospital":                                     (45.0167, -75.6501),
    "Winchester District Memorial Hospital":                            (45.0834, -75.3501),
    "Cornwall Community Hospital":                                      (45.0184, -74.7290),
    "Hawkesbury and District General Hospital":                         (45.6001, -74.6001),
    "Arnprior Regional Health":                                         (45.4334, -76.3501),

    # ── School Boards ─────────────────────────────────────────────────────
    "Thames Valley District School Board":                              (42.9849, -81.2453),
    "Upper Grand District School Board":                                (43.7315, -80.0993),
    "Kawartha Pine Ridge District School Board":                        (44.3001, -78.3197),
    "Upper Canada District School Board":                               (44.6971, -75.4833),
    "Grand Erie District School Board":                                 (43.1394, -80.2644),
    "Niagara Catholic District School Board":                           (43.1594, -79.2469),
    "Humber College Institute Of Technology and Advanced Learning":     (43.7279, -79.6069),
    "Conestoga College Institute Of Technology and Advanced Learning":  (43.4978, -80.5231),
    "Sheridan College Institute Of Technology and Advanced Learning":   (43.5319, -79.8908),
    "Avon Maitland District School Board":                              (43.3700, -81.0000),
    "Trillium Lakelands District School Board":                         (44.6047, -79.4609),
    "Near North District School Board":                                 (46.3091, -79.4608),
    "Northeastern Catholic District School Board":                      (48.4758, -81.3305),
    "Nipissing-Parry Sound Catholic District School Board":             (46.3091, -79.4608),
    "Algonquin and Lakeshore Catholic District School Board":           (44.2312, -76.4862),
    "Limestone District School Board":                                  (44.2312, -76.4862),
    "Hastings and Prince Edward District School Board":                 (44.1501, -77.4001),
    "Renfrew County District School Board":                             (45.4734, -76.6877),
    "Renfrew County Catholic District School Board":                    (45.4734, -76.6877),
    "Huron-Superior Catholic District School Board":                    (46.5210, -84.3430),
    "Huron Perth Catholic District School Board":                       (43.3700, -81.0000),
    "Bruce-Grey Catholic District School Board":                        (44.5667, -81.0001),
    "Bluewater District School Board":                                  (43.7315, -81.2001),
    "Greater Essex County District School Board":                       (42.3167, -82.9834),
    "Windsor-Essex Catholic District School Board":                     (42.3167, -82.9834),
    "Lambton Kent District School Board":                               (42.9945, -82.4049),
    "St. Clair Catholic District School Board":                         (42.9945, -82.4049),
    "Peel District School Board":                                       (43.6894, -79.7417),
    "Dufferin-Peel Catholic District School Board":                     (43.6894, -79.7417),
    "York Region District School Board":                                (43.8971, -79.4366),
    "York Catholic District School Board":                              (43.8971, -79.4366),
    "Durham District School Board":                                     (43.8979, -78.8443),
    "Durham Catholic District School Board":                            (43.8979, -78.8443),
    "Halton District School Board":                                     (43.5319, -79.8908),
    "Halton Catholic District School Board":                            (43.5319, -79.8908),
    "Waterloo Region District School Board":                            (43.4516, -80.4925),
    "Waterloo Catholic District School Board":                          (43.4516, -80.4925),
    "Rainbow District School Board":                                    (46.4870, -80.9930),
    "Sudbury Catholic District School Board":                           (46.4870, -80.9930),
    "Simcoe County District School Board":                              (44.3667, -79.6921),
    "Simcoe Muskoka Catholic District School Board":                    (44.3667, -79.6921),
    "Trillium Lakelands District School Board":                         (44.6047, -79.4609),
    "Keewatin-Patricia District School Board":                          (49.7667, -94.4834),
    "Rainy River District School Board":                                (48.7167, -94.5667),
    "Superior-Greenstone District School Board":                        (48.3809, -89.2477),
    "Lakehead District School Board":                                   (48.3809, -89.2477),
    "Thunder Bay Catholic District School Board":                       (48.3809, -89.2477),
    "Conseil Scolaire De District Catholique Du Centre-Est De L'Ontario": (45.4215, -75.6972),
    "Conseil Scolaire Catholique MonAvenir":                            (43.7000, -79.4000),
    "Conseil Scolaire Viamonde":                                        (43.7000, -79.4000),
    "Conseil Scolaire De District Catholique De L'est Ontarien":        (45.4215, -75.6972),
    "Conseil Des Ecoles Publiques De L'est De L'ontario":               (45.4215, -75.6972),
    "Conseil Scolaire Catholique Providence":                           (42.3167, -82.9834),
    "Conseil Scolaire Du District Du Grand Nord De L'ontario":          (46.4870, -80.9930),
    "Conseil Scolaire Du District Catholique Des Aurores Boreales":     (48.3809, -89.2477),
    "Conseil Scolaire Du District Du Nord-Est De L'ontario":            (48.4758, -81.3305),

    # ── Ontario Government Ministries ──────────────────────────────────────
    "Public and Business Service Delivery and  Procurement":            (43.6532, -79.3832),
    "Children, Community and Social Services":                          (43.6532, -79.3832),
    "Environment, Conservation and Parks":                              (43.6532, -79.3832),
    "Labour, Immigration, Training and Skills Development":             (43.6532, -79.3832),
    "Treasury Board Secretariat":                                       (43.6532, -79.3832),
    "Health":                                                           (43.6532, -79.3832),
    "Education":                                                        (43.6532, -79.3832),
    "Attorney General":                                                 (43.6532, -79.3832),
    "Finance":                                                          (43.6532, -79.3832),
    "Infrastructure":                                                   (43.6532, -79.3832),
    "Municipal Affairs and Housing":                                    (43.6532, -79.3832),
    "Natural Resources and Forestry":                                   (43.6532, -79.3832),
    "Solicitor General":                                                (43.6532, -79.3832),
    "Transportation":                                                   (43.6532, -79.3832),
    "Agriculture, Food and Rural Affairs":                              (43.6532, -79.3832),
    "Economic Development, Job Creation and Trade":                     (43.6532, -79.3832),
    "Energy":                                                           (43.6532, -79.3832),
    "Government and Consumer Services":                                 (43.6532, -79.3832),
    "Indigenous Affairs":                                               (43.6532, -79.3832),
    "Long-Term Care":                                                   (43.6532, -79.3832),
    "Mines":                                                            (43.6532, -79.3832),
    "Northern Development":                                             (43.6532, -79.3832),
    "Seniors and Accessibility":                                        (43.6532, -79.3832),
    "Tourism, Culture and Sport":                                       (43.6532, -79.3832),
    "Cabinet Office":                                                   (43.6532, -79.3832),

    # ── Crown Agencies / Other ─────────────────────────────────────────────
    "Ontario Lottery And Gaming Corporation":                           (43.6532, -79.3832),
    "Ontario Power Generation":                                         (43.6532, -79.3832),
    "Hydro One Networks Inc":                                           (43.6532, -79.3832),
    "Hydro One":                                                        (43.6532, -79.3832),
    "Ontario Clean Water Agency":                                       (43.6532, -79.3832),
    "Ontario Infrastructure and Lands Corporation":                     (43.6532, -79.3832),
    "Infrastructure Ontario":                                           (43.6532, -79.3832),
    "Metrolinx":                                                        (43.6453, -79.3806),
    "Toronto Transit Commission":                                       (43.6453, -79.3806),
    "Ontario Provincial Police":                                        (43.6532, -79.3832),
    "Correctional Services":                                            (43.6532, -79.3832),
    "Legal Aid Ontario":                                                (43.6532, -79.3832),
    "Ontario Human Rights Commission":                                  (43.6532, -79.3832),
    "Liquor Control Board Of Ontario":                                  (43.6532, -79.3832),
    "LCBO":                                                             (43.6532, -79.3832),
    "Workplace Safety and Insurance Board":                             (43.6453, -79.3806),
    "Regional Municipality Of Niagara – Niagara Reg. Police":          (43.1594, -79.2469),
    "Ontario Securities Commission":                                    (43.6532, -79.3832),
    "Financial Services Regulatory Authority Of Ontario":               (43.6532, -79.3832),
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--coords", default="employer_coords.json")
    args = parser.parse_args()

    with open(args.coords, encoding="utf-8") as f:
        coords = json.load(f)

    injected = 0
    not_in_file = 0

    for name, (lat, lon) in MANUAL.items():
        if name in coords:
            if coords[name] is None:
                coords[name] = {
                    "lat": lat, "lon": lon,
                    "display_name": "manual",
                    "query_used": "[MANUAL]"
                }
                injected += 1
        else:
            not_in_file += 1

    with open(args.coords, "w", encoding="utf-8") as f:
        json.dump(coords, f, indent=2, ensure_ascii=False)

    print(f"Injected: {injected} manual coords")
    print(f"Not in coords file (not in your CSV): {not_in_file}")
    print(f"\nNow run:")
    print(f"  python build_map_data.py --input sunshine2025.csv --coords employer_coords.json --output sunshine_map.json")


if __name__ == "__main__":
    main()
