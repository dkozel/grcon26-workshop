#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: Noise and Filtering
# Author: GNU Radio Intro Workshop
# Description: A tone in noise, cleaned up by a low-pass filter
# GNU Radio version: 3.10.12.0

from PyQt5 import Qt
from gnuradio import qtgui
from PyQt5 import QtCore
from gnuradio import analog
from gnuradio import blocks
from gnuradio import filter
from gnuradio.filter import firdes
import sip
import threading
from gnuradio import gr
from gnuradio.filter import firdes
from gnuradio.fft import window
import sys
import signal
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation




class noise_and_filtering(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "Noise and Filtering", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("Noise and Filtering")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except BaseException as exc:
            print(f"Qt GUI: Could not set Icon: {str(exc)}", file=sys.stderr)
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("gnuradio/flowgraphs", "noise_and_filtering")

        try:
            geometry = self.settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
        except BaseException as exc:
            print(f"Qt GUI: Could not restore geometry: {str(exc)}", file=sys.stderr)
        self.flowgraph_started = threading.Event()

        ##################################################
        # Variables
        ##################################################
        self.width = width = 1000
        self.samp_rate = samp_rate = 48000
        self.noise_amp = noise_amp = 0.2
        self.freq = freq = 2000
        self.cutoff = cutoff = 3000

        ##################################################
        # Blocks
        ##################################################

        self._width_range = qtgui.Range(100, 5000, 100, 1000, 200)
        self._width_win = qtgui.RangeWidget(self._width_range, self.set_width, "Transition width (Hz)", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._width_win, 1, 1, 1, 1)
        for r in range(1, 2):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._freq_range = qtgui.Range(-24000, 24000, 250, 2000, 200)
        self._freq_win = qtgui.RangeWidget(self._freq_range, self.set_freq, "Tone frequency (Hz)", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._freq_win, 0, 0, 1, 1)
        for r in range(0, 1):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._cutoff_range = qtgui.Range(500, 20000, 250, 3000, 200)
        self._cutoff_win = qtgui.RangeWidget(self._cutoff_range, self.set_cutoff, "Filter cutoff (Hz)", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._cutoff_win, 1, 0, 1, 1)
        for r in range(1, 2):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.time_sink = qtgui.time_sink_c(
            256, #size
            samp_rate, #samp_rate
            "Filtered signal", #name
            1, #number of inputs
            None # parent
        )
        self.time_sink.set_update_time(0.10)
        self.time_sink.set_y_axis(-2, 2)

        self.time_sink.set_y_label('Amplitude', "")

        self.time_sink.enable_tags(True)
        self.time_sink.set_trigger_mode(qtgui.TRIG_MODE_AUTO, qtgui.TRIG_SLOPE_POS, 0.0, 0, 0, "")
        self.time_sink.enable_autoscale(False)
        self.time_sink.enable_grid(False)
        self.time_sink.enable_axis_labels(True)
        self.time_sink.enable_control_panel(False)
        self.time_sink.enable_stem_plot(False)


        labels = ["I", "Q", 'Signal 3', 'Signal 4', 'Signal 5',
            'Signal 6', 'Signal 7', 'Signal 8', 'Signal 9', 'Signal 10']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ['blue', 'red', 'green', 'black', 'cyan',
            'magenta', 'yellow', 'dark red', 'dark green', 'dark blue']
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]
        styles = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        markers = [-1, -1, -1, -1, -1,
            -1, -1, -1, -1, -1]


        for i in range(2):
            if len(labels[i]) == 0:
                if (i % 2 == 0):
                    self.time_sink.set_line_label(i, "Re{{Data {0}}}".format(i/2))
                else:
                    self.time_sink.set_line_label(i, "Im{{Data {0}}}".format(i/2))
            else:
                self.time_sink.set_line_label(i, labels[i])
            self.time_sink.set_line_width(i, widths[i])
            self.time_sink.set_line_color(i, colors[i])
            self.time_sink.set_line_style(i, styles[i])
            self.time_sink.set_line_marker(i, markers[i])
            self.time_sink.set_line_alpha(i, alphas[i])

        self._time_sink_win = sip.wrapinstance(self.time_sink.qwidget(), Qt.QWidget)
        self.top_grid_layout.addWidget(self._time_sink_win, 3, 0, 1, 2)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.throttle = blocks.throttle( gr.sizeof_gr_complex*1, samp_rate, True, 0 if "auto" == "auto" else max( int(float(0.1) * samp_rate) if "auto" == "time" else int(0.1), 1) )
        self.sig = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, freq, 1, 0, 0)
        self._noise_amp_range = qtgui.Range(0, 1, 0.01, 0.2, 200)
        self._noise_amp_win = qtgui.RangeWidget(self._noise_amp_range, self.set_noise_amp, "Noise amplitude", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._noise_amp_win, 0, 1, 1, 1)
        for r in range(0, 1):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.noise = analog.noise_source_c(analog.GR_GAUSSIAN, noise_amp, 0)
        self.lpf = filter.fir_filter_ccf(
            1,
            firdes.low_pass(
                1,
                samp_rate,
                cutoff,
                width,
                window.WIN_HAMMING,
                6.76))
        self.freq_sink = qtgui.freq_sink_c(
            2048, #size
            window.WIN_BLACKMAN_hARRIS, #wintype
            0, #fc
            samp_rate, #bw
            "Before and after the low-pass filter", #name
            2,
            None # parent
        )
        self.freq_sink.set_update_time(0.10)
        self.freq_sink.set_y_axis((-120), 10)
        self.freq_sink.set_y_label('Relative Gain', 'dB')
        self.freq_sink.set_trigger_mode(qtgui.TRIG_MODE_FREE, 0.0, 0, "")
        self.freq_sink.enable_autoscale(False)
        self.freq_sink.enable_grid(False)
        self.freq_sink.set_fft_average(1.0)
        self.freq_sink.enable_axis_labels(True)
        self.freq_sink.enable_control_panel(False)
        self.freq_sink.set_fft_window_normalized(False)



        labels = ["Unfiltered", "Filtered", '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
            "magenta", "yellow", "dark red", "dark green", "dark blue"]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(2):
            if len(labels[i]) == 0:
                self.freq_sink.set_line_label(i, "Data {0}".format(i))
            else:
                self.freq_sink.set_line_label(i, labels[i])
            self.freq_sink.set_line_width(i, widths[i])
            self.freq_sink.set_line_color(i, colors[i])
            self.freq_sink.set_line_alpha(i, alphas[i])

        self._freq_sink_win = sip.wrapinstance(self.freq_sink.qwidget(), Qt.QWidget)
        self.top_grid_layout.addWidget(self._freq_sink_win, 2, 0, 1, 2)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.add = blocks.add_vcc(1)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.add, 0), (self.throttle, 0))
        self.connect((self.lpf, 0), (self.freq_sink, 1))
        self.connect((self.lpf, 0), (self.time_sink, 0))
        self.connect((self.noise, 0), (self.add, 1))
        self.connect((self.sig, 0), (self.add, 0))
        self.connect((self.throttle, 0), (self.freq_sink, 0))
        self.connect((self.throttle, 0), (self.lpf, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("gnuradio/flowgraphs", "noise_and_filtering")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_width(self):
        return self.width

    def set_width(self, width):
        self.width = width
        self.lpf.set_taps(firdes.low_pass(1, self.samp_rate, self.cutoff, self.width, window.WIN_HAMMING, 6.76))

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.freq_sink.set_frequency_range(0, self.samp_rate)
        self.lpf.set_taps(firdes.low_pass(1, self.samp_rate, self.cutoff, self.width, window.WIN_HAMMING, 6.76))
        self.sig.set_sampling_freq(self.samp_rate)
        self.throttle.set_sample_rate(self.samp_rate)
        self.time_sink.set_samp_rate(self.samp_rate)

    def get_noise_amp(self):
        return self.noise_amp

    def set_noise_amp(self, noise_amp):
        self.noise_amp = noise_amp
        self.noise.set_amplitude(self.noise_amp)

    def get_freq(self):
        return self.freq

    def set_freq(self, freq):
        self.freq = freq
        self.sig.set_frequency(self.freq)

    def get_cutoff(self):
        return self.cutoff

    def set_cutoff(self, cutoff):
        self.cutoff = cutoff
        self.lpf.set_taps(firdes.low_pass(1, self.samp_rate, self.cutoff, self.width, window.WIN_HAMMING, 6.76))




def main(top_block_cls=noise_and_filtering, options=None):

    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls()

    tb.start()
    tb.flowgraph_started.set()

    tb.show()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        Qt.QApplication.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    timer = Qt.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    qapp.exec_()

if __name__ == '__main__':
    main()
