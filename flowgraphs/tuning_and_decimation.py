#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: Tuning and Decimation
# Author: GNU Radio Intro Workshop
# Description: Select one of three 'stations', shift it to 0 Hz, filter and decimate
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




class tuning_and_decimation(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "Tuning and Decimation", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("Tuning and Decimation")
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

        self.settings = Qt.QSettings("gnuradio/flowgraphs", "tuning_and_decimation")

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
        self.tune = tune = 20000
        self.samp_rate = samp_rate = 192000
        self.decim = decim = 4

        ##################################################
        # Blocks
        ##################################################

        self._tune_range = qtgui.Range(-96000, 96000, 500, 20000, 200)
        self._tune_win = qtgui.RangeWidget(self._tune_range, self.set_tune, "Tune to (Hz)", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._tune_win, 0, 0, 1, 2)
        for r in range(0, 1):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.xlate_sink = qtgui.freq_sink_c(
            2048, #size
            window.WIN_BLACKMAN_hARRIS, #wintype
            0, #fc
            (samp_rate/decim), #bw
            "Frequency Xlating FIR Filter output (48 kS/s)", #name
            1,
            None # parent
        )
        self.xlate_sink.set_update_time(0.10)
        self.xlate_sink.set_y_axis((-120), 10)
        self.xlate_sink.set_y_label('Relative Gain', 'dB')
        self.xlate_sink.set_trigger_mode(qtgui.TRIG_MODE_FREE, 0.0, 0, "")
        self.xlate_sink.enable_autoscale(False)
        self.xlate_sink.enable_grid(False)
        self.xlate_sink.set_fft_average(1.0)
        self.xlate_sink.enable_axis_labels(True)
        self.xlate_sink.enable_control_panel(False)
        self.xlate_sink.set_fft_window_normalized(False)



        labels = ['', '', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
            "magenta", "yellow", "dark red", "dark green", "dark blue"]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.xlate_sink.set_line_label(i, "Data {0}".format(i))
            else:
                self.xlate_sink.set_line_label(i, labels[i])
            self.xlate_sink.set_line_width(i, widths[i])
            self.xlate_sink.set_line_color(i, colors[i])
            self.xlate_sink.set_line_alpha(i, alphas[i])

        self._xlate_sink_win = sip.wrapinstance(self.xlate_sink.qwidget(), Qt.QWidget)
        self.top_grid_layout.addWidget(self._xlate_sink_win, 2, 1, 1, 1)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.xlate = filter.freq_xlating_fir_filter_ccc(decim, firdes.low_pass(1.0, samp_rate, 10e3, 5e3), tune, samp_rate)
        self.throttle = blocks.throttle( gr.sizeof_gr_complex*1, samp_rate, True, 0 if "auto" == "auto" else max( int(float(0.1) * samp_rate) if "auto" == "time" else int(0.1), 1) )
        self.station_c = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, 55000, 0.25, 0, 0)
        self.station_b = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, 20000, 1.0, 0, 0)
        self.station_a = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, (-60000), 0.5, 0, 0)
        self.noise = analog.noise_source_c(analog.GR_GAUSSIAN, 0.05, 0)
        self.mixer = blocks.multiply_vcc(1)
        self.manual_sink = qtgui.freq_sink_c(
            2048, #size
            window.WIN_BLACKMAN_hARRIS, #wintype
            0, #fc
            (samp_rate/decim), #bw
            "Multiply + Low Pass Filter output (48 kS/s)", #name
            1,
            None # parent
        )
        self.manual_sink.set_update_time(0.10)
        self.manual_sink.set_y_axis((-120), 10)
        self.manual_sink.set_y_label('Relative Gain', 'dB')
        self.manual_sink.set_trigger_mode(qtgui.TRIG_MODE_FREE, 0.0, 0, "")
        self.manual_sink.enable_autoscale(False)
        self.manual_sink.enable_grid(False)
        self.manual_sink.set_fft_average(1.0)
        self.manual_sink.enable_axis_labels(True)
        self.manual_sink.enable_control_panel(False)
        self.manual_sink.set_fft_window_normalized(False)



        labels = ['', '', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
            "magenta", "yellow", "dark red", "dark green", "dark blue"]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.manual_sink.set_line_label(i, "Data {0}".format(i))
            else:
                self.manual_sink.set_line_label(i, labels[i])
            self.manual_sink.set_line_width(i, widths[i])
            self.manual_sink.set_line_color(i, colors[i])
            self.manual_sink.set_line_alpha(i, alphas[i])

        self._manual_sink_win = sip.wrapinstance(self.manual_sink.qwidget(), Qt.QWidget)
        self.top_grid_layout.addWidget(self._manual_sink_win, 2, 0, 1, 1)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.lpf = filter.fir_filter_ccf(
            decim,
            firdes.low_pass(
                1,
                samp_rate,
                10000,
                5000,
                window.WIN_HAMMING,
                6.76))
        self.lo = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, (-tune), 1, 0, 0)
        self.band_sink = qtgui.freq_sink_c(
            2048, #size
            window.WIN_BLACKMAN_hARRIS, #wintype
            0, #fc
            samp_rate, #bw
            "The whole band (192 kS/s)", #name
            1,
            None # parent
        )
        self.band_sink.set_update_time(0.10)
        self.band_sink.set_y_axis((-120), 10)
        self.band_sink.set_y_label('Relative Gain', 'dB')
        self.band_sink.set_trigger_mode(qtgui.TRIG_MODE_FREE, 0.0, 0, "")
        self.band_sink.enable_autoscale(False)
        self.band_sink.enable_grid(False)
        self.band_sink.set_fft_average(1.0)
        self.band_sink.enable_axis_labels(True)
        self.band_sink.enable_control_panel(False)
        self.band_sink.set_fft_window_normalized(False)



        labels = ['', '', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
            "magenta", "yellow", "dark red", "dark green", "dark blue"]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.band_sink.set_line_label(i, "Data {0}".format(i))
            else:
                self.band_sink.set_line_label(i, labels[i])
            self.band_sink.set_line_width(i, widths[i])
            self.band_sink.set_line_color(i, colors[i])
            self.band_sink.set_line_alpha(i, alphas[i])

        self._band_sink_win = sip.wrapinstance(self.band_sink.qwidget(), Qt.QWidget)
        self.top_grid_layout.addWidget(self._band_sink_win, 1, 0, 1, 2)
        for r in range(1, 2):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.band = blocks.add_vcc(1)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.band, 0), (self.throttle, 0))
        self.connect((self.lo, 0), (self.mixer, 1))
        self.connect((self.lpf, 0), (self.manual_sink, 0))
        self.connect((self.mixer, 0), (self.lpf, 0))
        self.connect((self.noise, 0), (self.band, 3))
        self.connect((self.station_a, 0), (self.band, 0))
        self.connect((self.station_b, 0), (self.band, 1))
        self.connect((self.station_c, 0), (self.band, 2))
        self.connect((self.throttle, 0), (self.band_sink, 0))
        self.connect((self.throttle, 0), (self.mixer, 0))
        self.connect((self.throttle, 0), (self.xlate, 0))
        self.connect((self.xlate, 0), (self.xlate_sink, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("gnuradio/flowgraphs", "tuning_and_decimation")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_tune(self):
        return self.tune

    def set_tune(self, tune):
        self.tune = tune
        self.lo.set_frequency((-self.tune))
        self.xlate.set_center_freq(self.tune)

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.band_sink.set_frequency_range(0, self.samp_rate)
        self.lo.set_sampling_freq(self.samp_rate)
        self.lpf.set_taps(firdes.low_pass(1, self.samp_rate, 10000, 5000, window.WIN_HAMMING, 6.76))
        self.manual_sink.set_frequency_range(0, (self.samp_rate/self.decim))
        self.station_a.set_sampling_freq(self.samp_rate)
        self.station_b.set_sampling_freq(self.samp_rate)
        self.station_c.set_sampling_freq(self.samp_rate)
        self.throttle.set_sample_rate(self.samp_rate)
        self.xlate.set_taps(firdes.low_pass(1.0, self.samp_rate, 10e3, 5e3))
        self.xlate_sink.set_frequency_range(0, (self.samp_rate/self.decim))

    def get_decim(self):
        return self.decim

    def set_decim(self, decim):
        self.decim = decim
        self.manual_sink.set_frequency_range(0, (self.samp_rate/self.decim))
        self.xlate_sink.set_frequency_range(0, (self.samp_rate/self.decim))




def main(top_block_cls=tuning_and_decimation, options=None):

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
