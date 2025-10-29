#!/usr/bin/env python3
# SpotMicro IK (super simple) — degrees, 3 floats only
# Convention: omega matches your reference (front-right leg):
#   0° = arm in sagittal plane (forward/back), 90° = arm straight out to the side.
# Prints: "omega theta phi" (space-separated), rounded to 3 decimals.
#
# Usage: python3 spotmicro_ik_simple.py X Y Z
import sys, math
from dataclasses import dataclass


@dataclass
class Params:
    L1: float = 110.0
    L2: float = 130.0
    x_off: float = 28.5
    y_off: float = 10.0
    z_off: float = 60.4  # set from your CAD


def hip_pos(w, p):
    return (
        p.x_off,
        p.y_off * math.cos(w) - p.z_off * math.sin(w),
        p.y_off * math.sin(w) + p.z_off * math.cos(w),
    )


def vz_residual(w, X, Y, Z, p):
    _, p2y, p2z = hip_pos(w, p)
    dy = Y - p2y
    dz = Z - p2z
    return -math.sin(w) * dy + math.cos(w) * dz  # z' after R_x(-w)


def solve_omega(X, Y, Z, p):
    # bracket roots on [-pi, pi], bisection refine; choose near 0 by default
    roots = []
    N = 720
    w_prev = -math.pi
    f_prev = vz_residual(w_prev, X, Y, Z, p)
    for k in range(1, N + 1):
        w = -math.pi + 2 * math.pi * k / N
        f = vz_residual(w, X, Y, Z, p)
        if f_prev * f <= 0.0:
            a, b = w_prev, w
            fa, fb = f_prev, f
            for _ in range(50):
                m = 0.5 * (a + b)
                fm = vz_residual(m, X, Y, Z, p)
                if fa * fm <= 0.0:
                    b, fb = m, fm
                else:
                    a, fa = m, fm
            roots.append(0.5 * (a + b))
        w_prev, f_prev = w, f
    if not roots:
        # Newton fallback
        w = 0.0
        for _ in range(80):
            f = vz_residual(w, X, Y, Z, p)
            h = 1e-6
            fp = (vz_residual(w + h, X, Y, Z, p) - vz_residual(w - h, X, Y, Z, p)) / (
                2 * h
            )
            if abs(fp) < 1e-12:
                break
            step = f / fp
            w -= step
            if abs(step) < 1e-12:
                break
        return ((w + math.pi) % (2 * math.pi)) - math.pi
    # pick root closest to 0
    w = min(roots, key=lambda r: abs(((r + math.pi) % (2 * math.pi)) - math.pi))
    return ((w + math.pi) % (2 * math.pi)) - math.pi


def ik_simple_deg(X, Y, Z, p=Params()):
    # 1) solve omega in math radians
    w = solve_omega(X, Y, Z, p)
    # 2) hip and vector to foot
    p2x, p2y, p2z = hip_pos(w, p)
    dx = X - p2x
    dy = Y - p2y
    dz = Z - p2z
    # 3) rotate into leg plane
    dy_p = math.cos(w) * dy + math.sin(w) * dz
    dx_p = dx
    d = math.hypot(dx_p, dy_p)
    if d > (p.L1 + p.L2) + 1e-9 or d < abs(p.L1 - p.L2) - 1e-9:
        raise SystemExit("Unreachable")
    # 4) knee and hip pitch
    cos_phi = max(-1.0, min(1.0, (p.L1**2 + p.L2**2 - d**2) / (2 * p.L1 * p.L2)))
    phi = math.degrees(math.acos(cos_phi))
    alpha = math.atan2(dy_p, dx_p)
    cos_beta = max(-1.0, min(1.0, (p.L1**2 + d**2 - p.L2**2) / (2 * p.L1 * d)))
    beta = math.acos(cos_beta)
    theta_math = ((alpha - beta) + math.pi) % (2 * math.pi) - math.pi  # knee-down
    # Convert to YOUR convention: 0 = vertical down, 90 = horizontal back, 180 = vertical up
    theta = 90.0 - math.degrees(theta_math)
    # 5) omega (your convention for FR leg): mech = math + 90°
    omega_deg = math.degrees(((w + math.pi) % (2 * math.pi) - math.pi)) + 90.0
    return round(omega_deg, 3), round(theta, 3), round(phi, 3)


def main():
    if len(sys.argv) != 4:
        print("Usage: python3 spotmicro_ik_simple.py X Y Z", file=sys.stderr)
        raise SystemExit(2)
    X, Y, Z = map(float, sys.argv[1:4])
    om, th, ph = ik_simple_deg(X, Y, Z)
    print(f"{om} {th} {ph}")


if __name__ == "__main__":
    main()
