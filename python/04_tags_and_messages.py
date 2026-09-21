#!/usr/bin/env python3
"""
Stream tags and messages.

A threshold detector watches the signal level.  When the level rises above
the threshold it
  * attaches a stream tag to that exact sample ("burst_start"), and
  * publishes a message on its "detections" message port.

Vector Source (quiet, loud burst, quiet, loud burst)
    -> threshold_detector -> Tag Debug      (prints the tags it sees)
                          \\-> Message Debug (prints the messages)

Run it:  python3 04_tags_and_messages.py
"""
import numpy as np
import pmt
from gnuradio import blocks, gr


class threshold_detector(gr.sync_block):
    """Pass samples through; tag and announce every rising edge above `threshold`."""

    def __init__(self, threshold=0.5):
        gr.sync_block.__init__(self, name="Threshold Detector",
                               in_sig=[np.float32], out_sig=[np.float32])
        self.threshold = threshold
        self.above = False
        self.message_port_register_out(pmt.intern("detections"))

    def work(self, input_items, output_items):
        x = input_items[0]
        output_items[0][:] = x
        above = np.abs(x) > self.threshold
        # rising edges: above now, not above on the previous sample
        prev = np.concatenate(([self.above], above[:-1]))
        for i in np.flatnonzero(above & ~prev):
            offset = self.nitems_written(0) + i          # absolute sample number
            self.add_item_tag(0, offset, pmt.intern("burst_start"), pmt.from_double(float(x[i])))
            msg = pmt.dict_add(pmt.make_dict(), pmt.intern("sample"), pmt.from_uint64(int(offset)))
            self.message_port_pub(pmt.intern("detections"), msg)
        if len(x):
            self.above = bool(above[-1])
        return len(x)


class tags_and_messages(gr.top_block):
    def __init__(self):
        gr.top_block.__init__(self, "Tags and Messages")
        quiet, loud = [0.01] * 1000, [0.9] * 200
        self.src = blocks.vector_source_f(quiet + loud + quiet + loud + quiet)
        self.detector = threshold_detector(0.5)
        self.tag_debug = blocks.tag_debug(gr.sizeof_float, "tags seen downstream", "")
        self.msg_debug = blocks.message_debug()
        self.connect(self.src, self.detector, self.tag_debug)
        self.msg_connect((self.detector, "detections"), (self.msg_debug, "print"))


if __name__ == "__main__":
    tb = tags_and_messages()
    tb.run()
