"""Plotting engine — matplotlib figures saved as SVG/PNG served from /media/plots/."""
import uuid
import numpy as np
import sympy as sp
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from config import MEDIA_DIR

plt.rcParams.update({
    "figure.facecolor": "#0d1020", "axes.facecolor": "#0d1020",
    "axes.edgecolor": "#8b93b8", "axes.labelcolor": "#e8ecf8",
    "xtick.color": "#aab2d0", "ytick.color": "#aab2d0",
    "grid.color": "#2a3050", "text.color": "#e8ecf8",
    "font.size": 12,
})
PALETTE = ["#6ea8ff", "#ffd166", "#4ade80", "#f87171", "#c084fc", "#22d3ee"]


def plot_graph(functions: list, x_min: float, x_max: float, title: str = "",
               x_label: str = "x", y_label: str = "y", x_points=None, y_points=None):
    """Plot 1..n functions of x. Returns dict with media URL."""
    x = sp.Symbol("x")
    fig, ax = plt.subplots(figsize=(8, 5))
    for i, f in enumerate(functions):
        expr = sp.sympify(str(f))
        fn = sp.lambdify(x, expr, modules=["numpy"])
        xs = np.linspace(float(x_min), float(x_max), 800)
        with np.errstate(all="ignore"):
            ys = fn(xs)
        ys = np.asarray(ys, dtype=float)
        ys = np.where(np.abs(ys) > 1e6, np.nan, ys)
        ax.plot(xs, ys, color=PALETTE[i % len(PALETTE)], linewidth=2.2, label=f"$y = {sp.latex(expr)}$")
    if x_points and y_points:
        ax.scatter([float(p) for p in x_points], [float(p) for p in y_points],
                   color="#ffd166", zorder=5, s=48, edgecolors="white", linewidths=0.8)
    ax.grid(True, alpha=0.5, linewidth=0.6)
    ax.axhline(0, color="#59628a", lw=0.8); ax.axvline(0, color="#59628a", lw=0.8)
    if len(functions) > 1:
        leg = ax.legend(facecolor="#151a30", edgecolor="#3a4270", labelcolor="white")
    if title:
        ax.set_title(title, fontsize=14, pad=12)
    ax.set_xlabel(x_label); ax.set_ylabel(y_label)
    fig.tight_layout()
    pid = uuid.uuid4().hex[:10]
    out = MEDIA_DIR / "plots" / f"{pid}.svg"
    fig.savefig(out, format="svg")
    plt.close(fig)
    return {"url": f"/media/plots/{pid}.svg", "kind": "image_svg", "title": title or "Graph"}


def plot_surface(function: str, x_min: float, x_max: float, y_min: float, y_max: float, title: str = ""):
    """3D surface z = f(x, y) as PNG."""
    xs_ = np.linspace(float(x_min), float(x_max), 90)
    ys_ = np.linspace(float(y_min), float(y_max), 90)
    X, Y = np.meshgrid(xs_, ys_)
    x, y = sp.symbols("x y")
    expr = sp.sympify(str(function))
    fn = sp.lambdify((x, y), expr, modules=["numpy"])
    with np.errstate(all="ignore"):
        Z = fn(X, Y)
    Z = np.asarray(Z, dtype=float)
    Z = np.where(np.abs(Z) > 1e6, np.nan, Z)
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection="3d")
    surf = ax.plot_surface(X, Y, Z, cmap="plasma", linewidth=0, antialiased=True, alpha=0.95)
    fig.colorbar(surf, shrink=0.6, pad=0.08)
    if title:
        ax.set_title(title)
    ax.set_xlabel("x"); ax.set_ylabel("y"); ax.set_zlabel("z")
    pid = uuid.uuid4().hex[:10]
    out = MEDIA_DIR / "plots" / f"{pid}.png"
    fig.savefig(out, format="png", dpi=140)
    plt.close(fig)
    return {"url": f"/media/plots/{pid}.png", "kind": "image_png", "title": title or "3D surface"}
