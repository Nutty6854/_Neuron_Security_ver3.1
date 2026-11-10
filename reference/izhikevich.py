"""Izhikevich (2003) spiking neuron driven by a time-varying current, and a fixed encoder layer.

Model (v in mV, t in ms):
    dv/dt = 0.04 v^2 + 5 v + 140 - u + I(t)
    du/dt = a (b v - u)
    if v >= v_peak:  v <- c,  u <- u + d

Forward Euler at step dt_ms; I(t) is given per step. Every call starts from v_init and
u = b * v_init, so no state carries over between inputs. Same equations and update order as
claude_izhikevich/izhikevich.py; the only change is that the current varies with time.
"""

from __future__ import annotations

import math
import random


def simulate(currents, neuron, dt_ms, record_trace=False):
    """Simulate one neuron under a current waveform (one value per step).

    Returns spike times (ms), final v and u, and optionally the membrane trace
    (one value per step, clipped to v_peak at spikes).
    """
    a = neuron["a"]
    b = neuron["b"]
    c = neuron["c"]
    d = neuron["d"]
    v_peak = neuron["v_peak"]

    v = neuron["v_init"]
    u = b * v
    spike_times = []
    trace = [] if record_trace else None

    for k, current in enumerate(currents):
        v += dt_ms * (0.04 * v * v + 5.0 * v + 140.0 - u + current)
        u += dt_ms * a * (b * v - u)
        if v >= v_peak:
            spike_times.append((k + 1) * dt_ms)
            if trace is not None:
                trace.append(v_peak)
            v = c
            u += d
        elif trace is not None:
            trace.append(v)

    if not (math.isfinite(v) and math.isfinite(u)):
        raise FloatingPointError(f"Izhikevich state diverged: v={v}, u={u}")

    return {"spike_times_ms": spike_times, "v_final": v, "u_final": u, "trace": trace}


def bin_counts(spike_times_ms, bin_ms, n_bins):
    """Spike counts in consecutive bins [k*bin_ms, (k+1)*bin_ms); a spike at the very end goes to the last bin."""
    counts = [0] * n_bins
    for t in spike_times_ms:
        k = min(int(t // bin_ms), n_bins - 1)
        counts[k] += 1
    return counts


class FixedEncoder:
    """Signal I(t) -> per-neuron current -> Izhikevich neurons -> binned spike counts.

    Gains and biases are drawn once from a seed and never trained.
    current_j(t) = clamp(gain_j * I(t) + bias_j, current_min, current_max)
    features     = [count_{j,k} / count_scale for j in neurons for k in bins]   (neuron-major)
    """

    def __init__(self, gains, biases, current_min, current_max, count_scale,
                 neuron, dt_ms, bin_ms, n_bins):
        self.gains = gains
        self.biases = biases
        self.current_min = current_min
        self.current_max = current_max
        self.count_scale = count_scale
        self.neuron = neuron
        self.dt_ms = dt_ms
        self.bin_ms = bin_ms
        self.n_bins = n_bins

    @classmethod
    def from_seed(cls, cfg, seed):
        enc = cfg["encoder"]
        rng = random.Random(seed)
        gains = [rng.uniform(enc["gain_min"], enc["gain_max"]) for _ in range(enc["n_neurons"])]
        biases = [rng.uniform(-enc["bias_range"], enc["bias_range"]) for _ in range(enc["n_neurons"])]
        return cls(gains, biases, enc["current_min"], enc["current_max"], enc["count_scale"],
                   dict(cfg["neuron"]), cfg["simulation"]["dt_ms"], enc["bin_ms"], enc["n_bins"])

    @property
    def n_neurons(self):
        return len(self.gains)

    @property
    def n_features(self):
        return self.n_neurons * self.n_bins

    def neuron_currents(self, signal, j):
        g, b = self.gains[j], self.biases[j]
        lo, hi = self.current_min, self.current_max
        return [min(hi, max(lo, g * s + b)) for s in signal]

    def clamped_fraction(self, signal):
        """Fraction of (neuron, step) currents that hit the clamp. Recorded, not used for training."""
        hit = 0
        for g, b in zip(self.gains, self.biases):
            for s in signal:
                i = g * s + b
                if i < self.current_min or i > self.current_max:
                    hit += 1
        return hit / (len(signal) * self.n_neurons)

    def spike_counts(self, signal):
        """counts[j][k]: spikes of neuron j in bin k."""
        expected = self.bin_ms * self.n_bins
        got = len(signal) * self.dt_ms
        if abs(got - expected) > 1e-9:
            raise ValueError(f"signal length {got} ms does not match bins {expected} ms")
        return [bin_counts(simulate(self.neuron_currents(signal, j), self.neuron, self.dt_ms)["spike_times_ms"],
                           self.bin_ms, self.n_bins)
                for j in range(self.n_neurons)]

    def encode_counts(self, counts):
        return [c / self.count_scale for row in counts for c in row]

    def encode(self, signal):
        return self.encode_counts(self.spike_counts(signal))

    def to_dict(self):
        return {
            "gains": self.gains,
            "biases": self.biases,
            "current_min": self.current_min,
            "current_max": self.current_max,
            "count_scale": self.count_scale,
            "neuron": self.neuron,
            "dt_ms": self.dt_ms,
            "bin_ms": self.bin_ms,
            "n_bins": self.n_bins,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(d["gains"], d["biases"], d["current_min"], d["current_max"], d["count_scale"],
                   d["neuron"], d["dt_ms"], d["bin_ms"], d["n_bins"])
