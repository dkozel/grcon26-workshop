#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: Exploring Waves
# Author: GNU Radio Intro Workshop
# Description: Two cosines with adjustable amplitude, frequency and phase
# GNU Radio version: 3.10.12.0

from PyQt5 import Qt
from gnuradio import qtgui
from PyQt5 import QtCore
from gnuradio import analog
from gnuradio import blocks
import numpy as np
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




class exploring_waves(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "Exploring Waves", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("Exploring Waves")
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

        self.settings = Qt.QSettings("gnuradio/flowgraphs", "exploring_waves")

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
        self.samp_rate = samp_rate = 32000
        self.ch2_phase = ch2_phase = 90
        self.ch2_freq = ch2_freq = 1000
        self.ch2_amp = ch2_amp = 1

        ##################################################
        # Blocks
        ##################################################

        self._ch2_phase_range = qtgui.Range(-180, 180, 5, 90, 200)
        self._ch2_phase_win = qtgui.RangeWidget(self._ch2_phase_range, self.set_ch2_phase, "Ch 2 phase (degrees)", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._ch2_phase_win, 2, 0, 1, 1)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._ch2_freq_range = qtgui.Range(0, 4000, 50, 1000, 200)
        self._ch2_freq_win = qtgui.RangeWidget(self._ch2_freq_range, self.set_ch2_freq, "Ch 2 frequency (Hz)", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._ch2_freq_win, 1, 0, 1, 1)
        for r in range(1, 2):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._ch2_amp_range = qtgui.Range(0, 2, 0.05, 1, 200)
        self._ch2_amp_win = qtgui.RangeWidget(self._ch2_amp_range, self.set_ch2_amp, "Ch 2 amplitude", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._ch2_amp_win, 0, 0, 1, 1)
        for r in range(0, 1):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.time_sink = qtgui.time_sink_f(
            128, #size
            samp_rate, #samp_rate
            "Channel 1, channel 2 and their sum", #name
            3, #number of inputs
            None # parent
        )
        self.time_sink.set_update_time(0.10)
        self.time_sink.set_y_axis(-3, 3)

        self.time_sink.set_y_label('Amplitude', "")

        self.time_sink.enable_tags(True)
        self.time_sink.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, 0, "")
        self.time_sink.enable_autoscale(False)
        self.time_sink.enable_grid(False)
        self.time_sink.enable_axis_labels(True)
        self.time_sink.enable_control_panel(False)
        self.time_sink.enable_stem_plot(False)


        labels = ["Ch 1", "Ch 2", "Sum", 'Signal 4', 'Signal 5',
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


        for i in range(3):
            if len(labels[i]) == 0:
                self.time_sink.set_line_label(i, "Data {0}".format(i))
            else:
                self.time_sink.set_line_label(i, labels[i])
            self.time_sink.set_line_width(i, widths[i])
            self.time_sink.set_line_color(i, colors[i])
            self.time_sink.set_line_style(i, styles[i])
            self.time_sink.set_line_marker(i, markers[i])
            self.time_sink.set_line_alpha(i, alphas[i])

        self._time_sink_win = sip.wrapinstance(self.time_sink.qwidget(), Qt.QWidget)
        self.top_grid_layout.addWidget(self._time_sink_win, 3, 0, 1, 1)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.sig_ch2 = analog.sig_source_f(samp_rate, analog.GR_COS_WAVE, ch2_freq, ch2_amp, 0, (ch2_phase * np.pi / 180))
        self.sig_ch1 = analog.sig_source_f(samp_rate, analog.GR_COS_WAVE, 1000, 1, 0, 0)
        self.freq_sink = qtgui.freq_sink_f(
            2048, #size
            window.WIN_BLACKMAN_hARRIS, #wintype
            0, #fc
            samp_rate, #bw
            "Spectrum of the sum", #name
            1,
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


        self.freq_sink.set_plot_pos_half(not True)

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
                self.freq_sink.set_line_label(i, "Data {0}".format(i))
            else:
                self.freq_sink.set_line_label(i, labels[i])
            self.freq_sink.set_line_width(i, widths[i])
            self.freq_sink.set_line_color(i, colors[i])
            self.freq_sink.set_line_alpha(i, alphas[i])

        self._freq_sink_win = sip.wrapinstance(self.freq_sink.qwidget(), Qt.QWidget)
        self.top_grid_layout.addWidget(self._freq_sink_win, 4, 0, 1, 1)
        for r in range(4, 5):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.blocks_throttle2_0 = blocks.throttle( gr.sizeof_float*1, samp_rate, True, 0 if "auto" == "auto" else max( int(float(0.1) * samp_rate) if "auto" == "time" else int(0.1), 1) )
        self.blocks_add_xx_0 = blocks.add_vff(1)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.blocks_add_xx_0, 0), (self.freq_sink, 0))
        self.connect((self.blocks_add_xx_0, 0), (self.time_sink, 2))
        self.connect((self.blocks_throttle2_0, 0), (self.blocks_add_xx_0, 0))
        self.connect((self.blocks_throttle2_0, 0), (self.time_sink, 0))
        self.connect((self.sig_ch1, 0), (self.blocks_throttle2_0, 0))
        self.connect((self.sig_ch2, 0), (self.blocks_add_xx_0, 1))
        self.connect((self.sig_ch2, 0), (self.time_sink, 1))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("gnuradio/flowgraphs", "exploring_waves")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.blocks_throttle2_0.set_sample_rate(self.samp_rate)
        self.freq_sink.set_frequency_range(0, self.samp_rate)
        self.sig_ch1.set_sampling_freq(self.samp_rate)
        self.sig_ch2.set_sampling_freq(self.samp_rate)
        self.time_sink.set_samp_rate(self.samp_rate)

    def get_ch2_phase(self):
        return self.ch2_phase

    def set_ch2_phase(self, ch2_phase):
        self.ch2_phase = ch2_phase
        self.sig_ch2.set_phase((self.ch2_phase * np.pi / 180))

    def get_ch2_freq(self):
        return self.ch2_freq

    def set_ch2_freq(self, ch2_freq):
        self.ch2_freq = ch2_freq
        self.sig_ch2.set_frequency(self.ch2_freq)

    def get_ch2_amp(self):
        return self.ch2_amp

    def set_ch2_amp(self, ch2_amp):
        self.ch2_amp = ch2_amp
        self.sig_ch2.set_amplitude(self.ch2_amp)




def main(top_block_cls=exploring_waves, options=None):

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
