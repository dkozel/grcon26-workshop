#!/usr/bin/env python3
"""
Custom Python blocks, and how to test them.

  dc_offset_ff        a sync block      (1 output sample per input sample)
  moving_average_ff   a decim block     (1 output sample per N input samples)

The tests at the bottom use GNU Radio's unittest helpers the same way the QA
files made by gr_modtool do: feed known data in with a Vector Source, collect
the output with a Vector Sink, and compare with what you expect.

Run the tests:  python3 03_custom_blocks.py
"""
import numpy as np
from gnuradio import blocks, gr, gr_unittest


class dc_offset_ff(gr.sync_block):
    """Add a constant to every sample (same code as the Embedded Python Block)."""

    def __init__(self, dc_offset=0.5):
        gr.sync_block.__init__(self, name="DC Offset", in_sig=[np.float32], out_sig=[np.float32])
        self.dc_offset = dc_offset

    def work(self, input_items, output_items):
        output_items[0][:] = input_items[0] + self.dc_offset
        return len(output_items[0])


class moving_average_ff(gr.decim_block):
    """Average each group of `decimation` input samples into one output sample."""

    def __init__(self, decimation=4):
        gr.decim_block.__init__(self, name="Moving Average Decimator",
                                in_sig=[np.float32], out_sig=[np.float32], decim=decimation)
        self.decimation = decimation

    def work(self, input_items, output_items):
        out = output_items[0]
        # GNU Radio guarantees len(input) == len(out) * decimation for a decim_block
        groups = input_items[0][:len(out) * self.decimation].reshape(len(out), self.decimation)
        out[:] = groups.mean(axis=1)
        return len(out)


class qa_custom_blocks(gr_unittest.TestCase):

    def setUp(self):
        self.tb = gr.top_block()

    def tearDown(self):
        self.tb = None

    def test_001_dc_offset(self):
        src_data = (0, 1, -2, 5.5, -0.5)
        expected = (0.5, 1.5, -1.5, 6.0, 0.0)
        src = blocks.vector_source_f(src_data)
        blk = dc_offset_ff(0.5)
        snk = blocks.vector_sink_f()
        self.tb.connect(src, blk, snk)
        self.tb.run()
        self.assertFloatTuplesAlmostEqual(expected, snk.data(), 6)

    def test_002_moving_average(self):
        src_data = (1, 1, 1, 1, 2, 4, 6, 8, 0, 0, 0, -4)
        expected = (1.0, 5.0, -1.0)
        src = blocks.vector_source_f(src_data)
        blk = moving_average_ff(4)
        snk = blocks.vector_sink_f()
        self.tb.connect(src, blk, snk)
        self.tb.run()
        self.assertFloatTuplesAlmostEqual(expected, snk.data(), 6)

    def test_003_long_input(self):
        # Much more data than fits in one call to work(): the scheduler will
        # call work() many times with chunks of varying size.
        n = 100_000
        src_data = np.arange(n, dtype=np.float32) % 8
        src = blocks.vector_source_f(src_data.tolist())
        blk = moving_average_ff(8)
        snk = blocks.vector_sink_f()
        self.tb.connect(src, blk, snk)
        self.tb.run()
        self.assertEqual(len(snk.data()), n // 8)
        self.assertFloatTuplesAlmostEqual([3.5] * (n // 8), snk.data(), 5)


if __name__ == "__main__":
    gr_unittest.run(qa_custom_blocks, verbosity=2)
