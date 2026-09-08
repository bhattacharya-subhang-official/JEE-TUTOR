"""CHEMISTRY engine — formula parsing, molar mass, equation balancing, stoichiometry,
pH, electrochemistry (Nernst/Faraday), thermodynamics (ΔG). JEE-Advanced ready."""
import re
import math
import sympy as sp

ATOMIC_MASSES = {
    "H": 1.008, "He": 4.003, "Li": 6.94, "Be": 9.012, "B": 10.81, "C": 12.011, "N": 14.007,
    "O": 15.999, "F": 18.998, "Ne": 20.180, "Na": 22.990, "Mg": 24.305, "Al": 26.982,
    "Si": 28.085, "P": 30.974, "S": 32.06, "Cl": 35.45, "Ar": 39.948, "K": 39.098,
    "Ca": 40.078, "Sc": 44.956, "Ti": 47.867, "V": 50.942, "Cr": 51.996, "Mn": 54.938,
    "Fe": 55.845, "Co": 58.933, "Ni": 58.693, "Cu": 63.546, "Zn": 65.38, "Ga": 69.723,
    "Ge": 72.630, "As": 74.922, "Se": 78.971, "Br": 79.904, "Kr": 83.798, "Rb": 85.468,
    "Sr": 87.62, "Y": 88.906, "Zr": 91.224, "Nb": 92.906, "Mo": 95.95, "Tc": 98.0,
    "Ru": 101.07, "Rh": 102.91, "Pd": 106.42, "Ag": 107.87, "Cd": 112.41, "In": 114.82,
    "Sn": 118.71, "Sb": 121.76, "Te": 127.60, "I": 126.90, "Xe": 131.29, "Cs": 132.91,
    "Ba": 137.33, "La": 138.91, "Ce": 140.12, "Pr": 140.91, "Nd": 144.24, "Pm": 145.0,
    "Sm": 150.36, "Eu": 151.96, "Gd": 157.25, "Tb": 158.93, "Dy": 162.50, "Ho": 164.93,
    "Er": 167.26, "Tm": 168.93, "Yb": 173.05, "Lu": 174.97, "Hf": 178.49, "Ta": 180.95,
    "W": 183.84, "Re": 186.21, "Os": 190.23, "Ir": 192.22, "Pt": 195.08, "Au": 196.97,
    "Hg": 200.59, "Tl": 204.38, "Pb": 207.2, "Bi": 208.98, "Po": 209.0, "At": 210.0,
    "Rn": 222.0, "Fr": 223.0, "Ra": 226.0, "Ac": 227.0, "Th": 232.04, "Pa": 231.04,
    "U": 238.03, "Np": 237.0, "Pu": 244.0,
}


def parse_formula(formula: str) -> dict:
    """Parse chemical formula → element:count. Supports groups, e.g. Ca(OH)2, Fe2(SO4)3."""
    def helper(s, i):
        counts = {}
        while i < len(s):
            ch = s[i]
            if ch == "(":
                inner, i = helper(s, i + 1)
                num, i = read_num(s, i)
                for el, n in inner.items():
                    counts[el] = counts.get(el, 0) + n * num
            elif ch == ")":
                return counts, i + 1
            elif ch.isupper():
                el = ch
                i += 1
                while i < len(s) and s[i].islower():
                    el += s[i]; i += 1
                num, i = read_num(s, i)
                counts[el] = counts.get(el, 0) + num
            elif ch in "·.":
                i += 1
                num, i = read_num(s, i)
                inner, i = helper(s, i)
                for el, n in inner.items():
                    counts[el] = counts.get(el, 0) + n * num
            elif ch.isspace():
                i += 1
            else:
                raise ValueError(f"Unexpected character '{ch}' in formula")
        return counts, i

    def read_num(s, i):
        num = ""
        while i < len(s) and (s[i].isdigit() or s[i] == "."):
            num += s[i]; i += 1
        return (int(float(num)) if num else 1), i

    counts, _ = helper(formula.strip(), 0)
    if not counts:
        raise ValueError(f"Cannot parse formula '{formula}'")
    return counts


def molar_mass(formula: str):
    counts = parse_formula(formula)
    total = 0.0
    elements = {}
    for el, n in counts.items():
        if el not in ATOMIC_MASSES:
            raise ValueError(f"Unknown element '{el}'")
        total += ATOMIC_MASSES[el] * n
        elements[el] = n
    return {"molar_mass_g/mol": round(total, 3), "elements": elements,
            "formula": formula.strip(), "moles_per_gram": round(1 / total, 6)}


def _parse_charge(spec: str):
    """'MnO4-' → ('MnO4', -1); 'Fe3+' → ('Fe', +3); 'SO4^2-' → ('SO4', -2); 'e-' → ('e', -1)."""
    s = str(spec).strip()
    m = re.search(r"\^(\d*)([+-])$", s)
    if m:
        mag = int(m.group(1)) if m.group(1) else 1
        return s[:m.start()].strip(), (mag if m.group(2) == "+" else -mag)
    m = re.search(r"([+-]{1,2})$", s)
    if m:
        signs = m.group(1)
        mag = len(signs)
        core = s[:m.start()].strip()
        md = re.search(r"(\d+)$", core)
        if md:
            digit = int(md.group(1))
            before = core[:md.start()]
            try:
                counts = parse_formula(before)
            except Exception:
                counts = None
            if counts is not None and len(counts) >= 2:
                # digit continues an oxyanion subscript: MnO4-, SO4--, NH4+
                return core, (mag if signs[0] == "+" else -mag)
            # bare ion with charge magnitude: Fe3+, Fe2+, O2-
            return before, (digit if signs[0] == "+" else -digit)
        return core, (len(signs) if signs[0] == "+" else -len(signs))
    return s, 0


def _split_species(side: str):
    return [s.strip() for s in re.split(r"\s+\+\s+", side.strip()) if s.strip()]


def balance_equation(reaction: str):
    """Balance a reaction, charge-aware. Use spaces around '+': 'MnO4- + Fe2+ + H+ -> Mn2+ + Fe3+ + H2O'."""
    rx = reaction.replace("=", "->") if "->" not in reaction else reaction
    sides = rx.split("->")
    if len(sides) != 2:
        raise ValueError("Use format: A + B -> C + D")
    lhs_species = _split_species(sides[0])
    rhs_species = _split_species(sides[1])
    species = lhs_species + rhs_species
    parsed = []
    for s in species:
        core, ch = _parse_charge(s)
        if core in ("e", "E", "e⁻"):
            parsed.append(({}, ch))     # electron: no atoms, charge -1
        else:
            parsed.append((parse_formula(core), ch))
    elements = sorted({el for c, _ in parsed for el in c})
    has_charge = any(ch != 0 for _, ch in parsed)
    n = len(species)
    rows = len(elements) + (1 if has_charge else 0)
    A = sp.zeros(rows, n)
    for j, (c, ch) in enumerate(parsed):
        sign = 1 if j < len(lhs_species) else -1
        for el, cnt in c.items():
            A[elements.index(el), j] = sign * cnt
        if has_charge:
            A[rows - 1, j] = sign * ch
    ns = A.nullspace()
    if not ns:
        raise ValueError("No balancing possible — reaction is inconsistent")
    v = ns[0]
    denoms = [sp.Rational(x).q for x in v if sp.Rational(x).q != 1]
    if denoms:
        lcmv = denoms[0] if len(denoms) == 1 else sp.ilcm(*denoms)
        v = v * lcmv
    ints = [int(sp.Rational(x)) for x in v]
    g = math.gcd(*[abs(i) for i in ints if i]) or 1
    ints = [i // g for i in ints]
    if any(i < 0 for i in ints):
        ints = [-i for i in ints]
    if any(i == 0 for i in ints):
        raise ValueError("A species got coefficient 0 — check the reaction")
    n_react = len(lhs_species)
    lhs = " + ".join((f"{ints[j]} " if ints[j] != 1 else "") + species[j] for j in range(n_react))
    rhs = " + ".join((f"{ints[j]} " if ints[j] != 1 else "") + species[j] for j in range(n_react, n))
    coeffs = {species[j]: ints[j] for j in range(n)}
    out = {"balanced": f"{lhs} -> {rhs}", "coefficients": coeffs}
    if has_charge:
        ne = max((coeffs.get("e-", 0)), 0)
        if "e-" in coeffs:
            out["electrons_transferred"] = ne
    return out


def stoich_calc(reaction: str, known_species: str, known_amount: float,
                target_species: str, known_is_grams: bool = False):
    bal = balance_equation(reaction)
    coeffs = bal["coefficients"]
    if known_species not in coeffs or target_species not in coeffs:
        raise ValueError(f"Species must appear in reaction. Found: {list(coeffs)}")
    moles_known = known_amount
    molar_known = None
    if known_is_grams:
        molar_known = molar_mass(known_species)["molar_mass_g/mol"]
        moles_known = known_amount / molar_known
    ratio = coeffs[target_species] / coeffs[known_species]
    moles_target = moles_known * ratio
    molar_target = molar_mass(target_species)["molar_mass_g/mol"]
    return {"balanced_reaction": bal["balanced"],
            "moles_known": round(moles_known, 5),
            "moles_target": round(moles_target, 5),
            "mass_target_g": round(moles_target * molar_target, 4),
            "molar_mass_target": molar_target,
            "volume_at_STP_L": round(moles_target * 22.4, 4)}


def ph_calc(mode: str, concentration: float, basicity: int = 1, dilution_factor: float = 1.0,
            ka: float = None, temp_K: float = 298.0):
    Kw = 10 ** (-14 * (298.15 / temp_K))
    c = concentration / dilution_factor
    if mode == "strong_acid":
        H = c * basicity
        return {"pH": round(-math.log10(H), 4), "H+_M": H, "note": "strong acid, complete dissociation"}
    if mode == "strong_base":
        OH = c * basicity
        return {"pH": round(14 + math.log10(OH), 4), "OH-_M": OH, "pOH": round(-math.log10(OH), 4)}
    if mode == "weak_acid":
        if not ka:
            raise ValueError("weak_acid needs ka")
        H = math.sqrt(ka * c)
        return {"pH": round(-math.log10(H), 4), "H+_M": H, "alpha_%": round(H / c * 100, 3)}
    if mode == "weak_base":
        if not ka:
            raise ValueError("weak_base needs kb as 'ka'")
        OH = math.sqrt(ka * c)
        return {"pH": round(14 + math.log10(OH), 4), "OH-_M": OH}
    raise ValueError("mode: strong_acid | strong_base | weak_acid | weak_base")


def nernst_emf(E0: float, n: int, Q: float, temperature_K: float = 298.0):
    F, R = 96485.0, 8.314
    E = E0 - (R * temperature_K / (n * F)) * math.log(Q) * 2.302585 * 0  # ln form below
    E = E0 - (R * temperature_K / (n * F)) * math.log(Q)
    out = {"E_volt": round(E, 5), "form": "E = E° − (RT/nF)·lnQ"}
    if abs(temperature_K - 298.0) < 1:
        out["E_at_298_simplified"] = round(E0 - (0.0591 / n) * math.log10(Q), 5)
        out["form_298"] = "E = E° − (0.0591/n)·log₁₀Q"
    return out


def faraday_electrolysis(I: float, t_s: float, z: int, species_molar_mass: float = None):
    moles_e = I * t_s / 96485.0
    out = {"moles_of_electrons": round(moles_e, 6), "charge_C": round(I * t_s, 2)}
    if species_molar_mass:
        out["mass_deposited_g"] = round(moles_e * species_molar_mass / z, 5)
    return out


def gibbs_free_energy(dH_kJ: float, dS_J: float, T: float = 298.0):
    dG = dH_kJ - T * dS_J / 1000.0
    return {"dG_kJ/mol": round(dG, 3), "spontaneous": dG < 0,
            "equilibrium_T_K": round(dH_kJ * 1000 / dS_J, 2) if dS_J else None,
            "form": "ΔG = ΔH − TΔS"}


def solution_properties(kind: str, **kw):
    R = 0.0821
    if kind == "osmotic":
        return {"pi_atm": round(kw["molarity"] * R * kw.get("T", 298) * kw.get("i", 1), 4)}
    if kind == "boiling_elevation":
        return {"dTb_C": round(kw["kb"] * kw["molality"] * kw.get("i", 1), 4)}
    if kind == "freezing_depression":
        return {"dTf_C": round(kw["kf"] * kw["molality"] * kw.get("i", 1), 4)}
    raise ValueError("kind: osmotic | boiling_elevation | freezing_depression")


# ═════════════════════════ JEE-ADV FULL SYLLABUS EXTENSIONS ═════════════════════════
RGAS = 8.314


def concentration_calc(kind: str, **kw):
    kind = str(kind).lower()
    if kind == "molarity_from_mass":
        M = kw.get("molar_mass") or molar_mass(kw["formula"])["molar_mass_g/mol"]
        Mv = kw["mass_g"] / M / kw["volume_L"]
        return {"molarity_M": round(Mv, 6), "moles": round(kw["mass_g"] / M, 6), "molar_mass_used": M}
    if kind == "molality":
        return {"molality_m": round(kw["moles_solute"] / kw["solvent_kg"], 6)}
    if kind == "mole_fraction":
        ns = kw["moles"]  # list
        tot = sum(ns)
        return {"fractions": [round(n / tot, 6) for n in ns], "total_moles": tot}
    if kind == "ppm":
        return {"ppm": round(kw["mass_solute"] / kw["mass_solution"] * 1e6, 4)}
    if kind == "dilution":
        M1, V1, M2, V2 = kw.get("M1"), kw.get("V1"), kw.get("M2"), kw.get("V2")
        if M1 is None:
            return {"M1": round(M2 * V2 / V1, 6)}
        if V1 is None:
            return {"V1": round(M2 * V2 / M1, 6)}
        if M2 is None:
            return {"M2": round(M1 * V1 / V2, 6)}
        return {"V2": round(M1 * V1 / M2, 6)}
    if kind == "molarity_to_molality":
        M, d, Ms = kw["M"], kw["density_g_mL"], kw["molar_mass_solute"]
        m = 1000 * M / (1000 * d - M * Ms)
        return {"molality_m": round(m, 6), "formula": "m = 1000M/(1000d − M·M₂)"}
    raise ValueError("kind: molarity_from_mass|molality|mole_fraction|ppm|dilution|molarity_to_molality")


def limiting_reagent(reaction: str, amounts: list, actual_yield_g: float = None, product: str = None):
    bal = balance_equation(reaction)
    coeffs = bal["coefficients"]
    potentials = {}
    moles_avail = {}
    for a in amounts:
        sp_, amt = a["species"], a["amount"]
        if sp_ not in coeffs:
            raise ValueError(f"{sp_} not in reaction")
        mol = amt / molar_mass(sp_)["molar_mass_g/mol"] if a.get("is_grams") else amt
        moles_avail[sp_] = mol
        potentials[sp_] = mol / coeffs[sp_]
    lr = min(potentials, key=potentials.get)
    extent = potentials[lr]
    products = {s: c for s, c in coeffs.items() if s not in moles_avail}
    out = {"balanced": bal["balanced"], "limiting_reagent": lr,
           "moles_available": {k: round(v, 5) for k, v in moles_avail.items()},
           "extent_of_reaction": round(extent, 6),
           "max_product_moles": {s: round(extent * c, 5) for s, c in products.items()},
           "max_product_grams": {s: round(extent * c * molar_mass(s)["molar_mass_g/mol"], 4) for s, c in products.items()}}
    if actual_yield_g is not None and product:
        theo = out["max_product_grams"].get(product)
        if theo:
            out["percent_yield"] = round(100 * actual_yield_g / theo, 3)
    return out


def empirical_formula(composition: dict, molar_mass_val: float = None):
    moles = {el: n / ATOMIC_MASSES[el] for el, n in composition.items()}
    mn = min(moles.values())
    ratio = {el: n / mn for el, n in moles.items()}
    rounded = {}
    for el, r in ratio.items():
        near_int = round(r)
        for denom in range(1, 7):
            if abs(r * denom - round(r * denom)) < 0.06:
                near_int = round(r * denom)
                break
        rounded[el] = near_int
    # reduce if all divisible
    from math import gcd
    g = 0
    for v in rounded.values():
        g = gcd(g, v)
    if g > 1:
        rounded = {el: v // g for el, v in rounded.items()}
    emp = "".join(f"{el}{(v if v != 1 else '')}" for el, v in sorted(rounded.items()))
    out = {"empirical_formula": emp, "ratios": {el: round(v, 4) for el, v in ratio.items()},
           "subscripts": rounded}
    if molar_mass_val:
        emp_mm = sum(ATOMIC_MASSES[el] * n for el, n in rounded.items())
        mult = round(molar_mass_val / emp_mm)
        out["multiplier"] = mult
        out["molecular_formula"] = "".join(f"{el}{(rounded[el]*mult if rounded[el]*mult != 1 else '')}" for el in sorted(rounded))
    return out


def combustion_analysis(sample_g: float, co2_g: float, h2o_g: float, molar_mass_val: float = None):
    molC = co2_g / 44.01
    molH = 2 * h2o_g / 18.015
    massC = molC * 12.011
    massH = molH * 1.008
    massO = sample_g - massC - massH
    out = {"moles_C": round(molC, 5), "moles_H": round(molH, 5),
           "mass_C_g": round(massC, 4), "mass_H_g": round(massH, 4)}
    if massO > 1e-6:
        molO = massO / 15.999
        out.update({"mass_O_g": round(massO, 4), "moles_O": round(molO, 5)})
        emp = empirical_formula({"C": massC, "H": massH, "O": massO}, molar_mass_val)
    else:
        emp = empirical_formula({"C": massC, "H": massH}, molar_mass_val)
    out["formula_result"] = emp
    return out


def degree_unsaturation(formula: str):
    counts = parse_formula(_parse_charge(formula)[0] if isinstance(formula, str) else formula)
    C = counts.get("C", 0)
    H = counts.get("H", 0)
    N = counts.get("N", 0)
    X = sum(counts.get(h, 0) for h in ("F", "Cl", "Br", "I"))
    dou = (2 * C + 2 + N - H - X) / 2
    return {"DoU": dou, "interpretation": f"{int(dou)} ring(s) + π bond(s) combined = {dou}",
            "note": "DoU = (2C + 2 + N − H − X)/2; O and S ignored"}


def gas_laws(kind: str, **kw):
    kind = str(kind).lower()
    if kind == "combined":
        P1, V1, T1 = kw.get("P1"), kw.get("V1"), kw.get("T1")
        P2, V2, T2 = kw.get("P2"), kw.get("V2"), kw.get("T2")
        if P1 is None:
            return {"P1": round(P2 * V2 * T1 / (V1 * T2), 6)}
        if V1 is None:
            return {"V1": round(P2 * V2 * T1 / (P1 * T2), 6)}
        if T1 is None:
            return {"T1_K": round(P1 * V1 * T2 / (P2 * V2), 6)}
        if P2 is None:
            return {"P2": round(P1 * V1 * T2 / (V1 * T1), 6)}
        if V2 is None:
            return {"V2": round(P1 * V1 * T2 / (P2 * T1), 6)}
        return {"T2_K": round(P2 * V2 * T1 / (P1 * V1), 6)}
    if kind == "partial_pressure":
        n_i, n_tot, P = kw["n_i"], kw["n_total"], kw["P_total"]
        return {"partial_pressure": round(n_i / n_tot * P, 6), "mole_fraction": round(n_i / n_tot, 6)}
    if kind == "grahams":
        if kw.get("M1") and kw.get("M2"):
            r = math.sqrt(kw["M2"] / kw["M1"])
            return {"rate1/rate2": round(r, 6), "formula": "r1/r2 = √(M2/M1)",
                    "time1/time2": round(1 / r, 6)}
        M1, M2 = kw["M1"], kw["M2"]
        return {"M2": round(M1 * (kw["rate2"] / kw["rate1"]) ** 2, 5)}
    if kind == "vanderwaals":
        n, a, b, T, V = kw["n"], kw["a"], kw["b"], kw["T"], kw["V"]
        P = n * RGAS * T / (V - n * b) - a * (n / V) ** 2
        return {"P_atm": round(P, 6), "note": "units: a in atm·L²/mol², b in L/mol, V in L"}
    if kind == "compressibility":
        P, V, n, T = kw["P"], kw["V"], kw["n"], kw["T"]
        return {"Z": round(P * V / (n * RGAS * T), 5),
                "meaning": "Z=1 ideal; Z<1 attractive dominate; Z>1 repulsive dominate"}
    raise ValueError("kind: combined|partial_pressure|grahams|vanderwaals|compressibility")


def equilibrium_tools(kind: str, **kw):
    kind = str(kind).lower()
    if kind == "kp_kc":
        T = kw["T"]
        rx = kw["reaction"]
        def _sides_counts(side):
            from math import gcd as _gcd
            counts = {}
            for s in _split_species(side):
                m = re.match(r"^(\d+)\s+(.+)$", s)
                mult, sp_ = (int(m.group(1)), m.group(2)) if m else (1, s)
                core, _ch = _parse_charge(sp_)
                counts[core] = counts.get(core, 0) + mult
            g = 0
            for v in counts.values():
                g = _gcd(g, v)
            if g > 1:
                counts = {k: v // g for k, v in counts.items()}
            return counts
        lhs = _sides_counts(rx.replace("=", "->").split("->")[0])
        rhs = _sides_counts(rx.replace("=", "->").split("->")[1])
        dn = sum(rhs.values()) - sum(lhs.values())
        if kw.get("Kc") is not None:
            Kp = kw["Kc"] * (0.0821 * T) ** dn
            return {"Kp": round(Kp, 8), "delta_n_gas": dn, "from": "Kc"}
        Kc = kw["Kp"] / (0.0821 * T) ** dn
        return {"Kc": round(Kc, 8), "delta_n_gas": dn, "from": "Kp",
                "formula": "Kp = Kc(RT)^Δn, R = 0.0821"}
    if kind == "dissociation_alpha":
        Kp, P = kw["Kp"], kw["P_total"]
        alpha = math.sqrt(Kp / (P + Kp))
        return {"alpha": round(alpha, 6), "alpha_%": round(alpha * 100, 3),
                "note": "for A(g) ⇌ B(g) + C(g) type: Kp = α²P/(1−α²)"}
    raise ValueError("kind: kp_kc|dissociation_alpha")


def ionic_tools(kind: str, **kw):
    kind = str(kind).lower()
    if kind == "buffer_acidic":
        pKa = kw["pKa"]
        ratio = kw.get("ratio") or (kw["salt_moles"] / kw["acid_moles"])
        pH = pKa + math.log10(ratio)
        return {"pH": round(pH, 4), "ratio_salt/acid": round(ratio, 5),
                "formula": "Henderson: pH = pKa + log([A⁻]/[HA])"}
    if kind == "buffer_basic":
        pKb = kw["pKb"]
        ratio = kw.get("ratio") or (kw["salt_moles"] / kw["base_moles"])
        pOH = pKb + math.log10(ratio)
        return {"pOH": round(pOH, 4), "pH": round(14 - pOH, 4)}
    if kind == "solubility_from_ksp":
        Ksp, typ = kw["Ksp"], kw.get("type", "AB")
        exp = {"AB": 1 / 2, "AB2": 1 / 3, "A2B": 1 / 3, "AB3": 1 / 4, "A3B2": 1 / 5}.get(typ)
        if exp is None:
            raise ValueError("type: AB | AB2 | A2B | AB3 | A3B2")
        s = Ksp ** exp
        return {"solubility_mol/L": round(s, 8), "type": typ,
                "grams/L": round(s * molar_mass(kw["formula"])["molar_mass_g/mol"], 6) if kw.get("formula") else None}
    if kind == "ksp_from_solubility":
        s = kw["solubility_mol/L"]
        typ = kw.get("type", "AB")
        Ksp = {"AB": s * s, "AB2": s * (2 * s) ** 2, "A2B": (2 * s) ** 2 * s,
               "AB3": s * (3 * s) ** 3, "A3B2": (3 * s) ** 3 * (2 * s) ** 2}[typ]
        return {"Ksp": Ksp, "type": typ}
    if kind == "salt_ph":
        c = kw["c"]
        if kw.get("pKa") is not None and kw.get("pKb") is not None:
            pH = 7 + 0.5 * (kw["pKa"] - kw["pKb"])
            return {"pH": round(pH, 4), "salt_type": "weak acid + weak base"}
        if kw.get("pKa") is not None:
            pH = 7 + 0.5 * (kw["pKa"] + math.log10(c))
            return {"pH": round(pH, 4), "salt_type": "weak acid + strong base (e.g. CH₃COONa)"}
        if kw.get("pKb") is not None:
            pH = 7 - 0.5 * (kw["pKb"] + math.log10(c))
            return {"pH": round(pH, 4), "salt_type": "weak base + strong acid (e.g. NH₄Cl)"}
        raise ValueError("give pKa and/or pKb with concentration c")
    raise ValueError("kind: buffer_acidic|buffer_basic|solubility_from_ksp|ksp_from_solubility|salt_ph")


def oxidation_number(species: str, element: str, oxide_type: str = "normal"):
    core, charge = _parse_charge(species)
    if core in ("e", "E"):
        raise ValueError("that's an electron")
    counts = parse_formula(core)
    el = element.strip()
    el = el if el in counts else (el.capitalize() if len(el) <= 3 else el)
    if el not in counts:
        raise ValueError(f"{el} not in {species}. Elements: {list(counts)}")
    fixed = {}
    unknowns = []
    for e, c in counts.items():
        if e == el:
            unknowns.append((e, c))
            continue
        if e == "O":
            v = {"normal": -2, "peroxide": -1, "superoxide": -0.5, "of2": 2}[oxide_type]
        elif e == "H":
            v = -1 if (len(counts) == 2 and any(m in counts for m in
                    ("Li", "Na", "K", "Rb", "Cs", "Ca", "Mg", "Ba", "Al", "Zn"))) else 1
        elif e == "F":
            v = -1
        elif e in ("Li", "Na", "K", "Rb", "Cs"):
            v = 1
        elif e in ("Be", "Mg", "Ca", "Sr", "Ba"):
            v = 2
        elif e == "Al":
            v = 3
        elif e in ("Cl", "Br", "I"):
            if "O" in counts:
                unknowns.append((e, c))
                continue
            v = -1
        else:
            unknowns.append((e, c))
            continue
        fixed[e] = v
    known_sum = sum(fixed[e] * counts[e] for e in fixed)
    if len(unknowns) != 1:
        return {"error": f"Cannot uniquely assign — multiple unknown elements ({[u[0] for u in unknowns]}). "
                         "Give another known oxidation state in the problem.", "fixed": fixed}
    e, c = unknowns[0]
    x = (charge - known_sum) / c
    return {"element": e, "oxidation_number": x,
            "note": f"sum of ON × count = charge({charge}); fixed: {fixed}",
            "species_charge": charge}


def kinetics_tools(kind: str, **kw):
    kind = str(kind).lower()
    if kind == "first_order":
        k, c0 = kw["k"], kw.get("c0")
        out = {"t_half": round(math.log(2) / k, 6), "formula": "c = c₀e^(−kt), t½ = ln2/k"}
        if c0 is not None:
            if kw.get("t") is not None:
                ct = c0 * math.exp(-k * kw["t"])
                out.update({"c_now": round(ct, 8), "t": kw["t"]})
            if kw.get("c_now") is not None:
                out["t_needed"] = round(math.log(c0 / kw["c_now"]) / k, 6)
        return out
    if kind == "second_order":
        k, c0 = kw["k"], kw["c0"]
        out = {"t_half": round(1 / (k * c0), 6), "formula": "1/c = 1/c₀ + kt"}
        if kw.get("t") is not None:
            out["c_now"] = round(1 / (1 / c0 + k * kw["t"]), 8)
        return out
    if kind == "zero_order":
        k, c0 = kw["k"], kw["c0"]
        out = {"t_half": round(c0 / (2 * k), 6), "formula": "c = c₀ − kt"}
        if kw.get("t") is not None:
            out["c_now"] = round(c0 - k * kw["t"], 8)
        return out
    if kind == "arrhenius":
        Ea, T = kw["Ea"], kw["T"]
        if kw.get("A"):
            k = kw["A"] * math.exp(-Ea / (RGAS * T))
            return {"k": k, "formula": "k = A·e^(−Ea/RT)"}
        k1, T1, T2 = kw["k1"], kw["T1"], kw["T2"]
        ratio = math.exp(Ea / RGAS * (1 / T1 - 1 / T2))
        return {"k2/k1": round(ratio, 6), "k2": round(k1 * ratio, 8),
                "formula": "ln(k2/k1) = −Ea/R (1/T2 − 1/T1)"}
    raise ValueError("kind: first_order|second_order|zero_order|arrhenius")


def thermochem(kind: str, **kw):
    kind = str(kind).lower()
    if kind == "heat":
        return {"q_J": round(kw["m"] * kw["c"] * kw["dT"], 4)}
    if kind == "bond_enthalpy":
        broken, formed = kw["broken_kJ"], kw["formed_kJ"]
        dH = sum(broken) - sum(formed)
        return {"dH_kJ/mol": round(dH, 3), "endothermic": dH > 0,
                "formula": "ΔH = Σ(bonds broken) − Σ(bonds formed)"}
    if kind == "transition_entropy":
        dH, T = kw["dH_J"], kw["T"]
        return {"dS_J/K": round(dH / T, 5), "note": "ΔS = ΔH/T at equilibrium transition"}
    if kind == "calorimetry_dH":
        q = kw["m_solution"] * kw.get("c", 4.184) * kw["dT"]
        n = kw["moles_reactant"]
        return {"q_solution_J": round(q, 3), "dH_kJ/mol": round(-q / 1000 / n, 4),
                "note": "exothermic → negative ΔH (q of solution +, reaction −)"}
    raise ValueError("kind: heat|bond_enthalpy|transition_entropy|calorimetry_dH")


def electrochem2(kind: str, **kw):
    kind = str(kind).lower()
    if kind == "molar_conductivity":
        kappa, M = kw["kappa_S_per_cm"], kw["M"]
        return {"Lambda_m_S_cm2/mol": round(1000 * kappa / M, 4),
                "formula": "Λm = 1000κ/M"}
    if kind == "degree_dissociation":
        return {"alpha": round(kw["Lambda_m"] / kw["Lambda_m0"], 5),
                "alpha_%": round(100 * kw["Lambda_m"] / kw["Lambda_m0"], 3)}
    if kind == "cell_potential":
        anode, cathode = kw["E_anode"], kw["E_cathode"]
        return {"E_cell": round(cathode - anode, 5),
                "note": "E°cell = E°cathode − E°anode (reduction potentials)",
                "spontaneous": (cathode - anode) > 0}
    if kind == "nernst_conc":
        E0, n, c_ox, c_red = kw["E0"], kw["n"], kw.get("c_oxidized", 1), kw.get("c_reduced", 1)
        Q = c_red / c_ox if kw.get("Q_is_redox", False) else c_ox / c_red
        E = E0 - (0.0591 / n) * math.log10(Q)
        return {"E": round(E, 5), "Q_used": round(Q, 8)}
    raise ValueError("kind: molar_conductivity|degree_dissociation|cell_potential|nernst_conc")


_VALENCE = {"H": 1, "He": 2, "Li": 1, "Be": 2, "B": 3, "C": 4, "N": 5, "O": 6, "F": 7}
_ZATOM = {"H": 1, "He": 2, "Li": 3, "Be": 4, "B": 5, "C": 6, "N": 7, "O": 8, "F": 9}


def bond_order_mo(species: str):
    """MO bond order & magnetism for diatomics/ions (B2…F2, O2^2-, NO, NO+, CN-, CO…).
    In this tool the digit before +/- is always a SUBSCRIPT (O2- = superoxide)."""
    s = str(species).strip()
    charge = 0
    m = re.search(r"\^(\d*)([+-])$", s)
    if m:
        mag = int(m.group(1)) if m.group(1) else 1
        charge = mag if m.group(2) == "+" else -mag
        core = s[:m.start()].strip()
    else:
        m = re.search(r"([+-]{1,2})$", s)
        if m:
            signs = m.group(1)
            charge = len(signs) if signs[0] == "+" else -len(signs)
            core = s[:m.start()].strip()
        else:
            core = s
    if core.lower() in ("e",):
        raise ValueError("that's an electron")
    counts = parse_formula(core)
    if len(counts) > 2:
        raise ValueError("only diatomic species supported")
    total_val = sum(_VALENCE[e] * c for e, c in counts.items()) - charge
    total_e = sum(_ZATOM.get(e, _VALENCE[e] + 2) * c for e, c in counts.items()) - charge
    sigma_first = total_e > 14   # O2, F2, NO+: σ2p below π2p; B2, C2, N2: π2p below σ2p
    # groups in energy order; label: (name, is_bonding, capacity_group_size)
    mid = ([("P", True)], [("p", True), ("p", True)]) if sigma_first \
        else ([("p", True), ("p", True)], [("P", True)])
    groups = [[("s", True)], [("s*", False)], list(mid[0]), list(mid[1]),
              [("q*", False), ("q*", False)], [("Q*", False)]]
    e_left = total_val
    bonding = antibonding = unpaired = 0
    for grp in groups:
        name, is_b = grp[0]
        cap = 2 * len(grp)
        take = min(e_left, cap)
        e_left -= take
        if is_b:
            bonding += take
        else:
            antibonding += take
        singles = min(take, len(grp))          # Hund: one per orbital first
        pairs = take - singles                 # then pair up
        unpaired += singles - pairs
    bo = (bonding - antibonding) / 2
    return {"valence_electrons": total_val, "bond_order": bo,
            "bonding_e": bonding, "antibonding_e": antibonding,
            "magnetism": "paramagnetic" if unpaired else "diamagnetic",
            "unpaired_electrons": unpaired,
            "stability": "stable" if bo > 0 else "unstable",
            "filling": "σ2p before π2p (O2/F2-type)" if sigma_first else "π2p before σ2p (B2–N2-type)"}


def coordination(kind: str, **kw):
    kind = str(kind).lower()
    if kind == "magnetic_moment":
        n = kw["n_unpaired"]
        mu = math.sqrt(n * (n + 2))
        return {"spin_only_mu_BM": round(mu, 4), "n_unpaired": n,
                "formula": "μ = √(n(n+2)) BM"}
    if kind == "ean":
        Z, ox, cn = kw["Z"], kw["ox_state"], kw["coordination_number"]
        ean = Z - ox + 2 * cn
        return {"EAN": ean, "noble_gas_check": {36: "Kr", 54: "Xe", 86: "Rn"}.get(ean, f"not a noble gas count ({ean})")}
    if kind == "cfse":
        dn, geom, strong = int(kw["d_n"]), kw.get("geometry", "oct"), kw.get("strong_field", False)
        if not 1 <= dn <= 9:
            raise ValueError("d_n between 1 and 9")
        # orbitals: oct: t2g(3, -0.4Δo) eg(2, +0.6Δo); tet: e(2, -0.6Δt) t2(3, +0.4Δt)
        if geom.startswith("oct"):
            low, high = ["t2g"] * 3 + ["eg"] * 2, ["t2g"] * 3 + ["eg"] * 2
            energy = {"t2g": -0.4, "eg": 0.6}
            fill_order = ["t2g", "t2g", "t2g", "eg", "eg"] if not strong else None
            units = "Δo"
        else:
            energy = {"e": -0.6, "t2": 0.4}
            fill_order = ["e", "e", "t2", "t2", "t2"]
            units = "Δt"
        orbs = (["t2g", "t2g", "t2g", "eg", "eg"] if geom.startswith("oct") else ["e", "e", "t2", "t2", "t2"])
        occ = []
        if geom.startswith("oct") and strong:
            # pair in t2g before occupying eg
            for i in range(dn):
                # fill first 3 singly, then pair t2g, only then eg
                placed = False
                for orb in ["t2g0", "t2g1", "t2g2"]:
                    pass
                placed = True
                break
            # simpler explicit:
            t2 = min(dn, 6)
            eg = max(dn - 6, 0) if dn > 6 else 0
            if dn <= 3:
                t2, eg = dn, 0
            occ_counts = {"t2g": t2, "eg": eg}
            pairs = max((dn - 3), 0) if dn <= 6 else (3 if dn <= 8 else 4)
            # recompute properly: strong oct: d4: t2g4eg0(1 pair) d5: t2g5(2) d6: t2g6(3) d7: t2g6eg1(3) d8: t2g6eg2(4)
            pairs = {1: 0, 2: 0, 3: 0, 4: 1, 5: 2, 6: 3, 7: 3, 8: 4, 9: 4}[dn]
            cfse = energy["t2g"] * t2 + energy["eg"] * eg
            return {"configuration": f"t2g{t2} eg{eg}", "CFSE": round(cfse, 2), "units": units,
                    "pairs": pairs, "note": f"strong-field octahedral d^{dn}"}
        # weak (Hund across all five)
        slots = [[] for _ in range(5)]
        order = orbs
        for i in range(dn):
            # fill singly first
            for s_i, s in enumerate(slots):
                if len(s) == 0:
                    slots[s_i].append(1)
                    break
            else:
                for s_i, s in enumerate(slots):
                    if len(s) == 1:
                        slots[s_i].append(1)
                        break
        counts = {}
        for s_i, s in enumerate(slots):
            counts[order[s_i]] = counts.get(order[s_i], 0) + len(s)
        cfse = sum(energy[k] * v for k, v in counts.items())
        pairs = sum(1 for s in slots if len(s) == 2)
        cfg = " ".join(f"{k}{v}" for k, v in counts.items())
        return {"configuration": cfg, "CFSE": round(cfse, 2), "units": units,
                "pairs": pairs, "unpaired": sum(1 for s in slots if len(s) == 1),
                "note": f"{'weak-field ' if not strong else ''}{geom[:3]}ahedral d^{dn}"}
    raise ValueError("kind: magnetic_moment|ean|cfse")


def organic_tools(kind: str, **kw):
    kind = str(kind).lower()
    if kind == "dou":
        return degree_unsaturation(kw["formula"])
    if kind == "percent_composition":
        comp = kw["composition"]  # {element: mass fraction or %}
        tot = sum(comp.values())
        moles = {el: v / ATOMIC_MASSES[el] for el, v in comp.items()}
        mn = min(moles.values())
        pct = {el: round(100 * v / tot, 3) for el, v in comp.items()}
        return {"percent": pct, "mole_ratios": {el: round(v / mn, 3) for el, v in moles.items()}}
    if kind == "iupac_unsat_note":
        return {"note": "organic mechanisms/nomenclature handled by the LLM directly"}
    raise ValueError("kind: dou|percent_composition")


def solutions_extra(kind: str, **kw):
    kind = str(kind).lower()
    if kind == "raoult_lowering":
        P0, x = kw["P0"], kw["x_solute"]
        return {"delta_P": round(P0 * x, 6), "relative_lowering": round(x, 6),
                "formula": "ΔP/P° = x_solute"}
    if kind == "henry":
        KH, x = kw["KH"], kw["x"]
        return {"p": round(KH * x, 6), "formula": "p = KH·x"}
    if kind == "vapor_ideal":
        P1o, P2o, x1 = kw["P1_deg"], kw["P2_deg"], kw["x1"]
        x2 = 1 - x1
        Ptot = P1o * x1 + P2o * x2
        return {"P_total": round(Ptot, 5), "y1_vapor": round(P1o * x1 / Ptot, 5),
                "y2_vapor": round(P2o * x2 / Ptot, 5),
                "note": "ideal solution, Dalton + Raoult"}
    raise ValueError("kind: raoult_lowering|henry|vapor_ideal")
