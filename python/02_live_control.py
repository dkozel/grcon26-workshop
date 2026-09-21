#!/usr/bin/env python3
"""
Control a running flowgraph from Python.

tb.start() returns immediately and the flowgraph keeps running in background
threads.  While it runs we change the signal amplitude with a setter (exactly
what a GRC slider does) and read the measured power from a probe block.

Signal Source -> Throttle -> Probe Avg Mag^2

Run it:  python3 02_live_control.py
"""
import math
import time

from gnuradio import analog, blocks, gr


class live_control(gr.top_block):
    def __init__(self, samp_rate=48000):
        gr.top_block.__init__(self, "Live Control")
        self.samp_rate = samp_rate
        self.amplitude = 1.0

        self.src = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, 1000, self.amplitude, 0)
        self.throttle = blocks.throttle(gr.sizeof_gr_complex, samp_rate)
        # Measures the average of |x|^2; alpha sets how quickly it follows changes
        self.probe = analog.probe_avg_mag_sqrd_c(-100, 0.001)
        self.connect(self.src, self.throttle, self.probe)

    # GRC generates setters like this one for every variable
    def set_amplitude(self, amplitude):
        self.amplitude = amplitude
        self.src.set_amplitude(amplitude)


def main():
    tb = live_control()
    tb.start()                          # returns immediately
    try:
        for amp in (1.0, 0.5, 0.1, 0.01):
            tb.set_amplitude(amp)
            time.sleep(0.5)             # let the probe settle
            level = tb.probe.level()
            print(f"amplitude {amp:5.2f} -> measured power {10 * math.log10(level):7.2f} dB")
    finally:
        tb.stop()                       # ask every block to stop...
        tb.wait()                       # ...and wait until they have


if __name__ == "__main__":
    main()
