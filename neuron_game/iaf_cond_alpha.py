import numpy as np

DEFAULT_PARAMS = {
    "C_m": 250.0,
    "E_L": -70.0,
    "g_L": 16.667,
    "I_e": 0.0,
    "t_ref": 1.0,
    "tau_syn_ex": 0.2,
    "tau_syn_in": 2.0,
    "E_ex": 0.0,
    "E_in": -85.0,
    "V_m": -70.0,
    "V_reset": -80.0,
    "V_th": -50.0,
    "dt": 0.1,
}
RANGES = {
    "C_m": [200.0, 300.0],
    "E_L": [-75.0, -55.0],
    "g_L": [10, 20.0],
    "tau_syn_ex": [0.1, 1.1],
    "tau_syn_in": [1.0, 3.0],
    "E_ex": [0.0, 2.0],
    "E_in": [-90.0, -75.0],
    "V_reset": [-85.0, -65.0],
    "V_th": [-50.0, -30.0],
}


class IAFCondAlpha:
    def __init__(self, params: dict = None):
        params = params or {}

        new_params = DEFAULT_PARAMS.copy()
        new_params.update(params)
        self._test_params(new_params)
        for param in DEFAULT_PARAMS:
            self.__setattr__(param, new_params[param])
        self.pse_factor = np.exp(1) / self.tau_syn_ex
        self.psi_factor = np.exp(1) / self.tau_syn_in
        self.refractory = 0

    def init_buffers(self, max_delay):
        self.size_buffer = int(max_delay / self.dt + 1)
        self.buffer_spikes_exc = np.zeros(self.size_buffer)
        self.buffer_spikes_inh = np.zeros(self.size_buffer)
        self.neuron_state = np.zeros(4)  # dg_ex, dg_in, g_ex, g_in

    def _test_params(self, params: dict):
        assert params["C_m"] > 0.0
        assert params["g_L"] > 0.0
        assert params["dt"] > 0.0
        assert params["t_ref"] >= params["dt"]
        assert params["tau_syn_ex"] > 0.0
        assert params["tau_syn_in"] > 0.0

    def update_v_m(self):
        tau = self.C_m / self.g_L
        return (-self.V_m + self.E_L + (-self.I_syn + self.I_e) / self.g_L) / tau

    def update_i_syn(self, input_exc, input_inh):
        self.neuron_state[0] += input_exc * self.pse_factor
        self.neuron_state[1] += input_inh * self.psi_factor
        I_syn = self.neuron_state[2] * (self.V_m - self.E_ex) + self.neuron_state[3] * (
            self.V_m - self.E_in
        )
        self.neuron_state[0] -= self.neuron_state[0] / self.tau_syn_ex * self.dt
        self.neuron_state[1] -= self.neuron_state[1] / self.tau_syn_in * self.dt
        self.neuron_state[2] += (
            self.neuron_state[0] - self.neuron_state[2] / self.tau_syn_ex
        ) * self.dt
        self.neuron_state[3] += (
            self.neuron_state[1] - self.neuron_state[3] / self.tau_syn_in
        ) * self.dt
        return I_syn

    def update(self, t):
        spiked = False
        buffer_idx = int(t / self.dt) % self.size_buffer
        self.I_syn = self.update_i_syn(
            self.buffer_spikes_exc[buffer_idx], self.buffer_spikes_inh[buffer_idx]
        )
        self.V_m += self.update_v_m() * self.dt
        if self.refractory > 0:
            self.V_m = self.V_reset
            self.refractory -= 1
        elif self.V_m >= self.V_th:
            self.refractory = self.t_ref / self.dt
            spiked = True
        self.buffer_spikes_inh[buffer_idx] = 0
        self.buffer_spikes_exc[buffer_idx] = 0

        return spiked

    def receive_spike(self, t, weight, delay):
        buffer_idx = int((t + delay) / self.dt) % self.size_buffer
        if weight > 0:
            self.buffer_spikes_exc[buffer_idx] += weight
        else:
            self.buffer_spikes_inh[buffer_idx] -= weight

    def get_params(self):
        return {
            "C_m": self.C_m,
            "E_L": self.E_L,
            "g_L": self.g_L,
            "tau_syn_ex": self.tau_syn_ex,
            "tau_syn_in": self.tau_syn_in,
            "E_ex": self.E_ex,
            "E_in": self.E_in,
            "V_reset": self.V_reset,
            "V_th": self.V_th,
        }
