"""Safe execution tools: inline arithmetic calc + sandboxed python_exec (numpy/scipy/sympy)."""
import ast
import math
import subprocess
import sys
import tempfile
import os

_PREAMBLE = """\
import numpy as np, scipy, sympy as sp, math
from scipy import constants as const
from scipy.integrate import quad, solve_ivp
from scipy.optimize import fsolve, minimize
np.set_printoptions(precision=6, suppress=False)
"""


class _CalcEval(ast.NodeVisitor):
    ALLOWED_FUNCS = {
        "sin": math.sin, "cos": math.cos, "tan": math.tan, "asin": math.asin,
        "acos": math.acos, "atan": math.atan, "atan2": math.atan2, "sinh": math.sinh,
        "cosh": math.cosh, "tanh": math.tanh, "sqrt": math.sqrt, "cbrt": lambda x: x ** (1 / 3),
        "exp": math.exp, "log": math.log, "log2": math.log2, "log10": math.log10,
        "abs": abs, "round": round, "floor": math.floor, "ceil": math.ceil,
        "min": min, "max": max, "pow": pow, "hypot": math.hypot,
        "deg": math.degrees, "rad": math.radians, "degrees": math.degrees, "radians": math.radians,
        "fact": math.factorial, "factorial": math.factorial, "gcd": math.gcd,
    }
    ALLOWED_CONSTS = {"pi": math.pi, "e": math.e, "tau": math.tau, "inf": math.inf,
                      "g": 9.8, "c": 3e8, "h": 6.626e-34, "k": 1.381e-23, "NA": 6.022e23,
                      "q": 1.602e-19, "me": 9.11e-31, "mp": 1.673e-27, "R": 8.314, "F": 96485}

    def visit(self, node):
        if isinstance(node, ast.Expression):
            return self.visit(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod, ast.FloorDiv)):
            return {ast.Add: lambda a, b: a + b, ast.Sub: lambda a, b: a - b,
                    ast.Mult: lambda a, b: a * b, ast.Div: lambda a, b: a / b,
                    ast.Pow: lambda a, b: a ** b, ast.Mod: lambda a, b: a % b,
                    ast.FloorDiv: lambda a, b: a // b}[type(node.op)](self.visit(node.left), self.visit(node.right))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            v = self.visit(node.operand)
            return v if isinstance(node.op, ast.UAdd) else -v
        if isinstance(node, ast.Name) and node.id in self.ALLOWED_CONSTS:
            return self.ALLOWED_CONSTS[node.id]
        if isinstance(node, ast.Name) and node.id in self.ALLOWED_FUNCS:
            return self.ALLOWED_FUNCS[node.id]
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in self.ALLOWED_FUNCS:
            return self.ALLOWED_FUNCS[node.func.id](*[self.visit(a) for a in node.args])
        raise ValueError(f"Blocked in calc: {ast.dump(node)[:80]}. Use python_exec for advanced math.")


def calc(expression: str):
    expr = str(expression).strip().replace("^", "**")
    try:
        val = _CalcEval().visit(ast.parse(expr, mode="eval"))
        if isinstance(val, complex):
            return {"result": str(val)}
        out = {"result": val}
        if isinstance(val, float):
            out["result"] = round(val, 10)
            if abs(val) > 1e15 or (0 < abs(val) < 1e-6):
                out["scientific"] = f"{val:.6e}"
        return out
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"calc error: {e}")


_BANNED = ("os.", "sys.", "subprocess", "socket", "shutil", "requests", "urllib",
           "open(", "__import__", "eval(", "exec(", "input(", "pathlib", "importlib",
           "ctypes", "threading", "multiprocessing", "signal", "while True:")


def python_exec(code: str, timeout: int = 25):
    """Run short numeric python (numpy/scipy/sympy preloaded) in an isolated process."""
    code = str(code)
    for b in _BANNED:
        if b in code:
            return {"error": f"Blocked token '{b}' — compute-only sandbox (numpy/scipy/sympy available).",
                    "stdout": "", "value": None}
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w", encoding="utf-8") as f:
        f.write(_PREAMBLE + "\n" + code)
        path = f.name
    try:
        p = subprocess.run([sys.executable, path], capture_output=True, text=True, timeout=timeout)
        stdout = p.stdout[-4000:]
        stderr = p.stderr[-1500:]
        if p.returncode != 0:
            return {"error": stderr or "non-zero exit", "stdout": stdout}
        return {"stdout": stdout, "note": "Print results explicitly with print()."}
    except subprocess.TimeoutExpired:
        return {"error": f"Execution timed out after {timeout}s — simplify or vectorize with numpy."}
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass
