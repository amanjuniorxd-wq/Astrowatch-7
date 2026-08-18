# Live swetest.cgi results, fetched this session via mcp__workspace__web_fetch.
# Each entry: label -> {"ayan": "D M S", "sun": "D M S", "moon": "D M S", "asc": "D M S"}
LIVE = {}

def dms(s):
    parts = s.replace("'", " ").replace('"', "").split()
    d, m, sec = float(parts[0]), float(parts[1]), float(parts[2])
    sign = -1 if d < 0 else 1
    return sign * (abs(d) + m/60 + sec/3600)

LIVE["Patna (mandatory test case)"] = {
    "ayan": dms("23 51 27.8113"),
    "sun": dms("33 25 22.2250"), "moon": dms("208 54 18.4129"),
    "mercury": dms("43 48 22.2951"), "venus": dms("26 48 33.1190"),
    "mars": dms("45 58 34.2059"), "jupiter": dms("26 20 2.2881"), "saturn": dms("27 29 38.8978"),
    "asc": dms("4 28 30.2395"),
}
LIVE["New York (mandatory 1946 test case)"] = {
    "ayan": dms("23 6 15.6488"),
    "sun": dms("59 39 53.6984"), "moon": dms("236 7 25.0048"),
    "mercury": dms("75 26 34.0633"), "venus": dms("92 26 7.8370"),
    "mars": dms("123 34 42.9387"), "jupiter": dms("174 20 52.2033"), "saturn": dms("90 41 30.1692"),
    "asc": dms("78 49 25.1639"),
}

if __name__ == "__main__":
    for k, v in LIVE.items():
        print(k, v)

LIVE["Tokyo 1830-06-17"] = {
    "ayan": dms("21 29 17.8216"), "sun": dms("64 23 2.0857"), "moon": dms("24 8 24.2034"),
    "mercury": dms("61 31 34.4443"), "venus": dms("21 7 35.3421"), "mars": dms("320 4 26.5177"),
    "jupiter": dms("263 35 43.5138"), "saturn": dms("113 16 55.8345"), "asc": dms("1 54 25.1778"),
}
LIVE["London 1800-10-03"] = {
    "ayan": dms("21 4 24.4092"), "sun": dms("168 35 51.1475"), "moon": dms("351 28 34.6226"),
    "mercury": dms("165 52 8.5714"), "venus": dms("184 24 20.4443"), "mars": dms("33 57 26.7340"),
    "jupiter": dms("99 45 10.6213"), "saturn": dms("119 33 25.8404"), "asc": dms("140 36 2.1861"),
}
LIVE["Moscow 1915-01-27"] = {
    "ayan": dms("22 40 25.8513"), "sun": dms("284 13 19.9568"), "moon": dms("65 35 11.3435"),
    "mercury": dms("298 51 51.1791"), "venus": dms("237 50 12.7423"), "mars": dms("275 29 49.7923"),
    "jupiter": dms("305 39 15.9694"), "saturn": dms("63 28 36.3165"), "asc": dms("183 49 31.9462"),
}
LIVE["London 1990-09-21"] = {
    "ayan": dms("23 43 52.6684"), "sun": dms("154 7 53.2806"), "moon": dms("178 15 40.9650"),
    "mercury": dms("136 53 20.1909"), "venus": dms("143 19 2.1329"), "mars": dms("45 9 3.1149"),
    "jupiter": dms("102 54 35.1885"), "saturn": dms("264 58 35.7464"), "asc": dms("119 8 9.6224"),
}
LIVE["New York 1942-09-10"] = {
    "ayan": dms("23 3 16.5890"), "sun": dms("143 59 47.8579"), "moon": dms("140 55 56.4526"),
    "mercury": dms("170 3 5.4939"), "venus": dms("126 41 40.3469"), "mars": dms("152 24 51.2328"),
    "jupiter": dms("86 21 54.0357"), "saturn": dms("49 16 8.7840"), "asc": dms("134 1 27.8672"),
}
LIVE["New Delhi 2024-11-23"] = {
    "ayan": dms("24 12 15.6032"), "sun": dms("217 55 28.1055"), "moon": dms("137 36 16.4333"),
    "mercury": dms("238 6 18.8217"), "venus": dms("260 13 47.9433"), "mars": dms("100 52 55.6587"),
    "jupiter": dms("53 54 29.4585"), "saturn": dms("318 32 58.2363"), "asc": dms("180 26 24.7911"),
}
LIVE["London 1823-07-19"] = {
    "ayan": dms("21 23 51.5682"), "sun": dms("94 46 25.9012"), "moon": dms("237 44 16.2817"),
    "mercury": dms("74 47 55.9940"), "venus": dms("139 58 1.4224"), "mars": dms("67 0 1.2273"),
    "jupiter": dms("66 18 56.4853"), "saturn": dms("30 28 49.7583"), "asc": dms("239 40 52.9953"),
}
LIVE["Singapore 2034-09-09"] = {
    "ayan": dms("24 20 28.9352"), "sun": dms("142 37 18.3766"), "moon": dms("105 7 53.7368"),
    "mercury": dms("168 7 8.7960"), "venus": dms("184 23 26.3219"), "mars": dms("135 34 40.5125"),
    "jupiter": dms("347 24 39.4105"), "saturn": dms("97 8 7.1502"), "asc": dms("6 50 11.2986"),
}
LIVE["New Delhi 1932-01-19"] = {
    "ayan": dms("22 54 30.0211"), "sun": dms("275 6 16.9085"), "moon": dms("43 1 8.9489"),
    "mercury": dms("252 57 34.7686"), "venus": dms("307 22 4.4774"), "mars": dms("278 5 31.7545"),
    "jupiter": dms("117 11 28.3550"), "saturn": dms("273 0 34.3500"), "asc": dms("22 13 55.3650"),
}
LIVE["London 1909-08-05"] = {
    "ayan": dms("22 35 24.9357"), "sun": dms("109 55 45.7459"), "moon": dms("341 37 13.9190"),
    "mercury": dms("111 10 49.2632"), "venus": dms("136 21 2.3605"), "mars": dms("342 7 45.2266"),
    "jupiter": dms("143 10 19.1147"), "saturn": dms("0 38 13.9605"), "asc": dms("222 24 27.4490"),
}
LIVE["Singapore 1960-12-15"] = {
    "ayan": dms("23 18 35.7472"), "sun": dms("240 38 3.6997"), "moon": dms("205 37 3.4944"),
    "mercury": dms("229 1 47.8744"), "venus": dms("283 15 20.2726"), "mars": dms("80 56 23.2724"),
    "jupiter": dms("257 4 18.7647"), "saturn": dms("264 25 18.2271"), "asc": dms("222 39 46.1199"),
}
LIVE["New Delhi 1910-04-10"] = {
    "ayan": dms("22 35 58.5215"), "sun": dms("356 58 19.8873"), "moon": dms("3 15 18.0938"),
    "mercury": dms("1 47 24.8834"), "venus": dms("311 29 54.0046"), "mars": dms("54 3 32.1832"),
    "jupiter": dms("165 46 13.8065"), "saturn": dms("2 46 46.7504"), "asc": dms("109 31 10.9999"),
}
