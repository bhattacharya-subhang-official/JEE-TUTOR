"""Symbolic / numeric MATH engine for JEE-Advanced (algebra, calculus, matrices, vectors,
complex numbers, sequences, binomial, probability & statistics, coordinate geometry,
conics, 3D geometry, ODEs)."""
import math
import re
from collections import Counter

import sympy as sp
from sympy.parsing.sympy_parser import (parse_expr, standard_transformations,
                                        implicit_multiplication_application, convert_xor)
from sympy.physics.units import convert_to
import sympy.physics.units as u
from sympy.calculus.util import continuous_domain, function_range, singularities
from sympy import geometry as ge


def _s(expr):
    try:
        return sp.sympify(str(expr), rational=True)
    except Exception as e:
        raise ValueError(f"Cannot parse expression '{expr}': {e}")


def _fmt(expr) -> str:
    return str(expr)


def _out(expr):
    e = sp.sympify(expr)
    res = {"result": _fmt(e)}
    try:
        res["latex"] = sp.latex(e)
    except Exception:
        pass
    if e.free_symbols:
        res["note"] = "Symbolic result — substitute numeric values for a number."
    else:
        try:
            res["numeric"] = str(sp.N(e, 8))
        except Exception:
            pass
    return res


# ---------------------------------------------------------------- algebra
def simplify_expr(expr: str, action: str = "simplify"):
    f = {
        "simplify": sp.simplify, "expand": sp.expand, "factor": sp.factor,
        "trigsimp": sp.trigsimp, "apart": sp.apart, "together": sp.together,
        "radsimp": sp.radsimp, "nsimplify": lambda e: sp.nsimplify(e),
    }.get(action)
    if f is None:
        raise ValueError(f"Unknown action '{action}'. Use: simplify/expand/factor/trigsimp/apart/together/radsimp")
    return _out(f(_s(expr)))


def solve_equation(equations: list, variables: list):
    eqs = []
    for e in equations:
        e = str(e)
        if "=" in e and "==" not in e:
            lhs, rhs = e.split("=", 1)
            eqs.append(sp.Eq(_s(lhs), _s(rhs)))
        else:
            eqs.append(_s(e))
    syms = [sp.Symbol(str(v)) for v in variables]
    sols = sp.solve(eqs, syms, dict=True)
    if not sols:
        return {"solutions": [], "note": "No closed-form solution found — try nsolve_system for numeric."}
    out = []
    for sol in sols[:16]:
        d = {}
        for sym, val in sol.items():
            item = {"result": _fmt(val)}
            try:
                item["latex"] = sp.latex(val)
                if not val.free_symbols:
                    item["numeric"] = str(sp.N(val, 8))
            except Exception:
                pass
            d[str(sym)] = item
        out.append(d)
    return {"n_solutions": len(sols), "solutions": out}


def polynomial_roots(expr: str, var: str = "x", numeric: bool = False):
    e = _s(expr)
    x = sp.Symbol(str(var))
    if numeric:
        roots = [complex(r) for r in sp.nroots(e, n=8, maxsteps=200)]
        return {"roots": [{"re": round(r.real, 8), "im": round(r.imag, 8)} for r in roots]}
    r = sp.roots(e, x)
    if not r:
        roots = sp.solve(sp.Eq(e, 0), x)
        return {"roots": [_fmt(v) for v in roots]}
    return {"roots": [{"root": _fmt(k), "multiplicity": v} for k, v in r.items()]}


def nsolve_system(equations: list, variables: list, guesses: list):
    eqs = []
    for e in equations:
        e = str(e)
        if "=" in e and "==" not in e:
            lhs, rhs = e.split("=", 1)
            eqs.append(_s(lhs) - _s(rhs))
        else:
            eqs.append(_s(e))
    syms = [sp.Symbol(str(v)) for v in variables]
    g = [float(x) for x in guesses]
    sol = sp.nsolve(sp.Matrix(eqs), syms, g, tol=1e-12, maxsteps=60)
    return {str(s): str(sp.N(v, 10)) for s, v in zip(syms, sol)}


# ---------------------------------------------------------------- calculus
def calculus(action: str, expr: str, var: str = "x", order: int = 1,
             lower=None, upper=None, point=None, direction: str = "+", series_order: int = 6):
    e = _s(expr)
    x = sp.Symbol(str(var))
    if action == "diff":
        return _out(sp.diff(e, x, int(order)))
    if action == "integrate":
        if lower is not None and upper is not None:
            val = sp.integrate(e, (x, _s(lower), _s(upper)))
            res = _out(val)
            try:
                res["numeric"] = str(sp.N(val, 10))
            except Exception:
                pass
            return res
        return _out(sp.integrate(e, x))
    if action == "limit":
        p = sp.oo if str(point) in ("oo", "inf", "infinity") else _s(point)
        if direction == "both":
            try:
                lp = sp.limit(e, x, p, "+")
                lm = sp.limit(e, x, p, "-")
                if sp.simplify(lp - lm) == 0:
                    return {"result": _fmt(lp), "two_sided": True}
                return {"result": "DNE (two-sided limit does not exist)",
                        "from_plus": _fmt(lp), "from_minus": _fmt(lm)}
            except Exception as ex:
                return {"error": f"limit failed: {ex}"}
        d = "+" if direction in ("+", "right") else "-"
        return _out(sp.limit(e, x, p, d))
    if action == "series":
        p = 0 if point is None else _s(point)
        return _out(sp.series(e, x, p, int(series_order)).removeO())
    raise ValueError("action must be diff / integrate / limit / series")


# ---------------------------------------------------------------- matrices & vectors
def matrix_op(matrix: list, op: str, matrix2: list = None, scalar=None):
    M = sp.Matrix(matrix)
    if op == "determinant":
        return {"determinant": _fmt(M.det())}
    if op == "inverse":
        return {"inverse": _fmt(M.inv())}
    if op == "transpose":
        return {"transpose": _fmt(M.T)}
    if op == "rank":
        return {"rank": int(M.rank())}
    if op == "trace":
        return {"trace": _fmt(M.trace())}
    if op == "eigenvalues":
        ev = M.eigenvals()
        return {"eigenvalues": [{"value": _fmt(k), "multiplicity": v} for k, v in ev.items()]}
    if op == "eigenvectors":
        ev = M.eigenvects()
        return {"eigen": [{"value": _fmt(val), "multiplicity": m,
                           "vectors": [_fmt(vec) for vec in vecs]} for val, m, vecs in ev]}
    if op == "charpoly":
        lam = sp.Symbol("lambda")
        return {"charpoly": _fmt(M.charpoly(lam).as_expr())}
    if op == "multiply" and matrix2 is not None:
        return {"product": _fmt(M * sp.Matrix(matrix2))}
    if op == "add" and matrix2 is not None:
        return {"sum": _fmt(M + sp.Matrix(matrix2))}
    if op == "power" and scalar is not None:
        return {"power": _fmt(M ** int(scalar))}
    if op == "adjoint":
        return {"adjoint": _fmt(M.adjoint())}
    raise ValueError(f"Unknown matrix op '{op}'")


def vector_op(a: list, op: str, b: list = None):
    A = sp.Matrix([_s(x) for x in a])
    if op == "magnitude":
        return {"magnitude": _fmt(sp.sqrt(A.dot(A)))}
    if op in ("dot", "cross", "angle", "projection", "area_parallelogram") and b is not None:
        B = sp.Matrix([_s(x) for x in b])
        if op == "dot":
            return {"dot": _fmt(A.dot(B))}
        if op == "cross":
            return {"cross": _fmt(A.cross(B)), "magnitude": _fmt(A.cross(B).norm())}
        if op == "angle":
            c = sp.acos(A.dot(B) / (A.norm() * B.norm()))
            return {"angle_rad": _fmt(c), "angle_deg": _fmt(sp.deg(c))}
        if op == "projection":
            return {"projection_of_a_on_b": _fmt((A.dot(B) / B.dot(B)) * B)}
        if op == "area_parallelogram":
            return {"area": _fmt(A.cross(B).norm())}
    if op == "unit":
        return {"unit_vector": _fmt(A / A.norm())}
    raise ValueError(f"Unknown vector op '{op}'")


# ---------------------------------------------------------------- units & constants
_UNIT_NS = {n: getattr(u, n) for n in dir(u) if not n.startswith("_")}


def units_convert(value: float, from_unit: str, to_unit: str):
    try:
        q = sp.Float(str(value)) * sp.sympify(from_unit, locals=_UNIT_NS)
        target = sp.sympify(to_unit, locals=_UNIT_NS)
        res = convert_to(q, target)
        return {"converted": _fmt(res), "numeric": str(sp.N(res / target, 10)), "unit": str(target)}
    except Exception as e:
        raise ValueError(f"Unit conversion failed: {e}. Use sympy unit names (meter, second, kilogram, newton, joule, tesla, ...).")


_CONSTANTS = {
    "g": {"value": 9.80665, "unit": "m/s^2", "name": "standard gravity"},
    "G": {"value": 6.67430e-11, "unit": "N·m²/kg²", "name": "gravitational constant"},
    "c": {"value": 2.99792458e8, "unit": "m/s", "name": "speed of light"},
    "h": {"value": 6.62607015e-34, "unit": "J·s", "name": "Planck constant"},
    "hbar": {"value": 1.054571817e-34, "unit": "J·s", "name": "reduced Planck"},
    "e": {"value": 1.602176634e-19, "unit": "C", "name": "elementary charge"},
    "me": {"value": 9.1093837015e-31, "unit": "kg", "name": "electron mass"},
    "mp": {"value": 1.67262192369e-27, "unit": "kg", "name": "proton mass"},
    "mn": {"value": 1.67492749804e-27, "unit": "kg", "name": "neutron mass"},
    "amu": {"value": 1.66053906660e-27, "unit": "kg", "name": "atomic mass unit"},
    "NA": {"value": 6.02214076e23, "unit": "1/mol", "name": "Avogadro number"},
    "kB": {"value": 1.380649e-23, "unit": "J/K", "name": "Boltzmann constant"},
    "R": {"value": 8.314462618, "unit": "J/(mol·K)", "name": "universal gas constant"},
    "F": {"value": 96485.33212, "unit": "C/mol", "name": "Faraday constant"},
    "epsilon0": {"value": 8.8541878128e-12, "unit": "F/m", "name": "vacuum permittivity"},
    "mu0": {"value": 1.25663706212e-6, "unit": "T·m/A", "name": "vacuum permeability"},
    "k_coulomb": {"value": 8.9875517923e9, "unit": "N·m²/C²", "name": "Coulomb constant 1/4πε₀"},
    "atm": {"value": 101325, "unit": "Pa", "name": "standard atmosphere"},
    "eV": {"value": 1.602176634e-19, "unit": "J", "name": "electron-volt in joules"},
    "Rydberg": {"value": 1.0973731568160e7, "unit": "1/m", "name": "Rydberg constant"},
    "Bohr": {"value": 5.29177210903e-11, "unit": "m", "name": "Bohr radius"},
    "sigma": {"value": 5.670374419e-8, "unit": "W/(m²·K⁴)", "name": "Stefan-Boltzmann"},
    "wien": {"value": 2.897771955e-3, "unit": "m·K", "name": "Wien constant"},
}


def physical_constant(name: str):
    key = name.strip().strip("_").lower()
    for k, v in _CONSTANTS.items():
        if k.strip().lower() == key:
            return {"symbol": k.strip(), **v}
    raise ValueError(f"Unknown constant '{name}'. Available: {', '.join(sorted(k.strip() for k in _CONSTANTS))}")


# ════════════════════════════════════════════════════════════ COMPLEX NUMBERS
_TRNS = standard_transformations + (implicit_multiplication_application, convert_xor)


def _loose(s: str):
    """Parse '2x+3y=5' style loose math (implicit multiplication, ^ as power)."""
    return parse_expr(str(s).replace("^", "**"), transformations=_TRNS)


def _pc(s: str):
    """Parse a complex literal like '3+4i', '2i', '1-I', '5'."""
    s = str(s).strip().replace(" ", "").replace("j", "i").replace("i", "I")
    s = re.sub(r"(\d)I", r"\1*I", s)
    return sp.sympify(s)


def _cx_out(z):
    z = sp.simplify(z)
    d = {"result": _fmt(z)}
    try:
        d["re"], d["im"] = _fmt(sp.re(z)), _fmt(sp.im(z))
    except Exception:
        pass
    return d


def complex_op(z1: str, op: str, z2: str = None, n: int = None):
    z = _pc(z1)
    if op == "add" and z2 is not None:
        return _cx_out(z + _pc(z2))
    if op == "subtract" and z2 is not None:
        return _cx_out(z - _pc(z2))
    if op == "multiply" and z2 is not None:
        return _cx_out(z * _pc(z2))
    if op == "divide" and z2 is not None:
        return _cx_out(z / _pc(z2))
    if op == "modulus":
        return {"modulus": _fmt(sp.Abs(z))}
    if op == "argument":
        th = sp.arg(z)
        return {"argument_rad": _fmt(th), "argument_deg": _fmt(sp.deg(sp.simplify(th)))}
    if op == "conjugate":
        return _cx_out(sp.conjugate(z))
    if op == "reciprocal":
        return _cx_out(1 / z)
    if op == "polar":
        r, th = sp.Abs(z), sp.arg(z)
        return {"modulus": _fmt(r), "argument_rad": _fmt(th), "argument_deg": _fmt(sp.deg(sp.simplify(th))),
                "polar_form": f"{_fmt(r)}·(cos θ + i sin θ), θ = {_fmt(th)} rad"}
    if op == "power":
        e = int(n if n is not None else float(z2))
        return _cx_out(sp.expand(z ** e))
    if op == "roots":
        nn = int(n or 2)
        r, th = float(sp.Abs(z)), float(sp.arg(z))
        rr = r ** (1.0 / nn)
        roots = [{"k": k, "re": round(rr * math.cos((th + 2 * math.pi * k) / nn), 6),
                  "im": round(rr * math.sin((th + 2 * math.pi * k) / nn), 6)} for k in range(nn)]
        return {"n": nn, "modulus_of_roots": round(rr, 6), "roots": roots,
                "note": "Roots are equally spaced on a circle of radius r^(1/n), 2π/n apart."}
    raise ValueError("op: add|subtract|multiply|divide|modulus|argument|conjugate|reciprocal|polar|power|roots")


# ════════════════════════════════════════════════════════════ SEQUENCES & SERIES
def _r(v):
    try:
        f = float(v)
        return round(f, 8)
    except Exception:
        return v


def sequence_series(kind: str, a: float = None, d: float = None, n: int = None,
                    last: float = None, numbers: list = None):
    kind = str(kind).lower()
    if kind == "ap":
        if a is None or n is None:
            raise ValueError("ap needs a and n (plus d, or last)")
        dd = d if d is not None else ((last - a) / (n - 1) if last is not None and n > 1 else None)
        if dd is None:
            raise ValueError("ap needs d or last term")
        term = a + (n - 1) * dd
        return {"d": _r(dd), "nth_term": _r(term), "sum_n": _r(n * (a + term) / 2),
                "formulas": "aₙ = a + (n−1)d,  Sₙ = n/2·(2a + (n−1)d) = n/2·(a + l)"}
    if kind == "gp":
        if a is None or n is None or d is None:
            raise ValueError("gp needs a, r (as d) and n")
        r = d
        term = a * r ** (n - 1)
        out = {"r": _r(r), "nth_term": _r(term),
               "sum_n": _r(a * (r ** n - 1) / (r - 1)) if r != 1 else _r(a * n)}
        if abs(r) < 1:
            out["sum_infinite"] = _r(a / (1 - r))
        out["formulas"] = "aₙ = a·rⁿ⁻¹,  Sₙ = a(rⁿ−1)/(r−1),  S∞ = a/(1−r) for |r|<1"
        return out
    if kind == "hp":
        if a is None or d is None or n is None:
            raise ValueError("hp needs a, d (step of reciprocals) and n")
        term = 1 / (1 / a + (n - 1) * d)
        return {"nth_term": _r(term), "note": "d = common difference of the reciprocal AP"}
    if kind == "sum_n":
        return {"sum": _r(n * (n + 1) / 2), "formula": "Σn = n(n+1)/2"}
    if kind == "sum_n2":
        return {"sum": _r(n * (n + 1) * (2 * n + 1) / 6), "formula": "Σn² = n(n+1)(2n+1)/6"}
    if kind == "sum_n3":
        return {"sum": _r((n * (n + 1) / 2) ** 2), "formula": "Σn³ = [n(n+1)/2]²"}
    if kind == "am_gm_hm":
        if not numbers:
            raise ValueError("numbers list required")
        nums = [float(x) for x in numbers]
        am = sum(nums) / len(nums)
        gm = math.prod(nums) ** (1 / len(nums))
        hm = len(nums) / sum(1 / x for x in nums)
        return {"AM": round(am, 8), "GM": round(gm, 8), "HM": round(hm, 8),
                "relation": "AM ≥ GM ≥ HM"}
    raise ValueError("kind: ap | gp | hp | sum_n | sum_n2 | sum_n3 | am_gm_hm")


# ════════════════════════════════════════════════════════════ BINOMIAL THEOREM
def binomial_theorem(a: str = "x", b: str = "1", power: int = 5, term_r: int = None, coeff_of: str = None):
    A, B = _s(a), _s(b)
    n = int(power)
    out = {"expansion": _fmt(sp.expand((A + B) ** n)), "n_terms": n + 1,
           "general_term": f"T_(r+1) = C(n,r)·({_fmt(A)})^(n−r)·({_fmt(B)})^r"}
    m = n + 1
    out["middle_term_1indexed"] = [m // 2, m // 2 + 1] if m % 2 == 0 else [m // 2 + 1]
    if term_r is not None:
        r = int(term_r)
        if not 0 <= r <= n:
            raise ValueError("r must be 0..n")
        C = sp.binomial(n, r)
        term = sp.expand(C * (A ** (n - r)) * (B ** r))
        out[f"T{r + 1}"] = _fmt(term)
        out["binomial_coefficient"] = _fmt(C)
    if coeff_of is not None:
        target = sp.expand(_s(coeff_of))
        d = sp.expand((A + B) ** n).as_coefficients_dict()
        val = None
        for k, v in d.items():
            if sp.simplify(k - target) == 0:
                val = v
                break
        out[f"coeff_of_{coeff_of}"] = _fmt(val) if val is not None else 0
    return out


# ════════════════════════════════════════════════════════════ COMBINATORICS / PROBABILITY / STATS
def combinatorics(n: int, r: int = None, kind: str = "nCr"):
    n, kind = int(n), str(kind).lower()
    if kind in ("ncr", "combination"):
        return {"nCr": int(sp.binomial(n, int(r)))}
    if kind in ("npr", "permutation"):
        return {"nPr": int(sp.factorial(n) // sp.factorial(n - int(r)))}
    if kind == "factorial":
        return {"factorial": int(sp.factorial(n))}
    if kind == "power_set":
        return {"subsets": 2 ** n}
    if kind == "arrange_repetition":
        return {"arrangements": n ** int(r)}
    raise ValueError("kind: nCr | nPr | factorial | power_set | arrange_repetition")


def binomial_probability(n: int, p: float, k: int, mode: str = "exact"):
    n, k, mode = int(n), int(k), str(mode).lower()
    q = 1 - p

    def pmf(i):
        return float(sp.binomial(n, i)) * (p ** i) * (q ** (n - i))
    if mode == "exact":
        val = pmf(k)
    elif mode == "at_least":
        val = sum(pmf(i) for i in range(k, n + 1))
    elif mode == "at_most":
        val = sum(pmf(i) for i in range(0, k + 1))
    else:
        raise ValueError("mode: exact | at_least | at_most")
    return {"probability": round(val, 8), "mean_np": n * p, "variance_npq": n * p * q}


def statistics_calc(numbers: list):
    nums = sorted(float(x) for x in numbers)
    n = len(nums)
    mean = sum(nums) / n
    med = nums[n // 2] if n % 2 else (nums[n // 2 - 1] + nums[n // 2]) / 2
    cnt = Counter(nums)
    mx = max(cnt.values())
    mode = [k for k, v in cnt.items() if v == mx] if mx > 1 else []
    var_p = sum((x - mean) ** 2 for x in nums) / n
    var_s = sum((x - mean) ** 2 for x in nums) / (n - 1) if n > 1 else 0.0

    def qtl(p):
        idx = p * (n - 1)
        lo = math.floor(idx)
        hi = math.ceil(idx)
        return nums[lo] + (nums[hi] - nums[lo]) * (idx - lo)
    return {"n": n, "mean": round(mean, 8), "median": round(med, 8), "mode": mode,
            "variance_population": round(var_p, 8), "variance_sample": round(var_s, 8),
            "std_population": round(math.sqrt(var_p), 8), "std_sample": round(math.sqrt(var_s), 8),
            "min": nums[0], "max": nums[-1], "range": nums[-1] - nums[0],
            "Q1": round(qtl(0.25), 8), "Q3": round(qtl(0.75), 8),
            "IQR": round(qtl(0.75) - qtl(0.25), 8)}


def normal_probability(mu: float, sigma: float, x1: float, x2: float = None, tail: str = "below"):
    def cdf(x):
        return 0.5 * (1 + math.erf((x - mu) / (sigma * math.sqrt(2))))
    tail = str(tail).lower()
    if tail == "below":
        p = cdf(x1)
    elif tail == "above":
        p = 1 - cdf(x1)
    elif tail == "between":
        if x2 is None:
            raise ValueError("between needs x2")
        p = abs(cdf(max(x1, x2)) - cdf(min(x1, x2)))
    else:
        raise ValueError("tail: below | above | between")
    return {"probability": round(p, 8), "z_note": "Φ(z) computed via erf; standard normal"}


# ════════════════════════════════════════════════════════════ QUADRATIC / DOMAIN / ODE
def quadratic_analysis(a: float, b: float, c: float):
    A, B, C = _s(a), _s(b), _s(c)
    x = sp.Symbol("x")
    D = sp.simplify(B ** 2 - 4 * A * C)
    r1 = sp.simplify((-B + sp.sqrt(D)) / (2 * A))
    r2 = sp.simplify((-B - sp.sqrt(D)) / (2 * A))
    nature = "real & distinct" if D > 0 else ("real & equal" if D == 0 else "complex conjugates")
    out = {"D": _fmt(D), "roots": [_fmt(r1), _fmt(r2)],
           "numeric_roots": [round(complex(sp.N(r1)).real, 8) + round(complex(sp.N(r1)).imag, 8) * 1j,
                             round(complex(sp.N(r2)).real, 8) + round(complex(sp.N(r2)).imag, 8) * 1j],
           "nature": nature, "sum_of_roots": _fmt(sp.simplify(-B / A)),
           "product_of_roots": _fmt(sp.simplify(C / A)),
           "vertex": [_fmt(sp.simplify(-B / (2 * A))), _fmt(sp.simplify(-D / (4 * A)))],
           "axis": f"x = {_fmt(sp.simplify(-B / (2 * A)))}",
           "opens": "upward (min value at vertex)" if A > 0 else "downward (max value at vertex)"}
    if D >= 0:
        out["factorized_form"] = f"{_fmt(A)}(x − ({_fmt(r1)}))(x − ({_fmt(r2)}))"
    return out


def domain_range(expr: str, var: str = "x", include_range: bool = False):
    f = _s(expr)
    x = sp.Symbol(str(var))
    dom = continuous_domain(f, x, sp.S.Reals)
    out = {"domain_reals": _fmt(dom)}
    try:
        out["singularities"] = _fmt(singularities(f, x))
    except Exception:
        pass
    if include_range:
        try:
            out["range"] = _fmt(function_range(f, x, dom))
        except Exception:
            out["range"] = "could not determine symbolically"
    return out


def ode_solve(equation: str, ics: dict = None):
    """Solve an ODE. Write derivatives as y' / y'' (or Derivative(y(x), x))."""
    y = sp.Function("y")
    x = sp.Symbol("x")
    eq = str(equation).replace("’", "'")
    eq = re.sub(r"y'''", "Derivative(y(x), (x, 3))", eq)
    eq = re.sub(r"y''", "Derivative(y(x), (x, 2))", eq)
    eq = re.sub(r"y'", "Derivative(y(x), x)", eq)
    eq = re.sub(r"\by\b(?!\()", "y(x)", eq)
    loc = {"y": y, "e": sp.E}
    lhs, _, rhs = eq.partition("=")
    E = sp.Eq(sp.sympify(lhs, locals=loc), sp.sympify(rhs, locals=loc) if rhs.strip() else 0)
    kw = {}
    if ics:
        parsed = {}
        for k, v in dict(ics).items():
            kk = re.sub(r"\by\b(?!\()", "y(x)", str(k).replace("'", ""))
            kk = re.sub(r"y'\(", "Derivative(y(x), x)(", kk.replace(" ", ""))
            kk = re.sub(r"y''\(", "Derivative(y(x), (x, 2))(", kk.replace(" ", ""))
            parsed[sp.sympify(kk, locals=loc)] = float(v)
        kw["ics"] = parsed
    sol = sp.dsolve(E, y(x), **kw)
    rhs_expr = sol.rhs if hasattr(sol, "rhs") else sol
    return {"solution": f"y(x) = {_fmt(rhs_expr)}", "latex": sp.latex(rhs_expr),
            "classification": str(sp.classify_ode(E, y(x))[0])}


# ════════════════════════════════════════════════════════════ COORDINATE GEOMETRY (2D)
def _pt(p):
    return ge.Point(float(p[0]), float(p[1]))


def _line_expr(line):
    """'2x+3y-5' or 'y=2x+1' → (a, b, c) for ax + by + c = 0."""
    x, y = sp.symbols("x y")
    s = str(line)
    if "=" in s:
        lhs, rhs = s.split("=", 1)
        e = _loose(lhs) - _loose(rhs)
    else:
        e = _loose(s)
    f = sp.expand(e)
    poly = sp.Poly(f, x, y)
    return poly.coeff_monomial(x), poly.coeff_monomial(y), poly.coeff_monomial(1)


def line_op(mode: str, p1=None, p2=None, point=None, line1=None, line2=None):
    mode = str(mode).lower()
    x, y = sp.symbols("x y")
    if mode == "equation_from_two_points" and p1 and p2:
        L = ge.Line(_pt(p1), _pt(p2))
        eq = L.equation(x, y)
        f = sp.expand(eq.lhs - eq.rhs)
        return {"equation": f"{_fmt(f)} = 0", "slope": _fmt(sp.nsimplify(L.slope)),
                "length": _fmt(L.length)}
    if mode == "dist_point_line" and point and line1:
        a, b, c = _line_expr(line1)
        val = a * float(point[0]) + b * float(point[1]) + c
        d = abs(val) / sp.sqrt(a ** 2 + b ** 2)
        return {"distance": _fmt(sp.simplify(d)),
                "formula": "|ax₁+by₁+c| / √(a²+b²)"}
    if mode == "angle_between_lines" and line1 and line2:
        a1, b1, _ = _line_expr(line1)
        a2, b2, _ = _line_expr(line2)
        m1, m2 = -a1 / b1, -a2 / b2
        tan_t = abs((m2 - m1) / (1 + m1 * m2))
        return {"angle_deg": round(math.degrees(math.atan(float(tan_t))), 6),
                "m1": _fmt(sp.simplify(m1)), "m2": _fmt(sp.simplify(m2))}
    if mode == "intersection" and line1 and line2:
        a1, b1, c1 = _line_expr(line1)
        a2, b2, c2 = _line_expr(line2)
        sol = sp.solve([sp.Eq(a1 * x + b1 * y + c1, 0), sp.Eq(a2 * x + b2 * y + c2, 0)], [x, y])
        if not sol:
            return {"note": "lines are parallel (no intersection)"}
        return {"point": [_fmt(sp.simplify(sol[x])), _fmt(sp.simplify(sol[y]))]}
    if mode == "foot_and_image_point_line" and point and line1:
        a, b, c = _line_expr(line1)
        px, py = float(point[0]), float(point[1])
        kk = (a * px + b * py + c) / (a * a + b * b)
        fx, fy = sp.simplify(px - a * kk), sp.simplify(py - b * kk)
        ix, iy = sp.simplify(px - 2 * a * kk), sp.simplify(py - 2 * b * kk)
        return {"foot_of_perpendicular": [_fmt(fx), _fmt(fy)], "image": [_fmt(ix), _fmt(iy)]}
    if mode == "dist_parallel_lines" and line1 and line2:
        a1, b1, c1 = _line_expr(line1)
        a2, b2, c2 = _line_expr(line2)
        if sp.simplify(a1 * b2 - a2 * b1) != 0:
            return {"note": "lines are NOT parallel — they intersect"}
        scale = (a2 / a1) if a1 != 0 else (b2 / b1)
        d = abs(c1 - c2 / scale) / sp.sqrt(a1 ** 2 + b1 ** 2)
        return {"distance": _fmt(sp.simplify(d)),
                "formula": "|c₁ − c₂|/√(a²+b²) after matching scales"}
    raise ValueError(f"Unsupported line_op mode/args: {mode}")


def circle_op(mode: str, h: float = None, k: float = None, r: float = None,
              equation: str = None, point=None, p1=None, p2=None, p3=None):
    mode = str(mode).lower()
    x, y = sp.symbols("x y")
    if mode == "from_center_radius":
        C = ge.Circle(ge.Point(float(h), float(k)), float(r))
        return {"center": [h, k], "radius": _fmt(C.radius), "area": _fmt(C.area),
                "circumference": _fmt(C.circumference),
                "equation": f"(x − {_fmt(h)})² + (y − {_fmt(k)})² = {_fmt(sp.simplify(float(r) ** 2))}"}
    if mode == "from_equation" and equation:
        a_, b_, c_ = _line_expr(equation)
        poly = sp.Poly(a_ * x + b_ * y + c_, x, y)
        a = poly.coeff_monomial(x)
        b = poly.coeff_monomial(y)
        c = poly.coeff_monomial(1)
        cx, cy = -a / 2, -b / 2
        r2 = sp.simplify(cx ** 2 + cy ** 2 - c)
        if r2 <= 0:
            return {"error": "Not a real circle (r² ≤ 0)"}
        return {"center": [_fmt(cx), _fmt(cy)], "r": _fmt(sp.sqrt(r2)), "r_squared": _fmt(r2),
                "standard_form": f"(x − {_fmt(cx)})² + (y − {_fmt(cy)})² = {_fmt(r2)}"}
    if mode == "from_3points" and p1 and p2 and p3:
        C = ge.Circle(_pt(p1), _pt(p2), _pt(p3))
        return {"center": [float(C.center.x), float(C.center.y)], "radius": _fmt(C.radius),
                "equation_pts": "circle through the 3 points"}
    if mode == "tangent_length" and point and equation:
        a_, b_, c_ = _line_expr(equation)
        poly = sp.Poly(a_ * x + b_ * y + c_, x, y)
        cx, cy = -poly.coeff_monomial(x) / 2, -poly.coeff_monomial(y) / 2
        r2 = sp.simplify(cx ** 2 + cy ** 2 - poly.coeff_monomial(1))
        d2 = (float(point[0]) - cx) ** 2 + (float(point[1]) - cy) ** 2
        return {"tangent_length": _fmt(sp.sqrt(sp.simplify(d2 - r2))),
                "formula": "L = √(S₁) where S₁ = power of the point"}
    raise ValueError(f"Unsupported circle_op mode/args: {mode}")


def conic_op(kind: str, a: float, b: float = None, orientation: str = "x"):
    kind = str(kind).lower()
    a = float(a)
    if kind == "parabola":
        sgn = -1 if str(orientation).lower() in ("left", "down") else 1
        axis_vertical = str(orientation).lower() in ("up", "down")
        A = abs(a)
        if axis_vertical:
            return {"opening": orientation, "focus": [0, sgn * A], "directrix": f"y = {-sgn * A}",
                    "latus_rectum": 4 * A, "equation": f"x² = {4 * A * sgn}·y (i.e. x² = 4ay form)",
                    "focal_length_a": A}
        return {"opening": orientation, "focus": [sgn * A, 0], "directrix": f"x = {-sgn * A}",
                "latus_rectum": 4 * A, "equation": f"y² = {4 * A * sgn}·x",
                "focal_length_a": A}
    if kind == "ellipse":
        b = float(b)
        if b > a:
            a, b = b, a
            major = "y-axis"
        else:
            major = "x-axis"
        c = math.sqrt(a * a - b * b)
        return {"a": a, "b": b, "c": round(c, 8), "eccentricity": round(c / a, 8),
                "foci": [round(c, 8), 0] if major == "x-axis" else [0, round(c, 8)],
                "vertices": [a, 0] if major == "x-axis" else [0, a],
                "latus_rectum": round(2 * b * b / a, 8),
                "directrices": round(a * a / c, 8),
                "sum_focal_distances": "2a (ellipse property)",
                "major_axis": major}
    if kind == "hyperbola":
        b = float(b)
        c = math.sqrt(a * a + b * b)
        return {"a": a, "b": b, "c": round(c, 8), "eccentricity": round(c / a, 8),
                "foci": [round(c, 8), 0], "vertices": [a, 0],
                "latus_rectum": round(2 * b * b / a, 8),
                "asymptotes": f"y = ±({round(b / a, 6)})x",
                "difference_focal_distances": "2a (hyperbola property)"}
    raise ValueError("kind: parabola | ellipse | hyperbola")


def triangle_op(p1=None, p2=None, p3=None, sides: list = None):
    if p1 and p2 and p3:
        A, B, C = _pt(p1), _pt(p2), _pt(p3)
        T = ge.Triangle(A, B, C)
        a = float(B.distance(C))
        b = float(C.distance(A))
        c = float(A.distance(B))

        def ang(x, y, z):
            return round(math.degrees(math.acos(max(-1, min(1, (y * y + z * z - x * x) / (2 * y * z))))), 6)
        angA, angB, angC = ang(a, b, c), ang(b, c, a), ang(c, a, b)
        types = []
        if abs(a * a - b * b - c * c) < 1e-9 or max(a, b, c) ** 2 < (sorted([a, b, c])[0] ** 2 + sorted([a, b, c])[1] ** 2):
            types.append("acute")
        if max(a, b, c) ** 2 > sorted([a, b, c])[0] ** 2 + sorted([a, b, c])[1] ** 2:
            types.append("obtuse")
        if abs(max(a, b, c) ** 2 - (sorted([a, b, c])[0] ** 2 + sorted([a, b, c])[1] ** 2)) < 1e-9:
            types = ["right-angled"]
        if len({round(a, 6), round(b, 6), round(c, 6)}) == 1:
            types.append("equilateral")
        elif len({round(a, 6), round(b, 6), round(c, 6)}) == 2:
            types.append("isosceles")
        else:
            types.append("scalene")
        cc, ic = T.circumcenter, T.incenter
        return {"side_lengths_abc": [round(a, 8), round(b, 8), round(c, 8)],
                "angles_ABC_deg": [angA, angB, angC], "area": _fmt(sp.simplify(T.area)),
                "type": "+".join(types),
                "centroid": [float(T.centroid.x), float(T.centroid.y)],
                "circumcenter": [float(cc.x), float(cc.y)],
                "circumradius": _fmt(T.circumcircle.radius),
                "incenter": [float(ic.x), float(ic.y)],
                "inradius": _fmt(T.incircle.radius),
                "orthocenter": [float(T.orthocenter.x), float(T.orthocenter.y)]}
    if sides and len(sides) == 3:
        a, b, c = [float(s) for s in sorted(sides)]
        if a + b <= c:
            return {"error": "Triangle inequality violated"}
        s = (a + b + c) / 2
        area = math.sqrt(s * (s - a) * (s - b) * (s - c))
        angA = math.degrees(math.acos((b * b + c * c - a * a) / (2 * b * c)))
        angB = math.degrees(math.acos((a * a + c * c - b * b) / (2 * a * c)))
        angC = 180 - angA - angB
        return {"semi_perimeter": s, "area_heron": round(area, 8),
                "angles_opposite_abc_deg": [round(angA, 6), round(angB, 6), round(angC, 6)],
                "circumradius_R": round(a * b * c / (4 * area), 8),
                "inradius_r": round(area / s, 8)}
    raise ValueError("Provide vertices p1,p2,p3 or sides [a,b,c]")


# ════════════════════════════════════════════════════════════ 3D GEOMETRY
def _v(p):
    return sp.Matrix([sp.Rational(str(float(c))).limit_denominator(10 ** 9) for c in p])


def _vn(v):
    return sp.sqrt(v.dot(v))


def solid3d(mode: str, **kw):
    mode = str(mode).lower()
    g = kw
    if mode == "dist_points":
        d = _v(g["p2"]) - _v(g["p1"])
        return {"distance": _fmt(_vn(d))}
    if mode == "plane_from_points" and all(g.get(k) for k in ("p1", "p2", "p3")):
        p1, p2, p3 = _v(g["p1"]), _v(g["p2"]), _v(g["p3"])
        n = (p2 - p1).cross(p3 - p1)
        d = -n.dot(p1)
        nrm = [sp.nsimplify(c) for c in n]
        return {"normal": [_fmt(c) for c in nrm], "d": _fmt(d),
                "equation": f"{_fmt(nrm[0])}x + {_fmt(nrm[1])}y + {_fmt(nrm[2])}z + {_fmt(d)} = 0"}
    if mode == "dist_point_plane" and g.get("point") and all(g.get(k) for k in ("p1", "p2", "p3")):
        p = _v(g["point"])
        p1, p2, p3 = _v(g["p1"]), _v(g["p2"]), _v(g["p3"])
        n = (p2 - p1).cross(p3 - p1)
        d = -n.dot(p1)
        dist = abs(n.dot(p) + d) / _vn(n)
        return {"distance": _fmt(sp.simplify(dist))}
    if mode == "foot_image_point_plane" and g.get("point") and g.get("normal") and g.get("plane_point"):
        p, n, q = _v(g["point"]), _v(g["normal"]), _v(g["plane_point"])
        t = (q - p).dot(n) / n.dot(n)
        foot = p + t * n
        img = p + 2 * t * n
        return {"foot_of_perpendicular": [_fmt(c) for c in foot],
                "image": [_fmt(c) for c in img]}
    if mode == "angle_line_plane" and all(g.get(k) for k in ("p1", "p2")) and g.get("normal"):
        d = _v(g["p2"]) - _v(g["p1"])
        n = _v(g["normal"])
        sin_t = abs(d.dot(n)) / (_vn(d) * _vn(n))
        return {"angle_deg": round(math.degrees(math.asin(float(sin_t))), 6),
                "note": "sinθ = |d·n|/(|d||n|)"}
    if mode == "angle_between_planes" and g.get("normal") and g.get("normal2"):
        n1, n2 = _v(g["normal"]), _v(g["normal2"])
        cos_t = abs(n1.dot(n2)) / (_vn(n1) * _vn(n2))
        return {"angle_deg": round(math.degrees(math.acos(float(cos_t))), 6)}
    if mode == "dist_skew_lines" and all(g.get(k) for k in ("p1", "p2", "p3", "p4")):
        p1, p2, p3, p4 = (_v(g[k]) for k in ("p1", "p2", "p3", "p4"))
        d1, d2 = p2 - p1, p4 - p3
        n = d1.cross(d2)
        if _vn(n) == 0:
            # parallel: distance from p3 to line1
            w = p3 - p1
            dist = _vn(w - (w.dot(d1) / d1.dot(d1)) * d1)
            return {"distance": _fmt(sp.simplify(dist)), "note": "lines are parallel"}
        dist = abs((p3 - p1).dot(n)) / _vn(n)
        return {"distance": _fmt(sp.simplify(dist)),
                "note": "|(p₃−p₁)·(d₁×d₂)|/|d₁×d₂| — shortest distance between skew lines"}
    if mode == "dist_point_line3d" and g.get("point") and all(g.get(k) for k in ("p1", "p2")):
        p, p1, p2 = _v(g["point"]), _v(g["p1"]), _v(g["p2"])
        d = p2 - p1
        w = p - p1
        dist = _vn(w - (w.dot(d) / d.dot(d)) * d)
        return {"distance": _fmt(sp.simplify(dist))}
    raise ValueError(f"Unsupported solid3d mode/args: {mode}")
