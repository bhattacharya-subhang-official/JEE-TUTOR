"""Engine registry — maps Gemini function-calling tool names to implementations."""
from engines import math_engine, physics_engine, chemistry_engine, tools_exec, plotting

# ---- grouped physics formulas: fn(kind, **params) ------------------------------
_PHYS_GROUPED = {
    "work_energy": physics_engine.work_energy,
    "momentum": physics_engine.momentum,
    "fluids": physics_engine.fluids,
    "elasticity": physics_engine.elasticity,
    "thermal": physics_engine.thermal,
    "kinetic_theory": physics_engine.kinetic_theory,
    "thermo_process": physics_engine.thermo_process,
    "electrostatics": physics_engine.electrostatics,
    "magnetism_extra": physics_engine.magnetism_extra,
    "emi": physics_engine.emi,
    "ac_circuits": physics_engine.ac_circuits,
    "em_waves": physics_engine.em_waves,
    "ray_optics2": physics_engine.ray_optics2,
    "wave_optics2": physics_engine.wave_optics2,
    "string_sound": physics_engine.string_sound,
    "rotation_extra": physics_engine.rotation_extra,
    "shm_extra": physics_engine.shm_extra,
    "modern_extra": physics_engine.modern_extra,
    "gravitation_extra": physics_engine.gravitation_extra,
}
_PHYS_FLAT = {
    "projectile": physics_engine.projectile,
    "suvat": physics_engine.suvat,
    "circular_motion": physics_engine.circular_motion,
    "shm": physics_engine.shm,
    "gravitation": physics_engine.gravitation,
    "collisions": physics_engine.collisions,
    "rotation": physics_engine.rotation,
    "coulomb": physics_engine.coulomb,
    "electric_field_point": physics_engine.electric_field_point,
    "capacitors": physics_engine.capacitors,
    "current_electricity": physics_engine.current_electricity,
    "optics": physics_engine.optics,
    "doppler": physics_engine.doppler,
    "sound_wave": physics_engine.sound_wave,
    "interference": physics_engine.wave_optics_interference,
    "modern_physics": physics_engine.modern_physics,
    "thermodynamics": physics_engine.thermodynamics,
    "magnetism": physics_engine.current_magnetism,
    "friction_incline": physics_engine.friction_incline,
    "capacitor_share": physics_engine.capacitor_share,
    "error_propagation": lambda **kw: physics_engine.error_propagation(kw.pop("formula"), kw.pop("values")),
}


def physics_formula(formula: str, params: dict):
    formula = str(formula)
    params = dict(params or {})
    fn = _PHYS_FLAT.get(formula) or _PHYS_GROUPED.get(formula)
    if fn is None:
        raise ValueError(f"Unknown formula '{formula}'. Available: {', '.join(sorted(set(_PHYS_FLAT) | set(_PHYS_GROUPED)))}")
    if formula in _PHYS_GROUPED:
        kind = params.pop("kind", None)
        if not kind:
            raise ValueError(f"'{formula}' needs a 'kind' parameter")
        try:
            return fn(str(kind), **params)
        except TypeError as e:
            raise ValueError(f"Bad parameters for {formula}({kind}): {e}")
    params.pop("kind", None)
    if formula == "optics":
        return fn(params.pop("lens_or_mirror", "lens"), **params)
    try:
        return fn(**params)
    except TypeError as e:
        raise ValueError(f"Bad parameters for {formula}: {e}")


# ---- grouped chemistry: chem_calc(tool, params) ---------------------------------
_CHEM_GROUPED = {
    "concentration": chemistry_engine.concentration_calc,
    "gas_laws": chemistry_engine.gas_laws,
    "equilibrium": chemistry_engine.equilibrium_tools,
    "ionic": chemistry_engine.ionic_tools,
    "kinetics": chemistry_engine.kinetics_tools,
    "thermochem": chemistry_engine.thermochem,
    "electrochem2": chemistry_engine.electrochem2,
    "coordination": chemistry_engine.coordination,
    "organic": chemistry_engine.organic_tools,
    "solutions2": chemistry_engine.solutions_extra,
}


def chem_calc(tool: str, params: dict):
    tool = str(tool)
    params = dict(params or {})
    fn = _CHEM_GROUPED.get(tool)
    if fn is not None:
        kind = params.pop("kind", None)
        if not kind:
            raise ValueError(f"'{tool}' needs a 'kind' parameter")
        try:
            return fn(str(kind), **params)
        except TypeError as e:
            raise ValueError(f"Bad parameters for {tool}({kind}): {e}")
    flat = {
        "limiting_reagent": chemistry_engine.limiting_reagent,
        "oxidation_number": lambda **kw: chemistry_engine.oxidation_number(kw.pop("species"), kw.pop("element"), kw.pop("oxide_type", "normal")),
        "empirical_formula": lambda **kw: chemistry_engine.empirical_formula(kw.pop("composition"), kw.pop("molar_mass_val", None)),
        "combustion_analysis": chemistry_engine.combustion_analysis,
        "degree_unsaturation": lambda **kw: chemistry_engine.degree_unsaturation(kw.pop("formula")),
        "bond_order": lambda **kw: chemistry_engine.bond_order_mo(kw.pop("species")),
    }
    fn2 = flat.get(tool)
    if fn2 is None:
        raise ValueError(f"Unknown chem tool '{tool}'. Available: {', '.join(sorted(set(_CHEM_GROUPED) | set(flat)))}")
    try:
        return fn2(**params)
    except TypeError as e:
        raise ValueError(f"Bad parameters for {tool}: {e}")


# name -> callable(args_dict) -> dict
TOOLS = {
    # ── general
    "calc": lambda a: tools_exec.calc(a["expression"]),
    "python_exec": lambda a: tools_exec.python_exec(a["code"], timeout=int(a.get("timeout", 25))),
    "units_convert": lambda a: math_engine.units_convert(a["value"], a["from_unit"], a["to_unit"]),
    "physical_constant": lambda a: math_engine.physical_constant(a["name"]),
    # ── algebra / calculus
    "solve_equation": lambda a: math_engine.solve_equation(a["equations"], a["variables"]),
    "calculus": lambda a: math_engine.calculus(
        a["action"], a["expr"], a.get("var", "x"), a.get("order", 1),
        a.get("lower"), a.get("upper"), a.get("point"), a.get("direction", "+"), a.get("series_order", 6)),
    "simplify_expr": lambda a: math_engine.simplify_expr(a["expr"], a.get("action", "simplify")),
    "polynomial_roots": lambda a: math_engine.polynomial_roots(a["expr"], a.get("var", "x"), bool(a.get("numeric", False))),
    "nsolve_system": lambda a: math_engine.nsolve_system(a["equations"], a["variables"], a["guesses"]),
    "matrix_op": lambda a: math_engine.matrix_op(a["matrix"], a["op"], a.get("matrix2"), a.get("scalar")),
    "vector_op": lambda a: math_engine.vector_op(a["a"], a["op"], a.get("b")),
    "quadratic_analysis": lambda a: math_engine.quadratic_analysis(a["a"], a["b"], a["c"]),
    "ode_solve": lambda a: math_engine.ode_solve(a["equation"], a.get("ics")),
    "domain_range": lambda a: math_engine.domain_range(a["expr"], a.get("var", "x"), bool(a.get("include_range", False))),
    # ── complex / sequences / binomial / prob-stats
    "complex_op": lambda a: math_engine.complex_op(a["z1"], a["op"], a.get("z2"), a.get("n")),
    "sequence_series": lambda a: math_engine.sequence_series(
        a["kind"], a.get("a"), a.get("d"), a.get("n"), a.get("last"), a.get("numbers")),
    "binomial_theorem": lambda a: math_engine.binomial_theorem(
        a.get("a", "x"), a.get("b", "1"), a.get("power", 5), a.get("term_r"), a.get("coeff_of")),
    "combinatorics": lambda a: math_engine.combinatorics(a["n"], a.get("r", 0), a.get("kind", "nCr")),
    "binomial_probability": lambda a: math_engine.binomial_probability(a["n"], a["p"], a["k"], a.get("mode", "exact")),
    "statistics_calc": lambda a: math_engine.statistics_calc(a["numbers"]),
    "normal_probability": lambda a: math_engine.normal_probability(a["mu"], a["sigma"], a["x1"], a.get("x2"), a.get("tail", "below")),
    # ── coordinate geometry
    "line_op": lambda a: math_engine.line_op(a["mode"], a.get("p1"), a.get("p2"), a.get("point"), a.get("line1"), a.get("line2")),
    "circle_op": lambda a: math_engine.circle_op(
        a["mode"], a.get("h"), a.get("k"), a.get("r"), a.get("equation"), a.get("point"), a.get("p1"), a.get("p2"), a.get("p3")),
    "conic_op": lambda a: math_engine.conic_op(a["kind"], a["a"], a.get("b"), a.get("orientation", "x")),
    "triangle_op": lambda a: math_engine.triangle_op(a.get("p1"), a.get("p2"), a.get("p3"), a.get("sides")),
    "solid3d": lambda a: math_engine.solid3d(a["mode"], **{k: v for k, v in a.items() if k != "mode"}),
    # ── plots
    "plot_graph": lambda a: plotting.plot_graph(
        a["functions"], a["x_min"], a["x_max"], a.get("title", ""),
        a.get("x_label", "x"), a.get("y_label", "y"), a.get("x_points"), a.get("y_points")),
    "plot_surface": lambda a: plotting.plot_surface(
        a["function"], a["x_min"], a["x_max"], a["y_min"], a["y_max"], a.get("title", "")),
    # ── physics
    "physics_formula": lambda a: physics_formula(a["formula"], a.get("params", {})),
    # ── chemistry
    "chemistry_balance": lambda a: chemistry_engine.balance_equation(a["reaction"]),
    "molar_mass": lambda a: chemistry_engine.molar_mass(a["formula"]),
    "stoich_calc": lambda a: chemistry_engine.stoich_calc(
        a["reaction"], a["known_species"], a["known_amount"], a["target_species"],
        bool(a.get("known_is_grams", False))),
    "ph_calc": lambda a: chemistry_engine.ph_calc(
        a["mode"], a["concentration"], int(a.get("basicity", 1)),
        a.get("dilution_factor", 1.0), a.get("ka"), a.get("temp_K", 298.0)),
    "nernst_emf": lambda a: chemistry_engine.nernst_emf(
        a["E0"], int(a["n"]), a["Q"], a.get("temperature_K", 298.0)),
    "faraday_electrolysis": lambda a: chemistry_engine.faraday_electrolysis(
        a["I"], a["t_s"], int(a["z"]), a.get("species_molar_mass")),
    "gibbs_free_energy": lambda a: chemistry_engine.gibbs_free_energy(
        a["dH_kJ"], a["dS_J"], a.get("T", 298.0)),
    "solution_properties": lambda a: chemistry_engine.solution_properties(a["kind"], **a.get("params", {})),
    "chem_calc": lambda a: chem_calc(a["tool"], a.get("params", {})),
}


def execute(name: str, args: dict) -> dict:
    fn = TOOLS.get(name)
    if fn is None:
        return {"error": f"Unknown tool '{name}'"}
    try:
        return fn(args or {})
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}
