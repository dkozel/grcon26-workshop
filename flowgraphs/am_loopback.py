#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: AM Transmitter and Receiver
# Author: GNU Radio Intro Workshop
# Description: Dial tone -> AM modulator -> noisy channel -> envelope detector -> soundcard
# GNU Radio version: 3.10.12.0

from PyQt5 import Qt
from gnuradio import qtgui
from PyQt5 import QtCore
from gnuradio import analog
from gnuradio import audio
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




class am_loopback(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "AM Transmitter and Receiver", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("AM Transmitter and Receiver")
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

        self.settings = Qt.QSettings("gnuradio/flowgraphs", "am_loopback")

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
        self.volume = volume = 0.5
        self.samp_rate = samp_rate = 48000
        self.rx_tune = rx_tune = 10000
        self.noise_amp = noise_amp = 0.05
        self.mod_index = mod_index = 0.8
        self.carrier = carrier = 10000

        ##################################################
        # Blocks
        ##################################################

        self._rx_tune_range = qtgui.Range(-20000, 20000, 500, 10000, 200)
        self._rx_tune_win = qtgui.RangeWidget(self._rx_tune_range, self.set_rx_tune, "Receiver tuning (Hz)", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._rx_tune_win, 1, 1, 1, 1)
        for r in range(1, 2):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._noise_amp_range = qtgui.Range(0, 1, 0.01, 0.05, 200)
        self._noise_amp_win = qtgui.RangeWidget(self._noise_amp_range, self.set_noise_amp, "Channel noise", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._noise_amp_win, 1, 0, 1, 1)
        for r in range(1, 2):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._carrier_range = qtgui.Range(-20000, 20000, 500, 10000, 200)
        self._carrier_win = qtgui.RangeWidget(self._carrier_range, self.set_carrier, "Transmit carrier (Hz)", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._carrier_win, 0, 1, 1, 1)
        for r in range(0, 1):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._volume_range = qtgui.Range(0, 2, 0.05, 0.5, 200)
        self._volume_win = qtgui.RangeWidget(self._volume_range, self.set_volume, "Volume", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._volume_win, 2, 0, 1, 2)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.vol = blocks.multiply_const_ff(volume)
        self.tone_440 = analog.sig_source_f(samp_rate, analog.GR_COS_WAVE, 440, 0.5, 0, 0)
        self.tone_350 = analog.sig_source_f(samp_rate, analog.GR_COS_WAVE, 350, 0.5, 0, 0)
        self.to_complex = blocks.float_to_complex(1)
        self.rx_select = filter.freq_xlating_fir_filter_ccc(1, firdes.low_pass(1.0, samp_rate, 5e3, 1e3), rx_tune, samp_rate)
        self.rf_time = qtgui.time_sink_c(
            2048, #size
            samp_rate, #samp_rate
            "AM envelope (I and Q)", #name
            1, #number of inputs
            None # parent
        )
        self.rf_time.set_update_time(0.10)
        self.rf_time.set_y_axis(-3, 3)

        self.rf_time.set_y_label('Amplitude', "")

        self.rf_time.enable_tags(True)
        self.rf_time.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, 0, "")
        self.rf_time.enable_autoscale(False)
        self.rf_time.enable_grid(False)
        self.rf_time.enable_axis_labels(True)
        self.rf_time.enable_control_panel(False)
        self.rf_time.enable_stem_plot(False)


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
                    self.rf_time.set_line_label(i, "Re{{Data {0}}}".format(i/2))
                else:
                    self.rf_time.set_line_label(i, "Im{{Data {0}}}".format(i/2))
            else:
                self.rf_time.set_line_label(i, labels[i])
            self.rf_time.set_line_width(i, widths[i])
            self.rf_time.set_line_color(i, colors[i])
            self.rf_time.set_line_style(i, styles[i])
            self.rf_time.set_line_marker(i, markers[i])
            self.rf_time.set_line_alpha(i, alphas[i])

        self._rf_time_win = sip.wrapinstance(self.rf_time.qwidget(), Qt.QWidget)
        self.top_grid_layout.addWidget(self._rf_time_win, 3, 1, 1, 1)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.rf_sink = qtgui.freq_sink_c(
            2048, #size
            window.WIN_BLACKMAN_hARRIS, #wintype
            0, #fc
            samp_rate, #bw
            "Transmitted AM signal + noise", #name
            1,
            None # parent
        )
        self.rf_sink.set_update_time(0.10)
        self.rf_sink.set_y_axis((-120), 10)
        self.rf_sink.set_y_label('Relative Gain', 'dB')
        self.rf_sink.set_trigger_mode(qtgui.TRIG_MODE_FREE, 0.0, 0, "")
        self.rf_sink.enable_autoscale(False)
        self.rf_sink.enable_grid(False)
        self.rf_sink.set_fft_average(1.0)
        self.rf_sink.enable_axis_labels(True)
        self.rf_sink.enable_control_panel(False)
        self.rf_sink.set_fft_window_normalized(False)



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
                self.rf_sink.set_line_label(i, "Data {0}".format(i))
            else:
                self.rf_sink.set_line_label(i, labels[i])
            self.rf_sink.set_line_width(i, widths[i])
            self.rf_sink.set_line_color(i, colors[i])
            self.rf_sink.set_line_alpha(i, alphas[i])

        self._rf_sink_win = sip.wrapinstance(self.rf_sink.qwidget(), Qt.QWidget)
        self.top_grid_layout.addWidget(self._rf_sink_win, 3, 0, 1, 1)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.plus_one = blocks.add_const_ff(1)
        self.modulator = blocks.multiply_vcc(1)
        self._mod_index_range = qtgui.Range(0, 1.5, 0.05, 0.8, 200)
        self._mod_index_win = qtgui.RangeWidget(self._mod_index_range, self.set_mod_index, "Modulation index", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._mod_index_win, 0, 0, 1, 1)
        for r in range(0, 1):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.message = blocks.add_vff(1)
        self.index = blocks.multiply_const_ff(mod_index)
        self.envelope = blocks.complex_to_mag(1)
        self.dc_block = filter.dc_blocker_ff(128, True)
        self.channel_noise = analog.noise_source_c(analog.GR_GAUSSIAN, noise_amp, 0)
        self.channel = blocks.add_vcc(1)
        self.carrier_osc = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, carrier, 1, 0, 0)
        self.audio_out = audio.sink(samp_rate, '', True)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.carrier_osc, 0), (self.modulator, 1))
        self.connect((self.channel, 0), (self.rf_sink, 0))
        self.connect((self.channel, 0), (self.rf_time, 0))
        self.connect((self.channel, 0), (self.rx_select, 0))
        self.connect((self.channel_noise, 0), (self.channel, 1))
        self.connect((self.dc_block, 0), (self.vol, 0))
        self.connect((self.envelope, 0), (self.dc_block, 0))
        self.connect((self.index, 0), (self.plus_one, 0))
        self.connect((self.message, 0), (self.index, 0))
        self.connect((self.modulator, 0), (self.channel, 0))
        self.connect((self.plus_one, 0), (self.to_complex, 0))
        self.connect((self.rx_select, 0), (self.envelope, 0))
        self.connect((self.to_complex, 0), (self.modulator, 0))
        self.connect((self.tone_350, 0), (self.message, 0))
        self.connect((self.tone_440, 0), (self.message, 1))
        self.connect((self.vol, 0), (self.audio_out, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("gnuradio/flowgraphs", "am_loopback")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_volume(self):
        return self.volume

    def set_volume(self, volume):
        self.volume = volume
        self.vol.set_k(self.volume)

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.carrier_osc.set_sampling_freq(self.samp_rate)
        self.rf_sink.set_frequency_range(0, self.samp_rate)
        self.rf_time.set_samp_rate(self.samp_rate)
        self.rx_select.set_taps(firdes.low_pass(1.0, self.samp_rate, 5e3, 1e3))
        self.tone_350.set_sampling_freq(self.samp_rate)
        self.tone_440.set_sampling_freq(self.samp_rate)

    def get_rx_tune(self):
        return self.rx_tune

    def set_rx_tune(self, rx_tune):
        self.rx_tune = rx_tune
        self.rx_select.set_center_freq(self.rx_tune)

    def get_noise_amp(self):
        return self.noise_amp

    def set_noise_amp(self, noise_amp):
        self.noise_amp = noise_amp
        self.channel_noise.set_amplitude(self.noise_amp)

    def get_mod_index(self):
        return self.mod_index

    def set_mod_index(self, mod_index):
        self.mod_index = mod_index
        self.index.set_k(self.mod_index)

    def get_carrier(self):
        return self.carrier

    def set_carrier(self, carrier):
        self.carrier = carrier
        self.carrier_osc.set_frequency(self.carrier)




def main(top_block_cls=am_loopback, options=None):

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
