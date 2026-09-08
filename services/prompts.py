"""System prompts + Gemini tool (function) declarations."""
import config

# ------------------------------------------------------------------ tools
FD = [
    {"name": "calc", "description": "Fast safe arithmetic evaluation. Supports + - * / ^ % //, sqrt, sin, cos, tan, asin, acos, atan, atan2, log, log10, log2, exp, abs, floor, ceil, round, min, max, hypot, factorial, deg/rad; constants pi, e, g, c, h, NA, q(=1.6e-19), me, mp, R, F.",
     "parameters": {"type": "OBJECT", "properties": {"expression": {"type": "STRING"}}, "required": ["expression"]}},
    {"name": "python_exec", "description": "Sandboxed Python for multi-step numerics, simulation, iteration, linear algebra, ODEs, root-finding. numpy, scipy, sympy, math preloaded. MUST print() results. Runs max 25s.",
     "parameters": {"type": "OBJECT", "properties": {"code": {"type": "STRING"}}, "required": ["code"]}},
    {"name": "solve_equation", "description": "Symbolic equation solving (algebra, simultaneous equations, trig, exponential). Use '==' or '=' inside equation strings. e.g. equations=['x**2 - 5*x + 6 = 0'], variables=['x'].",
     "parameters": {"type": "OBJECT", "properties": {
         "equations": {"type": "ARRAY", "items": {"type": "STRING"}},
         "variables": {"type": "ARRAY", "items": {"type": "STRING"}}},
         "required": ["equations", "variables"]}},
    {"name": "calculus", "description": "Differentiate, integrate (definite/indefinite), limit, Taylor series. action=diff|integrate|limit|series.",
     "parameters": {"type": "OBJECT", "properties": {
         "action": {"type": "STRING", "enum": ["diff", "integrate", "limit", "series"]},
         "expr": {"type": "STRING"}, "var": {"type": "STRING"},
         "order": {"type": "INTEGER"}, "lower": {"type": "STRING"}, "upper": {"type": "STRING"},
         "point": {"type": "STRING"}, "direction": {"type": "STRING", "enum": ["+", "-", "both"]},
         "series_order": {"type": "INTEGER"}},
         "required": ["action", "expr"]}},
    {"name": "simplify_expr", "description": "Simplify / expand / factor / trigsimp an expression.",
     "parameters": {"type": "OBJECT", "properties": {
         "expr": {"type": "STRING"},
         "action": {"type": "STRING", "enum": ["simplify", "expand", "factor", "trigsimp", "apart", "together", "radsimp"]}},
         "required": ["expr"]}},
    {"name": "polynomial_roots", "description": "Roots of a polynomial; numeric=true for numeric roots of any function.",
     "parameters": {"type": "OBJECT", "properties": {
         "expr": {"type": "STRING"}, "var": {"type": "STRING"}, "numeric": {"type": "BOOLEAN"}},
         "required": ["expr"]}},
    {"name": "nsolve_system", "description": "Numeric solution of nonlinear system (Newton). Provide one guess per variable.",
     "parameters": {"type": "OBJECT", "properties": {
         "equations": {"type": "ARRAY", "items": {"type": "STRING"}},
         "variables": {"type": "ARRAY", "items": {"type": "STRING"}},
         "guesses": {"type": "ARRAY", "items": {"type": "NUMBER"}}},
         "required": ["equations", "variables", "guesses"]}},
    {"name": "matrix_op", "description": "Matrix operations: determinant, inverse, transpose, rank, trace, eigenvalues, eigenvectors, charpoly, multiply, add, power, adjoint.",
     "parameters": {"type": "OBJECT", "properties": {
         "matrix": {"type": "ARRAY", "items": {"type": "ARRAY", "items": {"type": "NUMBER"}}},
         "op": {"type": "STRING"},
         "matrix2": {"type": "ARRAY", "items": {"type": "ARRAY", "items": {"type": "NUMBER"}}},
         "scalar": {"type": "NUMBER"}},
         "required": ["matrix", "op"]}},
    {"name": "vector_op", "description": "3D vector ops: dot, cross, magnitude, unit, angle, projection, area_parallelogram.",
     "parameters": {"type": "OBJECT", "properties": {
         "a": {"type": "ARRAY", "items": {"type": "NUMBER"}},
         "b": {"type": "ARRAY", "items": {"type": "NUMBER"}},
         "op": {"type": "STRING", "enum": ["dot", "cross", "magnitude", "unit", "angle", "projection", "area_parallelogram"]}},
         "required": ["a", "op"]}},
    {"name": "units_convert", "description": "Physical unit conversion via sympy units. from/to use sympy names: meter, centimeter, kilometer, inch, foot, mile, second, hour, day, kilogram, gram, newton, joule, electronvolt, watt, pascal, atmosphere, coulomb, ampere, volt, ohm, tesla, gauss, weber, henry, farad, kelvin, celsius(fabricated? use kelvin), mole, radian, degree, liter, m/s as meter/second, etc.",
     "parameters": {"type": "OBJECT", "properties": {
         "value": {"type": "NUMBER"}, "from_unit": {"type": "STRING"}, "to_unit": {"type": "STRING"}},
         "required": ["value", "from_unit", "to_unit"]}},
    {"name": "physical_constant", "description": "Get CODATA physical constants: g, G, c, h, hbar, e, me, mp, mn, amu, NA, kB, R, F, epsilon0, mu0, k_coulomb, atm, eV, Rydberg, Bohr, sigma.",
     "parameters": {"type": "OBJECT", "properties": {"name": {"type": "STRING"}}, "required": ["name"]}},
    {"name": "plot_graph", "description": "Plot 1+ functions of x to an SVG image (returned to user). functions like ['sin(x)', 'x**2/4']. Optionally scatter points.",
     "parameters": {"type": "OBJECT", "properties": {
         "functions": {"type": "ARRAY", "items": {"type": "STRING"}},
         "x_min": {"type": "NUMBER"}, "x_max": {"type": "NUMBER"},
         "title": {"type": "STRING"}, "x_label": {"type": "STRING"}, "y_label": {"type": "STRING"},
         "x_points": {"type": "ARRAY", "items": {"type": "NUMBER"}},
         "y_points": {"type": "ARRAY", "items": {"type": "NUMBER"}}},
         "required": ["functions", "x_min", "x_max"]}},
    {"name": "plot_surface", "description": "3D surface z=f(x,y) as PNG (returned to user).",
     "parameters": {"type": "OBJECT", "properties": {
         "function": {"type": "STRING"},
         "x_min": {"type": "NUMBER"}, "x_max": {"type": "NUMBER"},
         "y_min": {"type": "NUMBER"}, "y_max": {"type": "NUMBER"}, "title": {"type": "STRING"}},
         "required": ["function", "x_min", "x_max", "y_min", "y_max"]}},
    {"name": "physics_formula", "description": "JEE physics formula solver. FLAT formulas: projectile(v0, angle_deg, g, h0); suvat(any 3-4 of u,v,a,s,t); circular_motion(m,v,r); shm(m,k,A); gravitation(M,R,r,h,m); collisions(m1,m2,u1,u2,e:1=elastic,0=inelastic); rotation(I,alpha,tau,L,omega,KE); coulomb(q1,q2,r,medium_k); electric_field_point(q,r); capacitors(capacitances list, mode series/parallel, V); current_electricity(any 2 of V,I,R,t); optics(lens_or_mirror, f, u, h; Cartesian signs); doppler(f0, wave_speed, v_source>0 approaching, v_observer); sound_wave(f or lam, v); interference(d, lam, D, order); friction_incline(m, angle_deg, mu_s, mu_k, applied_N); capacitor_share(C1,C2,V1,V2); error_propagation(formula str in names, values{name:[value,err]}). GROUPED (need params.kind): work_energy[work(F,d,theta_deg)|ke(m,v)|pe(m,h)|spring_pe(k,x)|power_force(F,v)|efficiency(out,in)|work_energy_theorem(m,v1,v2)]; momentum[center_of_mass(masses[[m,x,y,z]..])|impulse(F,t,m | dp,t)|conservation_1d(m1,u1,m2,u2)]; fluids[buoyant_force(rho_fluid,V)|float_fraction(rho_obj,rho_fluid)|apparent_weight(m,rho_obj,rho_fluid)|bernoulli(P1,v1,h1,rho + two of P2,v2,h2)|continuity(A1,v1,A2)|torricelli(h,A)|stokes_terminal(r,rho_s,rho_f,eta)|reynolds(rho,v,D,eta)|capillary_rise(sigma,theta_deg,rho,r)|excess_pressure(sigma,r,bubble=drop/soap_bubble)|pascal_hydraulic(F1,A1,A2)]; elasticity[youngs(F,A,dl,L)|thermal_stress(Y,alpha,dT,A)|poisson]; thermal[calorimetry(m,c,dT)|latent(m,L)|mixing(m1,c1,T1,m2,c2,T2)|expansion(L0,alpha,dT,mode linear/area/volume)|conduction(k,A,dT,L)|conduction_series(rods[{k,L,A}],dT)|stefan(A,e,T,T0)|wien(T)|newton_cooling(k,T0,T_env,t)]; kinetic_theory[speeds(molar_mass_g or m_kg, T)|pressure(n,V,T)|mean_free_path(d,n_V)|dof_energy(dof,T)]; thermo_process[isothermal(n,T,V1,V2)|adiabatic(P1,V1,V2,gamma,n)|isobaric/isochoric(n,T1,T2)|carnot_eff/carnot_cop(T_hot,T_cold)|engine_eff(W,Q_in)]; electrostatics[field_ring(Q,R,z)|field_sheet(sigma)|shell(Q,R,r)|solid_sphere(Q,R,r)|dipole_field(p,r,mode axial/equatorial)|dipole_torque(p,E,theta_deg)|pe_charges(pairs[[q1,q2,r]..])|gauss_flux(Q_enc | E,A,theta_deg)|work_q(q,V1,V2)|dielectric_slab(A,d,t,K)|energy_density(E,V)]; magnetism_extra[wire_force(I,L,B,theta_deg)|parallel_wires(I1,I2,d)|loop_torque(N,I,A,B,theta_deg)|loop_center(N,I,R)|loop_axis(N,I,R,z)|helix(q,m,v_perp,v_parallel,B)]; emi[motional_emf(B,L,v)|self_emf(L,dI_dt)|solenoid_L(n_per_m,A,l)|mutual_emf(M,dI_dt)|inductor_energy(L,I,B)|lr_circuit(L,R,V0,t,mode growth/decay)|lc_oscillation(L,C)|induced_charge(dPhi,R)]; ac_circuits[lcr(R,L,C,f,V)|rms(V_peak or V_rms)|transformer(Np,Ns,Vp,eff,Ip or Is)]; em_waves[relation(f or lambda_m)|intensity_E(E0,A)|E_from_I(I)|radiation_pressure(I,surface absorbing/reflecting)]; ray_optics2[snell(n1,n2,theta1_deg)|critical_angle(n1,n2)|prism_n(A_deg,delta_min_deg)|prism_deviation(A_deg,n)|lens_combo(f1,f2,d)|magnifier(f)|telescope(f_obj,f_eye)|microscope(f_obj,f_eye,L_cm)]; wave_optics2[single_slit(a,lambda_m,theta_deg?,D?,m?)|brewster(n_ratio)|malus(I0,theta_deg)|rayleigh(lambda_m,D)]; string_sound[string_speed(T,mu or m,L)|harmonics(v,L,mode both_fixed/one_open)|beats(f1,f2)|decibel(I)|intensity_from_db(dB)|organ_pipe(v,L,type open/closed)]; rotation_extra[rolling_energy(m,v,body ring/disc/solid_sphere/hollow_sphere)|roll_incline(m,theta_deg,body)|parallel_axis(I_cm,m,d)|ang_mom_conservation(I1,omega1,I2)]; shm_extra[pendulum(L,g)|physical_pendulum(I,m,d)|springs_series/parallel(k1,k2)|energy_partition(m,A,omega,x)]; gravitation_extra[orbit_energies(M,m,r)|g_variation(R,h or d)|kepler3(r,M)|escape_energy(M,m,R)]; modern_extra[binding_energy(Z,A,m_nucleus_u)|decay(N0,half_life,t | fraction)|xray_min(V_volt)|moseley(Z,b,transition K_alpha/K_beta)|mass_energy(m_kg or m_u)|bohr_transition(n1,n2,Z)].",
     "parameters": {"type": "OBJECT", "properties": {
         "formula": {"type": "STRING"},
         "params": {"type": "OBJECT"}},
         "required": ["formula"]}},
    {"name": "chemistry_balance", "description": "Balance a chemical equation. Input 'H2 + O2 -> H2O'. Returns balanced equation + coefficients.",
     "parameters": {"type": "OBJECT", "properties": {"reaction": {"type": "STRING"}}, "required": ["reaction"]}},
    {"name": "molar_mass", "description": "Molar mass from formula, e.g. 'CuSO4.5H2O', 'KMnO4'.",
     "parameters": {"type": "OBJECT", "properties": {"formula": {"type": "STRING"}}, "required": ["formula"]}},
    {"name": "stoich_calc", "description": "Stoichiometry: balance reaction, convert known amount (mol or g) of one species → mol + grams + STP-liters of target.",
     "parameters": {"type": "OBJECT", "properties": {
         "reaction": {"type": "STRING"}, "known_species": {"type": "STRING"},
         "known_amount": {"type": "NUMBER"}, "target_species": {"type": "STRING"},
         "known_is_grams": {"type": "BOOLEAN"}},
         "required": ["reaction", "known_species", "known_amount", "target_species"]}},
    {"name": "ph_calc", "description": "pH calculations. mode ∈ strong_acid|strong_base|weak_acid|weak_base. params: concentration(M), basicity(1 for HCl, 2 for H2SO4), ka or kb for weak, dilution_factor.",
     "parameters": {"type": "OBJECT", "properties": {
         "mode": {"type": "STRING", "enum": ["strong_acid", "strong_base", "weak_acid", "weak_base"]},
         "concentration": {"type": "NUMBER"}, "basicity": {"type": "INTEGER"},
         "dilution_factor": {"type": "NUMBER"}, "ka": {"type": "NUMBER"}, "temp_K": {"type": "NUMBER"}},
         "required": ["mode", "concentration"]}},
    {"name": "nernst_emf", "description": "Nernst equation E = E° − (RT/nF)lnQ. Also gives 0.0591 form at 298K.",
     "parameters": {"type": "OBJECT", "properties": {
         "E0": {"type": "NUMBER"}, "n": {"type": "INTEGER"}, "Q": {"type": "NUMBER"}, "temperature_K": {"type": "NUMBER"}},
         "required": ["E0", "n", "Q"]}},
    {"name": "faraday_electrolysis", "description": "Faraday's laws of electrolysis: moles of e⁻, charge, mass deposited (needs species_molar_mass and z = electrons per ion).",
     "parameters": {"type": "OBJECT", "properties": {
         "I": {"type": "NUMBER"}, "t_s": {"type": "NUMBER"}, "z": {"type": "INTEGER"}, "species_molar_mass": {"type": "NUMBER"}},
         "required": ["I", "t_s", "z"]}},
    {"name": "gibbs_free_energy", "description": "ΔG = ΔH − TΔS in kJ/mol; spontaneity + equilibrium temperature.",
     "parameters": {"type": "OBJECT", "properties": {
         "dH_kJ": {"type": "NUMBER"}, "dS_J": {"type": "NUMBER"}, "T": {"type": "NUMBER"}},
         "required": ["dH_kJ", "dS_J"]}},
    {"name": "solution_properties", "description": "Colligative/van't Hoff: kind ∈ osmotic(molarity,T,i) | boiling_elevation(kb,molality,i) | freezing_depression(kf,molality,i). Pass others via params.",
     "parameters": {"type": "OBJECT", "properties": {
         "kind": {"type": "STRING"}, "params": {"type": "OBJECT"}},
         "required": ["kind"]}},
    {"name": "chem_calc", "description": "JEE chemistry calculator. FLAT tools: limiting_reagent(reaction, amounts[{species,amount,is_grams}], actual_yield_g?, product?); oxidation_number(species like 'MnO4-'/'Cr2O7--', element, oxide_type normal/peroxide/superoxide); empirical_formula(composition{el:mass}, molar_mass_val? → empirical + molecular); combustion_analysis(sample_g, co2_g, h2o_g, molar_mass_val?); degree_unsaturation(formula); bond_order(species 'O2','O2-','N2','NO+','CN-','CO' → MO bond order + magnetism). GROUPED (need params.kind): concentration[molarity_from_mass(formula or molar_mass, mass_g, volume_L)|molality(moles_solute,solvent_kg)|mole_fraction(moles list)|ppm|dilution(any 3 of M1,V1,M2,V2)|molarity_to_molality(M,density_g_mL,molar_mass_solute)]; gas_laws[combined(any 5 of P1,V1,T1,P2,V2,T2)|partial_pressure(n_i,n_total,P_total)|grahams(M1,M2 or rates)|vanderwaals(n,a,b,T,V)|compressibility(P,V,n,T)]; equilibrium[kp_kc(reaction,Kc or Kp,T)|dissociation_alpha(Kp,P_total)]; ionic[buffer_acidic(pKa, ratio or salt_moles+acid_moles)|buffer_basic(pKb,...)|solubility_from_ksp(Ksp,type AB/AB2/A2B/AB3,formula?)|ksp_from_solubility(solubility_mol/L,type)|salt_ph(pKa and/or pKb, c)]; kinetics[first_order(k,c0?,t?/c_now?)|second_order(k,c0,t?)|zero_order(k,c0,t?)|arrhenius(A,Ea,T | k1,T1,T2,Ea)]; thermochem[heat(m,c,dT)|bond_enthalpy(broken_kJ list,formed_kJ list)|transition_entropy(dH_J,T)|calorimetry_dH(m_solution,dT,moles_reactant)]; electrochem2[molar_conductivity(kappa_S_per_cm,M)|degree_dissociation(Lambda_m,Lambda_m0)|cell_potential(E_anode,E_cathode)|nernst_conc(E0,n,c_oxidized,c_reduced)]; coordination[magnetic_moment(n_unpaired)|ean(Z,ox_state,coordination_number)|cfse(d_n,geometry oct/tet,strong_field)]; organic[dou(formula)|percent_composition(composition)]; solutions2[raoult_lowering(P0,x_solute)|henry(KH,x)|vapor_ideal(P1_deg,P2_deg,x1)].",
     "parameters": {"type": "OBJECT", "properties": {
         "tool": {"type": "STRING"}, "params": {"type": "OBJECT"}},
         "required": ["tool"]}},
    {"name": "complex_op", "description": "Complex numbers: parse '3+4i'. op ∈ add|subtract|multiply|divide|modulus|argument|conjugate|reciprocal|polar|power(exp n)|roots(n-th roots, all k).",
     "parameters": {"type": "OBJECT", "properties": {
         "z1": {"type": "STRING"}, "op": {"type": "STRING"}, "z2": {"type": "STRING"}, "n": {"type": "INTEGER"}},
         "required": ["z1", "op"]}},
    {"name": "sequence_series", "description": "Sequences & series: kind ∈ ap(a,d or last,n → nth term+sum) | gp(a,r=d,n, infinite sum if |r|<1) | hp(a,d,n, d=step of reciprocals) | sum_n | sum_n2 | sum_n3 (n) | am_gm_hm(numbers list).",
     "parameters": {"type": "OBJECT", "properties": {
         "kind": {"type": "STRING"}, "a": {"type": "NUMBER"}, "d": {"type": "NUMBER"},
         "n": {"type": "INTEGER"}, "last": {"type": "NUMBER"}, "numbers": {"type": "ARRAY", "items": {"type": "NUMBER"}}},
         "required": ["kind"]}},
    {"name": "binomial_theorem", "description": "Binomial expansion of (a+b)^n; get full expansion, middle term indices, term_r (T_{r+1}, 0-indexed r), coeff_of (monomial like 'x**3').",
     "parameters": {"type": "OBJECT", "properties": {
         "a": {"type": "STRING"}, "b": {"type": "STRING"}, "power": {"type": "INTEGER"},
         "term_r": {"type": "INTEGER"}, "coeff_of": {"type": "STRING"}},
         "required": ["power"]}},
    {"name": "combinatorics", "description": "nCr | nPr | factorial | power_set | arrange_repetition(n^r).",
     "parameters": {"type": "OBJECT", "properties": {
         "n": {"type": "INTEGER"}, "r": {"type": "INTEGER"}, "kind": {"type": "STRING"}},
         "required": ["n"]}},
    {"name": "binomial_probability", "description": "Binomial distribution P(X=k), mode exact | at_least | at_most. Also returns mean np, variance npq.",
     "parameters": {"type": "OBJECT", "properties": {
         "n": {"type": "INTEGER"}, "p": {"type": "NUMBER"}, "k": {"type": "INTEGER"}, "mode": {"type": "STRING"}},
         "required": ["n", "p", "k"]}},
    {"name": "statistics_calc", "description": "Full descriptive statistics of a number list: mean, median, mode, variance (pop+sample), std, quartiles, IQR, range.",
     "parameters": {"type": "OBJECT", "properties": {
         "numbers": {"type": "ARRAY", "items": {"type": "NUMBER"}}}, "required": ["numbers"]}},
    {"name": "normal_probability", "description": "Normal distribution P: tail below | above | between(x1,x2).",
     "parameters": {"type": "OBJECT", "properties": {
         "mu": {"type": "NUMBER"}, "sigma": {"type": "NUMBER"}, "x1": {"type": "NUMBER"},
         "x2": {"type": "NUMBER"}, "tail": {"type": "STRING"}}, "required": ["mu", "sigma", "x1"]}},
    {"name": "quadratic_analysis", "description": "ax²+bx+c: discriminant, exact+numeric roots, nature, sum/product, vertex, axis, factorized form.",
     "parameters": {"type": "OBJECT", "properties": {
         "a": {"type": "NUMBER"}, "b": {"type": "NUMBER"}, "c": {"type": "NUMBER"}},
         "required": ["a", "b", "c"]}},
    {"name": "domain_range", "description": "Real domain + singularities of f(x); optional range (include_range=true, may be slow).",
     "parameters": {"type": "OBJECT", "properties": {
         "expr": {"type": "STRING"}, "var": {"type": "STRING"}, "include_range": {"type": "BOOLEAN"}},
         "required": ["expr"]}},
    {"name": "ode_solve", "description": "Solve ODE with dsolve. Write y''/y' for derivatives, y for y(x); ics dict like {'y(0)': 1}. Example equation: y'' + 4*y = 0.",
     "parameters": {"type": "OBJECT", "properties": {
         "equation": {"type": "STRING"}, "ics": {"type": "OBJECT"}}, "required": ["equation"]}},
    {"name": "line_op", "description": "2D lines: mode ∈ equation_from_two_points(p1,p2) | dist_point_line(point, line 'y=2x+1' or '3x+4y-5') | angle_between_lines(line1,line2) | intersection(line1,line2) | foot_and_image_point_line(point,line1) | dist_parallel_lines(line1,line2).",
     "parameters": {"type": "OBJECT", "properties": {
         "mode": {"type": "STRING"}, "p1": {"type": "ARRAY", "items": {"type": "NUMBER"}},
         "p2": {"type": "ARRAY", "items": {"type": "NUMBER"}},
         "point": {"type": "ARRAY", "items": {"type": "NUMBER"}},
         "line1": {"type": "STRING"}, "line2": {"type": "STRING"}},
         "required": ["mode"]}},
    {"name": "circle_op", "description": "Circles: mode ∈ from_center_radius(h,k,r) | from_equation('x**2+y**2-4*x+6*y-12' or '=25' forms) | from_3points(p1,p2,p3) | tangent_length(point, equation).",
     "parameters": {"type": "OBJECT", "properties": {
         "mode": {"type": "STRING"}, "h": {"type": "NUMBER"}, "k": {"type": "NUMBER"}, "r": {"type": "NUMBER"},
         "equation": {"type": "STRING"}, "point": {"type": "ARRAY", "items": {"type": "NUMBER"}},
         "p1": {"type": "ARRAY", "items": {"type": "NUMBER"}}, "p2": {"type": "ARRAY", "items": {"type": "NUMBER"}},
         "p3": {"type": "ARRAY", "items": {"type": "NUMBER"}}}, "required": ["mode"]}},
    {"name": "conic_op", "description": "Conic properties: kind parabola(a, orientation right/left/up/down; y²=4ax type) | ellipse(a,b; x²/a²+y²/b²) | hyperbola(a,b) → foci, eccentricity, latus rectum, directrices, asymptotes.",
     "parameters": {"type": "OBJECT", "properties": {
         "kind": {"type": "STRING"}, "a": {"type": "NUMBER"}, "b": {"type": "NUMBER"}, "orientation": {"type": "STRING"}},
         "required": ["kind", "a"]}},
    {"name": "triangle_op", "description": "Triangle from vertices p1,p2,p3 (area, angles, centroid, circumcenter+R, incenter+r, orthocenter, type) or sides [a,b,c] (Heron).",
     "parameters": {"type": "OBJECT", "properties": {
         "p1": {"type": "ARRAY", "items": {"type": "NUMBER"}}, "p2": {"type": "ARRAY", "items": {"type": "NUMBER"}},
         "p3": {"type": "ARRAY", "items": {"type": "NUMBER"}}, "sides": {"type": "ARRAY", "items": {"type": "NUMBER"}}},
         "required": []}},
    {"name": "solid3d", "description": "3D geometry: mode ∈ dist_points(p1,p2) | plane_from_points(p1,p2,p3) | dist_point_plane(point,p1,p2,p3) | foot_image_point_plane(point,normal,plane_point) | angle_line_plane(p1,p2,normal) | angle_between_planes(normal,normal2) | dist_skew_lines(p1,p2,p3,p4) | dist_point_line3d(point,p1,p2). Points are [x,y,z].",
     "parameters": {"type": "OBJECT", "properties": {
         "mode": {"type": "STRING"}, "p1": {"type": "ARRAY", "items": {"type": "NUMBER"}},
         "p2": {"type": "ARRAY", "items": {"type": "NUMBER"}}, "p3": {"type": "ARRAY", "items": {"type": "NUMBER"}},
         "p4": {"type": "ARRAY", "items": {"type": "NUMBER"}}, "point": {"type": "ARRAY", "items": {"type": "NUMBER"}},
         "normal": {"type": "ARRAY", "items": {"type": "NUMBER"}}, "normal2": {"type": "ARRAY", "items": {"type": "NUMBER"}},
         "plane_point": {"type": "ARRAY", "items": {"type": "NUMBER"}}}, "required": ["mode"]}},
]

# ------------------------------------------------------------------ prompts
NUMERICAL_SYS = """You are **JEE Tutor**, an elite coach for IIT-JEE **Advanced** Physics, Chemistry and Mathematics (India). You are in NUMERICAL-SOLVER mode.

## Phase 1 — Plan & Compute (tool calls)
Understand the problem completely (attachments may contain scanned questions). Call the provided tools to perform EVERY real computation — algebra, calculus, numerics, unit conversions, physics/chemistry formulas, plots. Use `python_exec` for multi-step problems, iteration, or verification (numpy/scipy/sympy preloaded; print results). Never trust mental arithmetic. If data seems missing, adopt the standard JEE assumption and state it. You may call several tools in sequence; verify surprising results with a second method.

## Phase 2 — Write the final solution (after tool results return)
Exam-style, in markdown with LaTeX ($inline$, $$display$$):
### 📋 Setup
**Given / To find** — with symbols and units.
### 🧠 Concept
The principle/theorem used + governing formula(s) in display math.
### ✍️ Solution
Numbered steps. Each step: the equation, the substitution, and a one-line justification. Reference which tool verified a step when relevant.
### ✅ Final Answer
**\\boxed{...}** with proper units, 3–4 significant figures.
### ⚡ Pitfalls & Tips
2–3 bullets: sign conventions, traps, shortcut, JEE-relevant remark.

**Rules:** SI units unless stated; g = 9.8 m/s² unless the problem says otherwise; explicit sign conventions (optics, electrostatics, rotation); if a sketch/graph helps, call `plot_graph`; be rigorous but concise; answer the exact question asked."""

DIAGRAM_SYS = """You are an expert scientific illustrator for IIT-JEE Advanced. Produce a precise, publication-quality educational diagram for the request.

Return STRICT JSON only (no markdown fence, no commentary):
{"kind":"svg"|"3d", "title":"...", "explanation":"2-4 sentences (markdown+LaTeX ok) explaining the diagram", "svg":"<svg ...>...</svg>", "scene":{...}}

**kind="svg"** → include "svg", omit "scene".
SVG rules: complete standalone `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 560" font-family="Segoe UI, Arial, sans-serif">`. Dark-theme friendly: NO background rect (transparent), strokes `#e8ecf8` (2px), accent palette #6ea8ff #ffd166 #4ade80 #f87171 #c084fc. Every quantity labeled with its symbol+value; leader lines; arrowheads via <defs><marker id="arr" ...>; dashed reference lines; angle arcs with degree labels; coordinate axes where relevant; a small title text top-left; unit annotations. Physics: force vectors from application point, v/ω labels, hatched ground (pattern), pulleys as circles, springs as zig-zag polylines. Chemistry: proper geometry (bond angles, lone pairs as dots), apparatus with labels. Math: accurate curves (use many small line segments or path Q/C commands), shaded regions with fill-opacity. NO <script>, NO external images, NO CSS animations.

**kind="3d"** → include "scene", omit "svg". Use for: molecular geometry (VSEPR), 3D optics, field/flux through surfaces, rotational mechanics in 3D, crystal structures, orbitals, solid geometry (tetrahedron distances etc.).
scene = {"background":"#0b0e1a", "axes":true, "grid":true, "camera_hint":"auto-rotate slowly", "objects":[...]} with coordinates in SI-like units, **y axis up**. Object types:
{"type":"sphere","pos":[x,y,z],"r":0.5,"color":"#4f8cff","opacity":1.0}
{"type":"box","pos":[x,y,z],"size":[w,h,d],"rotation":[rx,ry,rz],"color":"#...","opacity":1.0}   (rotation in radians, optional)
{"type":"cylinder","from":[x,y,z],"to":[x,y,z],"r":0.08,"color":"#..."}
{"type":"arrow","from":[x,y,z],"to":[x,y,z],"color":"#...","label":"F = 10 N"}
{"type":"line","points":[[x,y,z],[x,y,z],[...]],"color":"#...","dashed":false}
{"type":"label","pos":[x,y,z],"text":"m = 2 kg"}
{"type":"plane","pos":[0,0,0],"normal":[0,1,0],"size":8,"color":"#1e2438","opacity":0.6}
{"type":"cone","from":[x,y,z],"to":[x,y,z],"r":0.3,"color":"#..."}
Choose whichever kind communicates best; default to svg for 2D problems."""

ANIM_SYS = """You are an expert physics/chemistry/math ANIMATOR creating a beautiful, physically-correct animation for a JEE-Advanced student.

Return STRICT JSON only (no markdown fence):
{"title":"...", "explanation":"2-4 sentences describing what the animation shows (markdown ok)", "html":"<!DOCTYPE html> ... </html>"}

HTML rules (CRITICAL):
- ONE self-contained file. Inline CSS/JS ONLY. NO external resources, NO CDN, NO imports, NO fetch.
- Dark theme background #0b0e1a, light text #e8ecf8, accents #6ea8ff #ffd166 #4ade80 #f87171.
- body{margin:0}. A slim header bar with the title, the animation filling the viewport, and a one-line caption/legend at the bottom.
- Smooth 60fps: requestAnimationFrame loop; animation should run ~8-20s then loop cleanly.
- Include minimal controls: play/pause button and (if useful) a speed slider. Style them subtle.
- 2D → use <canvas> or SVG. 3D → window.THREE (three.js r128) is ALREADY LOADED as a global; create scene/camera/renderer yourself, add AmbientLight+DirectionalLight, and use the helper `new SimpleOrbit(camera, renderer.domElement)` (ALREADY LOADED globally — call orbit.update() each frame; supports drag-rotate + wheel-zoom); handle window resize.
- Show the governing formula(s) as HTML text (Unicode math: θ ω √ ² ³ ∫ Σ π Δ → no LaTeX libraries).
- Physical correctness matters: correct relative scales, trajectories (e.g. parabolas, SHM sine), vector directions, color-coded quantities with a legend.
- Code quality: no syntax errors, all variables defined, test your logic mentally."""

VIDEO_SYS = """You are a Manim Community Edition expert producing a JEE-Advanced educational video.

Return STRICT JSON only (no markdown fence):
{"title":"...", "caption":"1-2 sentences about the video", "manim_code":"<complete python code>"}

Manim rules:
{latex_line}
- EXACTLY ONE scene class subclassing Scene / ThreeDScene / MovingCameraScene, named descriptively (e.g. class ProjectileDemo(Scene)). construct(self) plays the whole video.
- 20–60 seconds of content: intro title → concept/formula → worked numeric example with numbers → key takeaway. Use self.wait(0.5-1) between ideas, run_time=1-2 per play.
- Allowed imports: from manim import *, numpy, math. FORBIDDEN: os, sys, subprocess, input(), random, file I/O, external images, SVGMobject.
- Use MathTex(r"...") for equations (double-escape backslashes in JSON), Text() for words, Create/Write/Transform/FadeIn/FadeOut/Indicate/Circumscribe, Axes/NumberPlane/plot for graphs, ValueTracker + always_redraw for dynamic values, SurroundingRectangle/Brace for emphasis. 3D: ThreeDAxes + set_camera_orientation(phi=..., theta=...).
- POSITION CONSTANTS: Manim CE has UR, UL, DR, DL, RIGHT, LEFT, UP, DOWN, ORIGIN — NOT UP_RIGHT/UP_LEFT/DOWN_RIGHT (those do not exist and crash). Use .to_corner(UR) / .to_edge(RIGHT) etc.
- Layout: nothing off-screen (854×480 default frame, font_size 24-44), no overlaps, everything self-contained and deterministic.
- Never call self.play with Mobject methods that don't exist; keep each self.play on animation primitives only."""

CAPABILITIES_NOTE = """Attachments may be present above (as [Attached file: ...] text or inline images) — read images carefully; they may contain the actual question."""


def video_system_prompt() -> str:
    if config.latex_available():
        latex_line = "- LaTeX IS installed on the render server: use MathTex(r\"...\") / Tex() freely for all equations."
    else:
        latex_line = "- LaTeX is NOT available: DO NOT use MathTex/Tex — they will crash the render. Use Text() with Unicode math (∫ Σ √ π θ ω × ² ³ ½ ⇒)."
    return VIDEO_SYS.replace("{latex_line}", latex_line)
