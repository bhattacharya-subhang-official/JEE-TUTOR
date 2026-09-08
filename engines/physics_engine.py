"""PHYSICS engine — verified formula solvers for JEE-Advanced (Mechanics, Waves, Optics,
Electricity & Magnetism, Modern Physics, Thermo). All return plain dicts with units noted."""
import math

import sympy as sp

OUT = {}


def _r(v):  # round nicely
    try:
        f = float(v)
        return round(f, 6) if abs(f) > 1e-4 or f == 0 else f
    except Exception:
        return v


def projectile(v0: float, angle_deg: float, g: float = 9.8, h0: float = 0.0):
    th = math.radians(angle_deg)
    vy, vx = v0 * math.sin(th), v0 * math.cos(th)
    disc = vy * vy + 2 * g * h0
    T = (vy + math.sqrt(disc)) / g
    R = vx * T
    H = h0 + vy * vy / (2 * g)
    return {"time_of_flight_s": _r(T), "range_m": _r(R), "max_height_m": _r(H),
            "v_x": _r(vx), "v_y0": _r(vy),
            "trajectory": "y(x) = h0 + x·tanθ − g·x²/(2v₀²cos²θ)",
            "note": "Projectile from height h0 above launch-reference ground."}


def suvat(u=None, v=None, a=None, s=None, t=None):
    """Solve the SUVAT system — give any 3 or 4 of u, v, a, s, t (others None)."""
    vals = {"u": u, "v": v, "a": a, "s": s, "t": t}
    known = {k for k, val in vals.items() if val is not None}
    out = {k: _r(val) for k, val in vals.items() if val is not None}

    def done():
        return len(out) == 5
    try:
        # --- 4-known cases: solve the single missing value
        if not done() and "u" not in out and {"v", "a", "t"} <= known:
            out["u"] = _r(v - a * t)
        if not done() and "u" not in out and {"v", "s", "t"} <= known:
            out["u"] = _r(2 * s / t - v)
        if not done() and "u" not in out and {"v", "a", "s"} <= known:
            disc = v * v - 2 * a * s
            if disc < 0:
                return {"error": "No real solution (u² = v² − 2as < 0) — check signs."}
            out["u"] = _r(math.sqrt(disc))
        if not done() and "v" not in out and {"u", "a", "t"} <= known:
            out["v"] = _r(u + a * t)
        if not done() and "v" not in out and {"u", "s", "t"} <= known:
            out["v"] = _r(2 * s / t - u)
        if not done() and "v" not in out and {"u", "a", "s"} <= known:
            disc = u * u + 2 * a * s
            if disc < 0:
                return {"error": "No real solution (v² = u² + 2as < 0) — check signs."}
            out["v"] = _r(math.sqrt(disc))
        if not done() and "a" not in out and {"v", "u", "t"} <= known and t != 0:
            out["a"] = _r((v - u) / t)
        if not done() and "a" not in out and {"v", "u", "s"} <= known and s != 0:
            out["a"] = _r((v * v - u * u) / (2 * s))
        if not done() and "a" not in out and {"u", "s", "t"} <= known and t != 0:
            out["a"] = _r(2 * (s - u * t) / (t * t))
        if not done() and "a" not in out and {"v", "s", "t"} <= known and t != 0:
            out["a"] = _r(2 * (s - v * t) / (t * t))
        if not done() and "s" not in out and {"u", "a", "t"} <= known:
            out["s"] = _r(u * t + 0.5 * a * t * t)
        if not done() and "s" not in out and {"u", "v", "a"} <= known and a != 0:
            out["s"] = _r((v * v - u * u) / (2 * a))
        if not done() and "s" not in out and {"u", "v", "t"} <= known:
            out["s"] = _r(0.5 * (u + v) * t)
        if not done() and "t" not in out and {"v", "u", "a"} <= known and a != 0:
            out["t"] = _r((v - u) / a)
        if not done() and "t" not in out and {"u", "a", "s"} <= known and a != 0:
            disc = u * u + 2 * a * s
            if disc < 0:
                return {"error": "No real time solution (u² + 2as < 0)."}
            t1 = (-u + math.sqrt(disc)) / a
            t2 = (-u - math.sqrt(disc)) / a
            tt = t1 if t1 >= 0 else t2
            out["t"] = _r(tt)
            if out.get("v") is None:
                out["v"] = _r(u + a * tt)
        if not done() and "t" not in out and {"u", "v", "s"} <= known and (u + v) != 0:
            out["t"] = _r(2 * s / (u + v))
        if not done() and "t" not in out and {"a", "s", "v"} <= known and a != 0:
            disc = v * v - 2 * a * s
            tt = (v - math.sqrt(disc)) / a if disc >= 0 else None
            if tt is not None:
                out["t"] = _r(tt)
        if not done() and "u" not in out and {"a", "s", "t"} <= known and t != 0:
            out["u"] = _r((s - 0.5 * a * t * t) / t)
        if not done() and "v" not in out and {"a", "s", "t"} <= known:
            out["v"] = _r(math.sqrt(max(2 * a * s + (out.get("u") or 0) ** 2, 0)))
        if not done() and "u" not in out and {"v", "a", "t"} <= known:
            out["u"] = _r(v - a * t)
        if not done() and "v" not in out and {"u", "a", "t"} <= known:
            out["v"] = _r(u + a * t)
    except Exception as e:
        return {"error": f"suvat solve failed: {e} — check the given combination is consistent."}
    if not done():
        return {"error": f"Could not determine all values. Known: {sorted(known)} — provide at least 3 of u, v, a, s, t.",
                "partial": out}
    out["note"] = "All quantities along one axis; sign indicates direction (SI units)."
    return out


def circular_motion(m: float, v: float, r: float):
    ac = v * v / r
    return {"centripetal_accel_m/s2": _r(ac), "centripetal_force_N": _r(m * ac),
            "angular_velocity_rad/s": _r(v / r), "period_s": _r(2 * math.pi * r / v)}


def shm(m: float = None, k: float = None, A: float = None, g: float = 9.8):
    out = {}
    if m and k:
        omega = math.sqrt(k / m)
        out.update({"omega_rad/s": _r(omega), "period_s": _r(2 * math.pi / omega),
                    "frequency_Hz": _r(omega / (2 * math.pi))})
    if k is not None and A is not None:
        out["max_energy_J"] = _r(0.5 * k * A * A)
    if m and k and A:
        out["max_speed_m/s"] = _r(A * math.sqrt(k / m))
    return out or {"error": "provide m, k and optionally A"}


def gravitation(M: float = None, R: float = None, r: float = None, h: float = None, m: float = None):
    G = 6.674e-11
    out = {}
    if M and R:
        out["escape_velocity_m/s"] = _r(math.sqrt(2 * G * M / R))
        out["surface_g_m/s2"] = _r(G * M / R / R)
    if M and r:
        out["orbital_velocity_m/s"] = _r(math.sqrt(G * M / r))
        out["orbital_period_s"] = _r(2 * math.pi * math.sqrt(r**3 / (G * M)))
    if M and r and m:
        out["PE_J"] = _r(-G * M * m / r)
    if R and h:
        out["g_at_height_m/s2"] = _r(9.8 * (R / (R + h))**2)
    return out or {"error": "provide M with R and/or r"}


def collisions(m1: float, m2: float, u1: float, u2: float, e: float = None):
    """1-D collision. e=1 elastic, e=0 perfectly inelastic, else coefficient of restitution."""
    if e is None:
        e = 1.0
    if e == 1.0:
        v1 = ((m1 - m2) * u1 + 2 * m2 * u2) / (m1 + m2)
        v2 = ((m2 - m1) * u2 + 2 * m1 * u1) / (m1 + m2)
    elif e == 0.0:
        v1 = v2 = (m1 * u1 + m2 * u2) / (m1 + m2)
    else:
        vcm = (m1 * u1 + m2 * u2) / (m1 + m2)
        v1 = vcm + e * m2 * (u2 - u1) / (m1 + m2)
        v2 = vcm + e * m1 * (u1 - u2) / (m1 + m2)
    ke_i = 0.5 * m1 * u1**2 + 0.5 * m2 * u2**2
    ke_f = 0.5 * m1 * v1**2 + 0.5 * m2 * v2**2
    return {"v1_final_m/s": _r(v1), "v2_final_m/s": _r(v2),
            "KE_initial_J": _r(ke_i), "KE_final_J": _r(ke_f), "KE_lost_J": _r(ke_i - ke_f)}


def rotation(I: float = None, alpha: float = None, tau: float = None, L: float = None, omega: float = None, KE: float = None):
    out = {}
    if I and omega:
        out["angular_momentum"] = _r(I * omega); out["KE_J"] = _r(0.5 * I * omega**2)
    if tau is not None and I is not None:
        out["alpha_rad/s2"] = _r(tau / I)
    if tau is not None and alpha is not None:
        out["moment_of_inertia"] = _r(tau / alpha)
    if L is not None and I is not None:
        out["omega_rad/s"] = _r(L / I)
    out["help"] = "MOI: ring mR², disc ½mR², rod-center mL²/12, rod-end mL²/3, solid sphere ⅖mR², shell ⅔mR², block a²/6, plate ⅟₁₂m(a²+b²)"
    return out


def coulomb(q1: float, q2: float, r: float, medium_k: float = 1.0):
    k = 8.9875517923e9 / medium_k
    F = k * q1 * q2 / r**2
    return {"force_N": _r(F), "attraction" if (q1 * q2 < 0) else "repulsion": True,
            "field_at_r_N/C": _r(abs(F / (q1 if q1 else 1)))}


def electric_field_point(q: float, r: float, medium_k: float = 1.0):
    k = 8.9875517923e9 / medium_k
    return {"E_N/C": _r(k * abs(q) / r**2), "V_volt": _r(k * q / r)}


def capacitors(capacitances: list, mode: str, V: float = None):
    cs = [float(c) for c in capacitances]
    if mode == "series":
        Ceq = 1.0 / sum(1 / c for c in cs)
    elif mode == "parallel":
        Ceq = sum(cs)
    else:
        return {"error": "mode = series | parallel"}
    out = {"C_eq_farad": _r(Ceq)}
    if V:
        out["energy_J"] = _r(0.5 * Ceq * V * V); out["total_charge_C"] = _r(Ceq * V)
    return out


def current_electricity(V: float = None, I: float = None, R: float = None, t: float = None):
    out = {}
    if V is not None and R is not None:
        I = V / R
    elif V is not None and I is not None:
        R = V / I
    elif I is not None and R is not None:
        V = I * R
    else:
        return {"error": "provide any 2 of V, I, R"}
    out.update({"V_volt": _r(V), "I_amp": _r(I), "R_ohm": _r(R), "power_W": _r(V * I)})
    if t is not None:
        out["heat_J"] = _r(V * I * t)
    return out


def optics(kind: str, f: float, u: float, h: float = None):
    """Cartesian convention: distances measured pole→object against incident light negative.
    kind: 'lens' (converging f>0) or 'mirror' (concave f<0)."""
    if kind == "lens":
        v = 1 / (1 / f + 1 / u)
        m = v / u
    else:
        v = 1 / (1 / f - 1 / u)
        m = -v / u
    out = {"v": _r(v), "magnification": _r(m), "nature": "real" if (kind == "lens" and v > 0) or (kind == "mirror" and v < 0) else "virtual",
           "orientation": "inverted" if m < 0 else "erect"}
    if h is not None:
        out["image_height"] = _r(m * h)
    out["note"] = "Lens: 1/v − 1/u = 1/f. Mirror: 1/v + 1/u = 1/f. Cartesian signs."
    return out


def doppler(f0: float, wave_speed: float, v_source: float = 0.0, v_observer: float = 0.0):
    """v_source/v_observer > 0 means approaching."""
    f = f0 * (wave_speed + v_observer) / max(wave_speed - v_source, 1e-9)
    return {"apparent_frequency_Hz": _r(f), "shift_Hz": _r(f - f0)}


def sound_wave(f: float = None, v: float = 343.0, lam: float = None):
    if f and not lam:
        lam = v / f
    elif lam and not f:
        f = v / lam
    return {"frequency_Hz": _r(f), "wavelength_m": _r(lam), "speed_m/s": v}


def wave_optics_interference(d: float, lam: float, D: float, order: float = 1.0):
    return {"fringe_width_m": _r(lam * D / d), "y_bright_m": _r(order * lam * D / d),
            "y_dark_m": _r((order - 0.5) * lam * D / d)}


def modern_physics(kind: str, phi_eV: float = None, wavelength_m: float = None, freq: float = None,
                   V_volt: float = None, m: float = None, v: float = None, KE_J: float = None, Z: int = None, n: int = None):
    h, c, e = 6.62607015e-34, 2.99792458e8, 1.602176634e-19
    out = {}
    if kind == "photoelectric":
        E = h * freq if freq else h * c / wavelength_m
        Kmax = E - phi_eV * e
        out.update({"photon_energy_J": _r(E), "photon_energy_eV": _r(E / e),
                    "Kmax_J": _r(Kmax), "Kmax_eV": _r(Kmax / e),
                    "stopping_potential_V": _r(max(Kmax, 0) / e),
                    "threshold_wavelength_m": _r(h * c / (phi_eV * e))})
    elif kind == "de_broglie":
        if m and v:
            out["lambda_m"] = _r(h / (m * v))
        elif KE_J and m:
            out["lambda_m"] = _r(h / math.sqrt(2 * m * KE_J))
        elif V_volt:
            out["lambda_electron_m"] = _r(12.27e-10 / math.sqrt(V_volt))
    elif kind == "bohr":
        if Z and n:
            out["E_n_eV"] = _r(-13.6 * Z * Z / (n * n))
            out["r_n_m"] = _r(0.529e-10 * n * n / Z)
            out["v_n_m/s"] = _r(2.188e6 * Z / n)
            if n > 1:
                out["transition_to_ground_eV"] = _r(13.6 * Z * Z * (1 - 1 / (n * n)))
    elif kind == "radioactivity":
        out["help"] = "N = N0·e^(−λt), t½ = ln2/λ, activity A = λN"
    return out or {"error": "kind: photoelectric | de_broglie | bohr | radioactivity"}


def thermodynamics(kind: str, n: float = None, T: float = None, P: float = None, V: float = None,
                   dU: float = None, W: float = None, Q: float = None, gamma: float = None):
    R = 8.314
    out = {}
    if kind == "ideal_gas":
        known = [x for x in (P, V, n, T) if x is not None]
        if len(known) == 3:
            if P is None: out["P_Pa"] = _r(n * R * T / V)
            elif V is None: out["V_m3"] = _r(n * R * T / P)
            elif n is None: out["n_mol"] = _r(P * V / (R * T))
            elif T is None: out["T_K"] = _r(P * V / (n * R))
        else:
            return {"error": "provide any 3 of P(Pa), V(m³), n(mol), T(K)"}
    elif kind == "first_law":
        if dU is not None and W is not None:
            out["Q_J"] = _r(dU + W)
        elif Q is not None and W is not None:
            out["dU_J"] = _r(Q - W)
        elif Q is not None and dU is not None:
            out["W_J"] = _r(Q - dU)
        else:
            return {"error": "provide any 2 of dU, W, Q (Q−W=ΔU, W by gas)"}
    elif kind == "process":
        if gamma and T is not None:
            out["Cv_molar"] = _r(R / (gamma - 1)); out["Cp_molar"] = _r(gamma * R / (gamma - 1))
            f = 2 / (gamma - 1)
            out["degrees_of_freedom"] = _r(f)
    return out


def current_magnetism(kind: str, **kw):
    out = {}
    if kind == "lorentz":
        q, v, B, th = kw.get("q", 1.6e-19), kw["v"], kw["B"], kw.get("theta_deg", 90)
        F = q * v * B * math.sin(math.radians(th))
        out.update({"force_N": _r(abs(F)), "radius_m": _r(kw.get("m", 9.1e-31) * v / (abs(q) * B)) if B else None})
    elif kind == "wire_field":
        I, d = kw["I"], kw["d"]
        out["B_T"] = _r(1e-7 * 2 * math.pi * I / d)
    elif kind == "solenoid":
        n_turns, I, mu_r = kw["n_per_m"], kw["I"], kw.get("mu_r", 1.0)
        out["B_T"] = _r(4 * math.pi * 1e-7 * mu_r * n_turns * I)
    elif kind == "induction":
        out["emf_V"] = _r(abs(kw["dPhi_dt"]))
    return out


# ═════════════════════════ JEE-ADV FULL SYLLABUS EXTENSIONS ═════════════════════════
_G = 9.8


def friction_incline(m: float, angle_deg: float, mu_s: float = None, mu_k: float = None,
                     applied_N: float = 0.0, g: float = _G):
    """Block on incline: static/kinetic friction analysis. applied_N along incline, up = +."""
    th = math.radians(angle_deg)
    N = m * g * math.cos(th)
    drive = m * g * math.sin(th) - applied_N        # + = down-slope pull (no friction)
    fmax = (mu_s if mu_s is not None else 0) * N
    if abs(drive) <= fmax:
        return {"normal_N": _r(N), "state": "STATIC — equilibrium",
                "friction_N": _r(drive), "f_max_static": _r(fmax),
                "acceleration_m/s2": 0.0,
                "note": "Static friction self-adjusts to balance the driving force."}
    a = (drive - math.copysign((mu_k or 0) * N, drive)) / m
    return {"normal_N": _r(N), "state": "SLIDING", "f_max_static": _r(fmax),
            "friction_N": _r(math.copysign((mu_k or 0) * N, -drive)),
            "acceleration_m/s2": _r(a),
            "direction": "down the incline" if a > 0 else "up the incline"}


def work_energy(kind: str, **kw):
    kind = str(kind).lower()
    if kind == "work":
        F, d, th = kw["F"], kw["d"], math.radians(kw.get("theta_deg", 0))
        return {"work_J": _r(F * d * math.cos(th))}
    if kind == "ke":
        return {"KE_J": _r(0.5 * kw["m"] * kw["v"] ** 2)}
    if kind == "pe":
        return {"PE_J": _r(kw["m"] * kw.get("g", _G) * kw["h"])}
    if kind == "spring_pe":
        return {"PE_J": _r(0.5 * kw["k"] * kw["x"] ** 2)}
    if kind == "power_work":
        return {"power_W": _r(kw["W"] / kw["t"])}
    if kind == "power_force":
        th = math.radians(kw.get("theta_deg", 0))
        return {"power_W": _r(kw["F"] * kw["v"] * math.cos(th))}
    if kind == "efficiency":
        return {"efficiency_%": _r(100 * kw["out"] / kw["in"]),
                "note": "out = useful output energy/power, in = input"}
    if kind == "work_energy_theorem":
        m, v1, v2 = kw["m"], kw["v1"], kw["v2"]
        return {"W_net_J": _r(0.5 * m * (v2 ** 2 - v1 ** 2))}
    raise ValueError("kind: work|ke|pe|spring_pe|power_work|power_force|efficiency|work_energy_theorem")


def momentum(kind: str, **kw):
    kind = str(kind).lower()
    if kind == "center_of_mass":
        masses = kw["masses"]  # [[m, x, y, z?]...]
        dim = len(masses[0]) - 1
        M = sum(r[0] for r in masses)
        com = [sum(r[0] * r[i + 1] for r in masses) / M for i in range(dim)]
        return {"total_mass": _r(M), "com": [_r(c) for c in com]}
    if kind == "impulse":
        if kw.get("F") is not None and kw.get("t") is not None:
            J = kw["F"] * kw["t"]
            out = {"impulse_Ns": _r(J)}
            if kw.get("m"):
                out["delta_v_m/s"] = _r(J / kw["m"])
            return out
        if kw.get("dp") is not None and kw.get("t") is not None:
            return {"force_N": _r(kw["dp"] / kw["t"])}
        return {"impulse_Ns": _r(kw["dp"])}
    if kind == "conservation_1d":
        m1, m2, u1, u2 = kw["m1"], kw["m2"], kw["u1"], kw["u2"]
        P = m1 * u1 + m2 * u2
        vcm = P / (m1 + m2)
        return {"p_total": _r(P), "v_cm_m/s": _r(vcm),
                "KE_total_J": _r(0.5 * m1 * u1 ** 2 + 0.5 * m2 * u2 ** 2)}
    if kind == "variable_mass_rocket":
        return {"thrust_N": _r(kw["v_rel"] * abs(kw["dm_dt"])),
                "note": "F = v_rel·(dm/dt), dm/dt > 0 for ejecting mass"}
    raise ValueError("kind: center_of_mass|impulse|conservation_1d|variable_mass_rocket")


def fluids(kind: str, **kw):
    kind = str(kind).lower()
    g = kw.get("g", _G)
    if kind == "buoyant_force":
        return {"buoyant_force_N": _r(kw["rho_fluid"] * kw["V"] * g),
                "note": "F_B = ρ_fluid·V_submerged·g (Archimedes)"}
    if kind == "float_fraction":
        f = kw["rho_obj"] / kw["rho_fluid"]
        return {"submerged_fraction": _r(f), "above_fraction": _r(1 - f),
                "floats": f < 1}
    if kind == "apparent_weight":
        m, ro, rf = kw["m"], kw["rho_obj"], kw["rho_fluid"]
        W = m * g
        B = (m / ro) * rf * g
        return {"true_weight_N": _r(W), "buoyant_N": _r(B), "apparent_weight_N": _r(W - B)}
    if kind == "bernoulli":
        P1, v1, h1 = kw["P1"], kw["v1"], kw["h1"]
        rho = kw["rho"]
        missing = [k for k, v in (("P2", kw.get("P2")), ("v2", kw.get("v2")), ("h2", kw.get("h2"))) if v is None]
        if len(missing) == 1:
            tot = P1 + 0.5 * rho * v1 ** 2 + rho * g * h1
            m_ = missing[0]
            if m_ == "P2":
                return {"P2_Pa": _r(tot - 0.5 * rho * kw["v2"] ** 2 - rho * g * kw["h2"]), "solved": "P2"}
            if m_ == "v2":
                val = (tot - kw["P2"] - rho * g * kw["h2"]) * 2 / rho
                if val < 0:
                    return {"error": "Negative v² — inconsistent Bernoulli data"}
                return {"v2_m/s": _r(math.sqrt(val)), "solved": "v2"}
            if m_ == "h2":
                return {"h2_m": _r((tot - kw["P2"] - 0.5 * rho * kw["v2"] ** 2) / (rho * g)), "solved": "h2"}
        known = [x for x in (kw.get("P2"), kw.get("v2"), kw.get("h2")) if x is not None]
        if not missing and known == 3:
            dP = (kw["P2"] + 0.5 * rho * kw["v2"] ** 2 + rho * g * kw["h2"]) - (P1 + 0.5 * rho * v1 ** 2 + rho * g * h1)
            return {"pressure_difference_Pa": _r(-dP), "bernoulli_constant": _r(P1 + 0.5 * rho * v1 ** 2 + rho * g * h1)}
        return {"error": "Give P1, v1, h1, rho and exactly two of (P2, v2, h2) — or all three to get ΔP."}
    if kind == "continuity":
        return {"v2_m/s": _r(kw["A1"] * kw["v1"] / kw["A2"]), "flow_rate_m3/s": _r(kw["A1"] * kw["v1"])}
    if kind == "torricelli":
        v = math.sqrt(2 * g * kw["h"])
        out = {"efflux_speed_m/s": _r(v)}
        if kw.get("A"):
            out["flow_rate_m3/s"] = _r(kw["A"] * v)
        return out
    if kind == "stokes_terminal":
        r, rs, rf, eta = kw["r"], kw["rho_s"], kw["rho_f"], kw["eta"]
        v = 2 * r * r * g * (rs - rf) / (9 * eta)
        return {"terminal_velocity_m/s": _r(v), "direction": "down" if v > 0 else "up",
                "formula": "v = 2r²g(ρs−ρf)/9η"}
    if kind == "reynolds":
        Re = kw["rho"] * kw["v"] * kw["D"] / kw["eta"]
        return {"Re": _r(Re), "flow": "laminar" if Re < 2000 else ("turbulent" if Re > 4000 else "transitional")}
    if kind == "capillary_rise":
        th = math.radians(kw.get("theta_deg", 0))
        h = 2 * kw["sigma"] * math.cos(th) / (kw["rho"] * kw["r"] * g)
        return {"rise_m": _r(h), "formula": "h = 2σcosθ/(ρgr)"}
    if kind == "excess_pressure":
        sig, r = kw["sigma"], kw["r"]
        kind_b = kw.get("bubble", "drop")
        f = {"drop": 2, "soap_bubble": 4, "air_bubble": 2}.get(kind_b, 2)
        return {"excess_pressure_Pa": _r(f * sig / r), "type": kind_b}
    if kind == "pascal_hydraulic":
        return {"F2_N": _r(kw["F1"] * kw["A2"] / kw["A1"]),
                "note": "F1/A1 = F2/A2 (pressure transmitted equally)"}
    if kind == "venturineflow":
        pass
    raise ValueError("kind: buoyant_force|float_fraction|apparent_weight|bernoulli|continuity|torricelli|stokes_terminal|reynolds|capillary_rise|excess_pressure|pascal_hydraulic")


def elasticity(kind: str, **kw):
    kind = str(kind).lower()
    if kind == "youngs":
        F, A, dl, L = kw["F"], kw["A"], kw["dl"], kw["L"]
        stress = F / A
        strain = dl / L
        return {"stress_N/m2": _r(stress), "strain": _r(strain),
                "youngs_modulus_Pa": _r(stress / strain),
                "energy_stored_J": _r(0.5 * F * dl)}
    if kind == "thermal_stress":
        return {"stress_Pa": _r(-kw["Y"] * kw["alpha"] * kw["dT"]),
                "force_N": _r(-kw["Y"] * kw["alpha"] * kw["dT"] * kw.get("A", 1)),
                "note": "rod fixed at both ends, temperature change dT"}
    if kind == "poisson":
        return {"poisson_ratio": _r(-kw["dlateral"] / kw["d_longitudinal"] * (kw["L_lateral"] / kw["L_long"]))}
    raise ValueError("kind: youngs|thermal_stress|poisson")


def thermal(kind: str, **kw):
    kind = str(kind).lower()
    if kind == "calorimetry":
        return {"Q_J": _r(kw["m"] * kw["c"] * kw["dT"]),
                "note": "Q = mcΔT; add Q = mL for phase change"}
    if kind == "latent":
        return {"Q_J": _r(kw["m"] * kw["L"])}
    if kind == "mixing":
        m1, c1, T1 = kw["m1"], kw["c1"], kw["T1"]
        m2, c2, T2 = kw["m2"], kw["c2"], kw["T2"]
        Tf = (m1 * c1 * T1 + m2 * c2 * T2) / (m1 * c1 + m2 * c2)
        return {"final_temp": _r(Tf), "note": "no phase change assumed; same units for T in/out"}
    if kind == "expansion":
        mode = kw.get("mode", "linear")
        a = kw["alpha"]
        L0, dT = kw["L0"], kw["dT"]
        mult = {"linear": 1, "area": 2, "volume": 3}[mode]
        beta = mult * a
        d = L0 * beta * dT
        return {f"delta_{mode}": _r(d), f"coeff_{mode}": _r(beta),
                "final_size": _r(L0 + d)}
    if kind == "conduction":
        k, A, dT, L = kw["k"], kw["A"], kw["dT"], kw["L"]
        return {"rate_W": _r(k * A * dT / L), "thermal_resistance_K/W": _r(L / (k * A)),
                "formula": "P = kAΔT/L"}
    if kind == "conduction_series":
        rods = kw["rods"]  # [{k, L, A}]
        R = sum(r["L"] / (r["k"] * r["A"]) for r in rods)
        return {"total_R_K/W": _r(R), "rate_W": _r(kw["dT"] / R),
                "interface_note": "same P through every rod in series"}
    if kind == "stefan":
        sig = 5.670374419e-8
        T, T0 = kw["T"], kw.get("T0", 0)
        return {"net_power_W": _r(kw["e"] * sig * kw["A"] * (T ** 4 - T0 ** 4)),
                "emitted_W": _r(kw["e"] * sig * kw["A"] * T ** 4)}
    if kind == "wien":
        return {"lambda_max_m": _r(2.897771955e-3 / kw["T"]),
                "formula": "λm·T = 2.898×10⁻³ m·K"}
    if kind == "newton_cooling":
        k, T0, Te, t = kw["k"], kw["T0"], kw["T_env"], kw["t"]
        return {"T_now": _r(Te + (T0 - Te) * math.exp(-k * t)),
                "time_constant_1/k_s": _r(1 / k)}
    raise ValueError("kind: calorimetry|latent|mixing|expansion|conduction|conduction_series|stefan|wien|newton_cooling")


def kinetic_theory(kind: str, **kw):
    kind = str(kind).lower()
    R, kB = 8.314, 1.380649e-23
    if kind == "speeds":
        T = kw["T"]
        if kw.get("molar_mass_g"):
            M = kw["molar_mass_g"] / 1000.0
            return {"v_rms_m/s": _r(math.sqrt(3 * R * T / M)),
                    "v_avg_m/s": _r(math.sqrt(8 * R * T / (math.pi * M))),
                    "v_mp_m/s": _r(math.sqrt(2 * R * T / M)),
                    "ratio": "v_mp : v_avg : v_rms = 1 : 1.128 : 1.224"}
        m = kw["m_kg"]
        return {"v_rms_m/s": _r(math.sqrt(3 * kB * T / m))}
    if kind == "pressure":
        return {"P_Pa": _r(kw["n"] * R * kw["T"] / kw["V"]),
                "KE_per_mol_J": _r(1.5 * R * kw["T"]),
                "KE_total_J": _r(1.5 * kw["n"] * R * kw["T"])}
    if kind == "mean_free_path":
        return {"lambda_m": _r(1 / (math.sqrt(2) * math.pi * kw["d"] ** 2 * kw["n_V"])),
                "formula": "λ = 1/(√2·π·d²·n)"}
    if kind == "dof_energy":
        f = kw["dof"]
        return {"gamma": _r(1 + 2 / f), "Cv_molar": _r(R / (1 + 2 / f) * 0 + R * f / 2),
                "Cp_molar": _r(R * f / 2 + R),
                "energy_per_mole_J": _r(0.5 * f * R * kw["T"]),
                "note": "mono f=3, diatomic f=5 (rt), poly f=6"}
    raise ValueError("kind: speeds|pressure|mean_free_path|dof_energy")


def thermo_process(kind: str, **kw):
    kind = str(kind).lower()
    R = 8.314
    if kind == "isothermal":
        n, T, V1, V2 = kw["n"], kw["T"], kw["V1"], kw["V2"]
        W = n * R * T * math.log(V2 / V1)
        return {"W_by_gas_J": _r(W), "Q_J": _r(W), "dU_J": 0.0,
                "note": "ΔU = 0 for isothermal ideal gas"}
    if kind == "adiabatic":
        P1, V1, V2, g = kw["P1"], kw["V1"], kw["V2"], kw["gamma"]
        P2 = P1 * (V1 / V2) ** g
        T1 = P1 * V1 / (kw.get("n", 1) * R) if kw.get("n") else None
        out = {"P2_Pa": _r(P2), "W_by_gas_J": _r((P1 * V1 - P2 * V2) / (g - 1)),
               "Q_J": 0.0}
        if T1:
            out["T1_K"] = _r(T1)
            out["T2_K"] = _r(T1 * (V1 / V2) ** (g - 1))
        return out
    if kind == "isobaric":
        n, T1, T2, P = kw["n"], kw["T1"], kw["T2"], kw["P"]
        dT = T2 - T1
        return {"W_by_gas_J": _r(n * R * dT), "Q_J": _r(n * 3.5 * R * dT), "dU_J": _r(n * 2.5 * R * dT),
                "note": "uses γ=1.4 (diatomic); pass n and both temps"}
    if kind == "isochoric":
        n, T1, T2 = kw["n"], kw["T1"], kw["T2"]
        dT = T2 - T1
        return {"W_by_gas_J": 0.0, "Q_J": _r(n * 1.5 * R * dT), "dU_J": _r(n * 1.5 * R * dT),
                "note": "uses Cv=1.5R (monoatomic)"}
    if kind == "carnot_eff":
        th, tc = kw["T_hot"], kw["T_cold"]
        return {"efficiency_%": _r(100 * (1 - tc / th)),
                "note": "η = 1 − Tc/Th (Kelvin!)"}
    if kind == "carnot_cop":
        th, tc = kw["T_hot"], kw["T_cold"]
        cop = tc / (th - tc)
        return {"COP_refrigerator": _r(cop), "COP_heat_pump": _r(1 + cop)}
    if kind == "engine_eff":
        return {"efficiency_%": _r(100 * kw["W"] / kw["Q_in"])}
    raise ValueError("kind: isothermal|adiabatic|isobaric|isochoric|carnot_eff|carnot_cop|engine_eff")


K = 8.9875517923e9
EP0 = 8.8541878128e-12
MU0 = 1.25663706212e-6


def electrostatics(kind: str, **kw):
    kind = str(kind).lower()
    if kind == "field_ring":
        Q, R, z = kw["Q"], kw["R"], kw["z"]
        E = K * Q * z / (R * R + z * z) ** 1.5
        return {"E_N/C": _r(E), "direction": "along axis", "max_at_z": _r(R / math.sqrt(2))}
    if kind == "field_sheet":
        return {"E_N/C": _r(kw["sigma"] / (2 * EP0)),
                "note": "infinite sheet: E = σ/2ε₀ (independent of distance)"}
    if kind == "shell":
        Q, R, r = kw["Q"], kw["R"], kw["r"]
        if r >= R:
            return {"E_N/C": _r(K * Q / r ** 2), "V_volt": _r(K * Q / r), "region": "outside"}
        return {"E_N/C": 0.0, "V_volt": _r(K * Q / R), "region": "inside"}
    if kind == "solid_sphere":
        Q, R, r = kw["Q"], kw["R"], kw["r"]
        if r >= R:
            return {"E_N/C": _r(K * Q / r ** 2), "V_volt": _r(K * Q / r), "region": "outside"}
        return {"E_N/C": _r(K * Q * r / R ** 3), "V_volt": _r(K * Q * (3 * R * R - r * r) / (2 * R ** 3)),
                "region": "inside"}
    if kind == "dipole_field":
        p, r, mode = kw["p"], kw["r"], kw.get("mode", "axial")
        f = 2 if mode == "axial" else 1
        return {"E_N/C": _r(K * f * p / r ** 3), "mode": mode,
                "note": "axial: 2kp/r³, equatorial: kp/r³ (antiparallel to p)"}
    if kind == "dipole_torque":
        p, E, th = kw["p"], kw["E"], math.radians(kw.get("theta_deg", 90))
        return {"torque_Nm": _r(p * E * math.sin(th)), "U_J": _r(-p * E * math.cos(th)),
                "max_torque_at": "90°", "stable_eq": "0° (p ∥ E)"}
    if kind == "pe_charges":
        pairs = kw["pairs"]  # [[q1, q2, r]...]
        U = sum(K * p[0] * p[1] / p[2] for p in pairs)
        return {"U_J": _r(U), "n_pairs": len(pairs),
                "note": "U = Σ k·qi·qj/rij over all pairs"}
    if kind == "gauss_flux":
        if kw.get("Q_enc") is not None:
            return {"flux_Nm2/C": _r(kw["Q_enc"] / EP0), "law": "Φ = q_enc/ε₀"}
        E, A, th = kw["E"], kw["A"], math.radians(kw.get("theta_deg", 0))
        return {"flux_Nm2/C": _r(E * A * math.cos(th))}
    if kind == "work_q":
        q, V1, V2 = kw["q"], kw["V1"], kw["V2"]
        return {"W_by_field_J": _r(-q * (V2 - V1)), "dU_J": _r(q * (V2 - V1)),
                "note": "W_ext = q(V₂ − V₁); W_field = −ΔU"}
    if kind == "dielectric_slab":
        A, d, t, Kd = kw["A"], kw["d"], kw["t"], kw["K"]
        C0 = EP0 * A / d
        C = EP0 * A / (d - t + t / Kd)
        return {"C0_farad": _r(C0), "C_with_slab_farad": _r(C), "ratio": _r(C / C0),
                "note": "slab thickness t, dielectric constant K, partially filled"}
    if kind == "energy_density":
        E = kw["E"]
        u = 0.5 * EP0 * E * E
        out = {"energy_density_J/m3": _r(u)}
        if kw.get("V"):
            out["total_energy_J"] = _r(u * kw["V"])
        return out
    raise ValueError("kind: field_ring|field_sheet|shell|solid_sphere|dipole_field|dipole_torque|pe_charges|gauss_flux|work_q|dielectric_slab|energy_density")


def capacitor_share(C1: float, C2: float, V1: float, V2: float):
    q1, q2 = C1 * V1, C2 * V2
    Vf = (q1 + q2) / (C1 + C2)
    Ui = 0.5 * C1 * V1 ** 2 + 0.5 * C2 * V2 ** 2
    Uf = 0.5 * (C1 + C2) * Vf ** 2
    return {"common_V": _r(Vf), "q1_final_C": _r(C1 * Vf), "q2_final_C": _r(C2 * Vf),
            "energy_initial_J": _r(Ui), "energy_final_J": _r(Uf), "energy_lost_J": _r(Ui - Uf),
            "note": "parallel connection of charged capacitors (like plates together)"}


def magnetism_extra(kind: str, **kw):
    kind = str(kind).lower()
    if kind == "wire_force":
        th = math.radians(kw.get("theta_deg", 90))
        return {"force_N": _r(kw["I"] * kw["L"] * kw["B"] * math.sin(th)),
                "direction": "F = IL×B (right-hand rule)"}
    if kind == "parallel_wires":
        I1, I2, d = kw["I1"], kw["I2"], kw["d"]
        f = MU0 * I1 * I2 / (2 * math.pi * d)
        return {"force_per_length_N/m": _r(f), "interaction": "attractive" if I1 * I2 > 0 else "repulsive"}
    if kind == "loop_torque":
        N, I, A, B, th = kw["N"], kw["I"], kw["A"], kw["B"], math.radians(kw.get("theta_deg", 90))
        m = N * I * A
        return {"magnetic_moment_Am2": _r(m), "torque_Nm": _r(m * B * math.sin(th)),
                "U_J": _r(-m * B * math.cos(th))}
    if kind == "loop_center":
        N, I, R = kw["N"], kw["I"], kw["R"]
        return {"B_T": _r(MU0 * N * I / (2 * R)), "formula": "B = μ₀NI/2R at centre"}
    if kind == "loop_axis":
        N, I, R, z = kw["N"], kw["I"], kw["R"], kw["z"]
        return {"B_T": _r(MU0 * N * I * R * R / (2 * (R * R + z * z) ** 1.5))}
    if kind == "helix":
        q, m, vp, vpar, B = kw["q"], kw["m"], kw["v_perp"], kw.get("v_parallel", 0), kw["B"]
        T = 2 * math.pi * m / (abs(q) * B)
        r = m * vp / (abs(q) * B)
        out = {"radius_m": _r(r), "period_s": _r(T), "frequency_Hz": _r(1 / T),
               "omega_rad/s": _r(abs(q) * B / m)}
        if vpar:
            out["pitch_m"] = _r(vpar * T)
        return out
    raise ValueError("kind: wire_force|parallel_wires|loop_torque|loop_center|loop_axis|helix")


def emi(kind: str, **kw):
    kind = str(kind).lower()
    if kind == "motional_emf":
        return {"emf_V": _r(kw["B"] * kw["L"] * kw["v"]),
                "note": "ε = BLv, rod ⊥ field moving ⊥ both"}
    if kind == "self_emf":
        return {"emf_V": _r(abs(kw["L"] * kw["dI_dt"])), "sign": "opposes change (Lenz)"}
    if kind == "solenoid_L":
        n, A, l = kw["n_per_m"], kw["A"], kw["l"]
        L = MU0 * n * n * A * l
        return {"L_henry": _r(L), "flux_per_amp_Wb": _r(L)}
    if kind == "mutual_emf":
        return {"emf_V": _r(abs(kw["M"] * kw["dI_dt"]))}
    if kind == "inductor_energy":
        return {"U_J": _r(0.5 * kw["L"] * kw["I"] ** 2),
                "energy_density_J/m3": _r(kw["B"] ** 2 / (2 * MU0)) if kw.get("B") else None}
    if kind == "lr_circuit":
        L, R, V0, t = kw["L"], kw["R"], kw["V0"], kw["t"]
        tau = L / R
        I0 = V0 / R
        mode = kw.get("mode", "growth")
        I = I0 * (1 - math.exp(-t / tau)) if mode == "growth" else I0 * math.exp(-t / tau)
        return {"tau_s": _r(tau), "I_now_A": _r(I), "I_max_A": _r(I0), "mode": mode,
                "I_formula": "I = I₀(1 − e^(−t/τ)) growth,  I₀e^(−t/τ) decay"}
    if kind == "lc_oscillation":
        L, C = kw["L"], kw["C"]
        f = 1 / (2 * math.pi * math.sqrt(L * C))
        return {"frequency_Hz": _r(f), "omega_rad/s": _r(1 / math.sqrt(L * C)),
                "period_s": _r(1 / f), "note": "energy oscillates L↔C like SHM"}
    if kind == "induced_charge":
        return {"charge_C": _r(abs(kw["dPhi"]) / kw["R"]),
                "note": "q = ΔΦ/R (total charge through circuit)"}
    raise ValueError("kind: motional_emf|self_emf|solenoid_L|mutual_emf|inductor_energy|lr_circuit|lc_oscillation|induced_charge")


def ac_circuits(kind: str, **kw):
    kind = str(kind).lower()
    if kind == "lcr":
        R, L, C, f, V = kw["R"], kw["L"], kw["C"], kw["f"], kw["V"]
        w = 2 * math.pi * f
        XL, XC = w * L, 1 / (w * C)
        Z = math.sqrt(R * R + (XL - XC) ** 2)
        phi = math.atan2(XL - XC, R)
        I = V / Z
        f0 = 1 / (2 * math.pi * math.sqrt(L * C))
        return {"XL_ohm": _r(XL), "XC_ohm": _r(XC), "Z_ohm": _r(Z),
                "phase_rad": _r(phi), "phase_deg": _r(math.degrees(phi)),
                "I_rms_A": _r(I), "V_R": _r(I * R), "V_L": _r(I * XL), "V_C": _r(I * XC),
                "resonant_freq_Hz": _r(f0), "Q_factor": _r(w0 := 2 * math.pi * f0 * L / R),
                "power_factor": _r(math.cos(phi)), "P_avg_W": _r(V * I * math.cos(phi)),
                "nature": "inductive" if XL > XC else ("capacitive" if XC > XL else "resonance")}
    if kind == "rms":
        if kw.get("V_peak"):
            return {"rms": _r(kw["V_peak"] / math.sqrt(2)), "note": "rms = peak/√2"}
        return {"peak": _r(kw["V_rms"] * math.sqrt(2))}
    if kind == "transformer":
        Np, Ns, Vp, eff = kw["Np"], kw["Ns"], kw["Vp"], kw.get("eff", 1.0)
        Vs = Vp * Ns / Np
        out = {"V_secondary": _r(Vs), "type": "step-up" if Vs > Vp else "step-down",
               "turn_ratio_Ns/Np": _r(Ns / Np)}
        if kw.get("Ip"):
            out["Is_A"] = _r(eff * Vp * kw["Ip"] / Vs)
        if kw.get("Is"):
            out["Ip_A"] = _r(Vs * kw["Is"] / (eff * Vp))
        return out
    raise ValueError("kind: lcr|rms|transformer")


def em_waves(kind: str, **kw):
    kind = str(kind).lower()
    c, mu0 = 2.99792458e8, 1.25663706212e-6
    eps0 = 8.8541878128e-12
    if kind == "relation":
        if kw.get("f"):
            return {"lambda_m": _r(c / kw["f"]), "note": "c = fλ, c = 3×10⁸ m/s"}
        return {"f_Hz": _r(c / kw["lambda_m"])}
    if kind == "intensity_E":
        E0 = kw["E0"]
        I = E0 * E0 / (2 * mu0 * c)
        out = {"intensity_W/m2": _r(I), "B0_T": _r(E0 / c)}
        if kw.get("A"):
            out["power_W"] = _r(I * kw["A"])
        return out
    if kind == "E_from_I":
        I = kw["I"]
        E0 = math.sqrt(2 * I / (c * eps0))
        return {"E0_V/m": _r(E0), "B0_T": _r(E0 / c)}
    if kind == "radiation_pressure":
        I = kw["I"]
        f = 2.0 if kw.get("surface", "absorbing") == "reflecting" else 1.0
        return {"pressure_Pa": _r(f * I / c), "momentum_flux_N/m2": _r(I / c),
                "surface": kw.get("surface", "absorbing")}
    raise ValueError("kind: relation|intensity_E|E_from_I|radiation_pressure")


def ray_optics2(kind: str, **kw):
    kind = str(kind).lower()
    if kind == "snell":
        n1, n2, t1 = kw["n1"], kw["n2"], math.radians(kw["theta1_deg"])
        s2 = n1 * math.sin(t1) / n2
        if s2 > 1:
            return {"result": "TOTAL INTERNAL REFLECTION", "critical_angle_deg":
                    round(math.degrees(math.asin(n2 / n1)), 4) if n1 > n2 else None}
        return {"theta2_deg": round(math.degrees(math.asin(s2)), 4)}
    if kind == "critical_angle":
        n1, n2 = kw["n1"], kw.get("n2", 1.0)
        if n1 <= n2:
            return {"error": "TIR requires n1 > n2 (dense → rare)"}
        return {"critical_angle_deg": round(math.degrees(math.asin(n2 / n1)), 4)}
    if kind == "prism_n":
        A, dm = math.radians(kw["A_deg"]), math.radians(kw["delta_min_deg"])
        n = math.sin((A + dm) / 2) / math.sin(A / 2)
        return {"n": round(n, 6), "condition": "minimum deviation, A < 2i_m etc."}
    if kind == "prism_deviation":
        A, n = kw["A_deg"], kw["n"]
        if A >= 2 * math.degrees(math.asin(min(1.0, 1.0 / n))):
            pass
        dm = 2 * math.asin(n * math.sin(math.radians(A) / 2)) - math.radians(A)
        return {"delta_min_deg": round(math.degrees(dm), 4)}
    if kind == "lens_combo":
        f1, f2, d = kw["f1"], kw["f2"], kw.get("d", 0.0)
        F = 1 / (1 / f1 + 1 / f2 - d / (f1 * f2))
        P = 1 / F
        return {"equivalent_f": _r(F), "power_D": _r(P),
                "note": "1/F = 1/f1 + 1/f2 − d/(f1f2); contact: d=0"}
    if kind == "magnifier":
        f, D = kw["f"], kw.get("D_cm", 25.0)
        return {"M_near_point": _r(1 + D / f), "M_relaxed": _r(D / f),
                "note": "image at near point (D) vs infinity (relaxed eye)"}
    if kind == "telescope":
        fo, fe = kw["f_obj"], kw["f_eye"]
        return {"M_relaxed": _r(-fo / fe), "tube_length": _r(fo + fe),
                "note": "normal adjustment; −ve → inverted image"}
    if kind == "microscope":
        fo, fe, L, D = kw["f_obj"], kw["f_eye"], kw.get("L_cm", kw.get("L", 6.0)), kw.get("D_cm", 25.0)
        return {"M_near_point": _r((L / fo) * (1 + D / fe)), "M_relaxed": _r(L * D / (fo * fe)),
                "tube_length_L": L}
    raise ValueError("kind: snell|critical_angle|prism_n|prism_deviation|lens_combo|magnifier|telescope|microscope")


def wave_optics2(kind: str, **kw):
    kind = str(kind).lower()
    if kind == "single_slit":
        a, lam = kw["a"], kw["lambda_m"]
        out = {"minima_condition": "a·sinθ = mλ (m = ±1, ±2, …)"}
        if kw.get("theta_deg") is not None:
            th = math.radians(kw["theta_deg"])
            ratio = a * math.sin(th) / lam
            out["m_at_angle"] = _r(ratio)
        if kw.get("D"):
            D = kw["D"]
            w = 2 * lam * D / a
            out["central_max_width_m"] = _r(w)
        if kw.get("m") is not None and kw.get("D"):
            out[f"y_min_m{kw['m']}"] = _r(kw["m"] * lam * kw["D"] / a)
        return out
    if kind == "brewster":
        n = kw.get("n_ratio", kw.get("n", 1.5))
        return {"brewster_angle_deg": round(math.degrees(math.atan(n)), 4),
                "reflected": "fully polarized ⊥ plane of incidence"}
    if kind == "malus":
        I0, th = kw["I0"], math.radians(kw["theta_deg"])
        return {"I_transmitted": _r(I0 * math.cos(th) ** 2)}
    if kind == "rayleigh":
        lam, D = kw["lambda_m"], kw["D"]
        th = 1.22 * lam / D
        return {"resolving_angle_rad": _r(th), "resolving_angle_deg": round(math.degrees(th), 8),
                "limit": "θ = 1.22λ/D"}
    if kind == "ydse_life":
        d, lam, D = kw["d"], kw["lambda_m"], kw["D"]
        return {"fringe_width_m": _r(lam * D / d)}
    raise ValueError("kind: single_slit|brewster|malus|rayleigh|ydse_life")


def string_sound(kind: str, **kw):
    kind = str(kind).lower()
    if kind == "string_speed":
        if kw.get("T") and kw.get("mu"):
            return {"v_m/s": _r(math.sqrt(kw["T"] / kw["mu"])), "formula": "v = √(T/µ)"}
        if kw.get("T") and kw.get("m") and kw.get("L"):
            mu = kw["m"] / kw["L"]
            return {"v_m/s": _r(math.sqrt(kw["T"] / mu)), "mu_kg/m": _r(mu)}
    if kind == "harmonics":
        v, L, mode = kw["v"], kw["L"], kw.get("mode", "both_fixed")
        f1 = v / (2 * L) if mode == "both_fixed" else v / (4 * L)
        out = {"fundamental_f1_Hz": _r(f1)}
        if mode == "both_fixed":
            out["harmonics"] = "f_n = n·f1 (all harmonics)"
            out["f2"] = _r(2 * f1)
        else:
            out["harmonics"] = "f_n = (2n−1)·f1 (odd only — closed pipe)"
            out["f3"] = _r(3 * f1)
        return out
    if kind == "beats":
        f1, f2 = kw["f1"], kw["f2"]
        return {"beat_frequency_Hz": _r(abs(f1 - f2)), "beat_period_s": _r(1 / abs(f1 - f2))}
    if kind == "decibel":
        I = kw["I"]
        return {"level_dB": _r(10 * math.log10(I / 1e-12)),
                "reference": "I₀ = 10⁻¹² W/m² (threshold)"}
    if kind == "intensity_from_db":
        return {"I_W/m2": _r(1e-12 * 10 ** (kw["dB"] / 10))}
    if kind == "organ_pipe":
        v, L, oc = kw["v"], kw["L"], kw.get("type", "closed")
        f1 = v / (4 * L) if oc == "closed" else v / (2 * L)
        out = {"fundamental_Hz": _r(f1), "type": oc}
        out["harmonics"] = "odd only (1,3,5…)" if oc == "closed" else "all harmonics"
        return out
    if kind == "wave_speed_tension":
        return {"v_m/s": _r(math.sqrt(kw["T"] / kw["mu"]))}
    raise ValueError("kind: string_speed|harmonics|beats|decibel|intensity_from_db|organ_pipe")


def rotation_extra(kind: str, **kw):
    kind = str(kind).lower()
    K_CONST = {"ring": 1.0, "hollow_cylinder": 1.0, "disc": 0.5, "solid_cylinder": 0.5,
               "solid_sphere": 0.4, "hollow_sphere": 2 / 3, "rod_center": 1 / 12, "rod_end": 1 / 3}
    if kind == "rolling_energy":
        m, v, body = kw["m"], kw["v"], kw.get("body", "solid_sphere")
        kk = K_CONST[body]
        R = kw.get("R", 1.0)
        w = v / R if R else 0
        KE = 0.5 * m * v * v * (1 + kk)
        return {"KE_total_J": _r(KE), "KE_trans_J": _r(0.5 * m * v * v),
                "KE_rot_J": _r(0.5 * kk * m * v * v), "k": kk, "body": body,
                "fraction_rotational": _r(kk / (1 + kk))}
    if kind == "roll_incline":
        m, th, body = kw["m"], kw["theta_deg"], kw.get("body", "solid_sphere")
        kk = K_CONST[body]
        a = _G * math.sin(math.radians(th)) / (1 + kk)
        N = m * _G * math.cos(math.radians(th))
        f = kk / (1 + kk) * m * _G * math.sin(math.radians(th))
        mu_min = (kk * math.tan(math.radians(th))) / (1 + kk)
        return {"acceleration_m/s2": _r(a), "friction_N": _r(f),
                "min_mu_static": _r(mu_min), "body": kk,
                "note": "a = g·sinθ/(1+k);  µ_min = k·tanθ/(1+k)"}
    if kind == "parallel_axis":
        Icm, m, d = kw["I_cm"], kw["m"], kw["d"]
        return {"I_new": _r(Icm + m * d * d), "theorem": "I = I_cm + Md²"}
    if kind == "ang_mom_conservation":
        I1, w1, I2 = kw["I1"], kw["omega1"], kw["I2"]
        w2 = I1 * w1 / I2
        return {"omega2_rad/s": _r(w2), "KE1_J": _r(0.5 * I1 * w1 ** 2), "KE2_J": _r(0.5 * I2 * w2 ** 2),
                "note": "L conserved; KE changes (work done by internal forces)"}
    raise ValueError("kind: rolling_energy|roll_incline|parallel_axis|ang_mom_conservation")


def shm_extra(kind: str, **kw):
    kind = str(kind).lower()
    if kind == "pendulum":
        L, g = kw["L"], kw.get("g", _G)
        T = 2 * math.pi * math.sqrt(L / g)
        return {"period_s": _r(T), "frequency_Hz": _r(1 / T), "formula": "T = 2π√(L/g)"}
    if kind == "physical_pendulum":
        I, m, d = kw["I"], kw["m"], kw["d"]
        T = 2 * math.pi * math.sqrt(I / (m * _G * d))
        return {"period_s": _r(T), "formula": "T = 2π√(I/mgd), d = pivot→CM"}
    if kind == "springs_series":
        k1, k2 = kw["k1"], kw["k2"]
        keq = 1 / (1 / k1 + 1 / k2)
        return {"k_eq": _r(keq), "note": "series: softer spring dominates"}
    if kind == "springs_parallel":
        return {"k_eq": _r(kw["k1"] + kw["k2"])}
    if kind == "energy_partition":
        m, A, w, x = kw["m"], kw["A"], kw["omega"], kw["x"]
        KE = 0.5 * m * w * w * (A * A - x * x)
        PE = 0.5 * m * w * w * x * x
        return {"KE_J": _r(KE), "PE_J": _r(PE), "E_total_J": _r(0.5 * m * w * w * A * A),
                "v_at_x": _r(w * math.sqrt(A * A - x * x))}
    raise ValueError("kind: pendulum|physical_pendulum|springs_series|springs_parallel|energy_partition")


def modern_extra(kind: str, **kw):
    kind = str(kind).lower()
    mp_u, mn_u = 1.007276, 1.008665
    if kind == "binding_energy":
        Z, A, mN = kw["Z"], kw["A"], kw["m_nucleus_u"]
        dm = Z * mp_u + (A - Z) * mn_u - mN
        return {"mass_defect_u": round(dm, 6),
                "BE_MeV": round(dm * 931.5, 4),
                "BE_per_nucleon_MeV": round(dm * 931.5 / A, 4),
                "note": "uses mp = 1.007276 u, mn = 1.008665 u"}
    if kind == "decay":
        N0 = kw["N0"]
        t_half = kw.get("half_life")
        t = kw.get("t")
        out = {}
        if t_half and t is not None:
            N = N0 * 2 ** (-t / t_half)
            lam = math.log(2) / t_half
            out.update({"N_now": _r(N), "decayed": _r(N0 - N), "fraction_left": _r(N / N0),
                        "activity_Bq": _r(lam * N), "lambda_1/s": _r(lam),
                        "mean_life_s": _r(1 / lam)})
        elif t_half and kw.get("fraction") is not None:
            t_needed = t_half * math.log(1 / kw["fraction"], 2) if False else t_half * math.log2(1 / kw["fraction"])
            out.update({"time_s": _r(t_needed), "half_lives": _r(math.log2(1 / kw["fraction"]))})
        else:
            return {"error": "provide N0 with (half_life + t) or (half_life + fraction)"}
        return out
    if kind == "xray_min":
        V = kw["V_volt"]
        return {"lambda_min_nm": _r(1239.84 / V / 1), "note": "λmin(nm) = 1240/V(volts) — Duane–Hunt"}
    if kind == "moseley":
        Z = kw["Z"]
        b = kw.get("b", 1)
        R = 1.0973731568160e7
        tr = kw.get("transition", "K_alpha")
        n1, n2 = (1, 2) if tr == "K_alpha" else (1, 3)
        nu = R * c_light * (Z - b) ** 2 * (1 / n1 ** 2 - 1 / n2 ** 2)
        return {"frequency_Hz": _r(nu), "lambda_nm": _r(c_light / nu * 1e9),
                "transition": tr, "formula": "√ν = a(Z−b)"}
    if kind == "mass_energy":
        m = kw["m_kg"] if kw.get("m_kg") else kw.get("m_u", 0) * 1.66053906660e-27
        E = m * c_light ** 2
        return {"E_J": _r(E), "E_MeV": _r(E / 1.602176634e-19 / 1e6)}
    if kind == "bohr_transition":
        Z, n1, n2 = kw.get("Z", 1), kw["n1"], kw["n2"]
        R = 1.0973731568160e7
        inv = R * Z * Z * (1 / min(n1, n2) ** 2 - 1 / max(n1, n2) ** 2)
        return {"lambda_m": _r(1 / inv), "lambda_nm": _r(1e9 / inv),
                "energy_eV": _r(13.6 * Z * Z * (1 / min(n1, n2) ** 2 - 1 / max(n1, n2) ** 2)),
                "series": {("1", "2"): "Lyman", ("1", "3"): "Lyman", ("2", "3"): "Balmer",
                           ("2", "4"): "Balmer", ("3", "4"): "Paschen"}.get((str(min(n1, n2)), str(max(n1, n2))), "")}
    raise ValueError("kind: binding_energy|decay|xray_min|moseley|mass_energy|bohr_transition")


c_light = 2.99792458e8


def gravitation_extra(kind: str, **kw):
    kind = str(kind).lower()
    G = 6.674e-11
    if kind == "orbit_energies":
        M, m, r = kw["M"], kw["m"], kw["r"]
        KE = G * M * m / (2 * r)
        PE = -G * M * m / r
        return {"KE_J": _r(KE), "PE_J": _r(PE), "E_total_J": _r(-KE),
                "v_orbital_m/s": _r(math.sqrt(G * M / r)),
                "note": "E = −KE = PE/2 (bound orbit)"}
    if kind == "g_variation":
        R = kw["R"]
        if kw.get("h") is not None:
            h = kw["h"]
            return {"g_at_height": _r(_G * (R / (R + h)) ** 2), "depth_or_height": h,
                    "formula": "g' = g·R²/(R+h)²"}
        d = kw.get("d", 0)
        return {"g_at_depth": _r(_G * (1 - d / R)), "formula": "g' = g(1 − d/R)"}
    if kind == "kepler3":
        r, M = kw["r"], kw["M"]
        T = 2 * math.pi * math.sqrt(r ** 3 / (G * M))
        return {"period_s": _r(T), "period_days": _r(T / 86400),
                "formula": "T² = 4π²r³/GM"}
    if kind == "escape_energy":
        M, m, R = kw["M"], kw["m"], kw["R"]
        ve = math.sqrt(2 * G * M / R)
        return {"escape_velocity_m/s": _r(ve), "escape_energy_J": _r(0.5 * m * ve * ve)}
    raise ValueError("kind: orbit_energies|g_variation|kepler3|escape_energy")


def error_propagation(formula: str, values: dict):
    """values = {name: [measured_value, absolute_error]} → f ± δf."""
    syms = {k: sp.Symbol(k) for k in values}
    f = sp.sympify(str(formula), locals=syms)
    fval = float(f.subs({s: values[k][0] for k, s in syms.items()}))
    rel = 0.0
    contribs = {}
    for k, s in syms.items():
        val, err = values[k][0], values[k][1]
        df = sp.diff(f, s).subs({sv: values[kk][0] for kk, sv in syms.items()})
        c = abs(float(df)) * err
        contribs[k] = c
        rel += c * c
    df_tot = math.sqrt(rel)
    return {"value": _r(fval), "abs_error": _r(df_tot),
            "result": f"{_r(fval)} ± {_r(df_tot)}",
            "rel_error_%": _r(100 * df_tot / abs(fval)) if fval else None,
            "contributions": {k: _r(v) for k, v in contribs.items()},
            "note": "quadrature combination of independent errors"}
