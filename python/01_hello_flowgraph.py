#!/usr/bin/env python3
"""
A flowgraph written directly in Python

Signal Source -> Add (noise) -> Head -> Vector Sink

Head lets exactly N samples through and then tells the flowgraph it is done,
so tb.run() returns on its own.  Vector Sink keeps every sample in memory so
we can analyse the result with NumPy afterwards.

Run it:  python3 01_hello_flowgraph.py
"""
import numpy as np
from gnuradio import analog, blocks, gr


class hello_flowgraph(gr.top_block):
    def __init__(self, samp_rate=32000, freq=1000, num_samples=32000):
        gr.top_block.__init__(self, "Hello Flowgraph")
        self.samp_rate = samp_rate

        # Blocks
        self.src = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, freq, 1.0, 0)
        self.noise = analog.noise_source_c(analog.GR_GAUSSIAN, 0.1, 0)
        self.add = blocks.add_cc()
        self.head = blocks.head(gr.sizeof_gr_complex, num_samples)
        self.sink = blocks.vector_sink_c()

        # Connections: (block, port) -> (block, port)
        self.connect((self.src, 0), (self.add, 0))
        self.connect((self.noise, 0), (self.add, 1))
        self.connect(self.add, self.head, self.sink)   # shorthand for a simple chain


def main():
    tb = hello_flowgraph()
    tb.run()                      # start, wait for Head to finish, stop

    x = np.array(tb.sink.data())
    print(f"Collected {len(x)} complex samples")

    spectrum = np.abs(np.fft.fftshift(np.fft.fft(x)))
    freqs = np.fft.fftshift(np.fft.fftfreq(len(x), 1 / tb.samp_rate))
    peak = freqs[np.argmax(spectrum)]
    power_db = 10 * np.log10(np.mean(np.abs(x) ** 2))
    print(f"Strongest frequency: {peak:.1f} Hz")
    print(f"Average power: {power_db:.2f} dB (tone at 0 dB plus a little noise)")


if __name__ == "__main__":
    main()
