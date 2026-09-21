#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: FM Band Recorder
# Author: GNU Radio Intro Workshop
# Description: Two narrowband FM stations at -50 kHz and +60 kHz, recorded to fm_band.cfile
# GNU Radio version: 3.10.12.0

from PyQt5 import Qt
from gnuradio import qtgui
from gnuradio import analog
from gnuradio import blocks
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




class fm_band_recorder(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "FM Band Recorder", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("FM Band Recorder")
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

        self.settings = Qt.QSettings("gnuradio/flowgraphs", "fm_band_recorder")

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
        self.samp_rate = samp_rate = 240000
        self.recording = recording = "fm_band.cfile"
        self.audio_rate = audio_rate = 48000

        ##################################################
        # Blocks
        ##################################################

        self.tone_440 = analog.sig_source_f(audio_rate, analog.GR_COS_WAVE, 440, 0.4, 0, 0)
        self.tone_350 = analog.sig_source_f(audio_rate, analog.GR_COS_WAVE, 350, 0.4, 0, 0)
        self.throttle = blocks.throttle( gr.sizeof_gr_complex*1, samp_rate, True, 0 if "auto" == "auto" else max( int(float(0.1) * samp_rate) if "auto" == "time" else int(0.1), 1) )
        self.shift_b = blocks.multiply_vcc(1)
        self.shift_a = blocks.multiply_vcc(1)
        self.noise = analog.noise_source_c(analog.GR_GAUSSIAN, 0.01, 0)
        self.lo_b = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, 60000, 1, 0, 0)
        self.lo_a = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, (-50000), 1, 0, 0)
        self.fm_b = analog.nbfm_tx(
        	audio_rate=audio_rate,
        	quad_rate=samp_rate,
        	tau=(7.5e-05),
        	max_dev=5000.0,
        	fh=(-1.0),
                )
        self.fm_a = analog.nbfm_tx(
        	audio_rate=audio_rate,
        	quad_rate=samp_rate,
        	tau=(7.5e-05),
        	max_dev=5000.0,
        	fh=(-1.0),
                )
        self.file_sink = blocks.file_sink(gr.sizeof_gr_complex*1, recording, False)
        self.file_sink.set_unbuffered(False)
        self.dial_tone = blocks.add_vff(1)
        self.beeps = blocks.multiply_vff(1)
        self.beep_tone = analog.sig_source_f(audio_rate, analog.GR_COS_WAVE, 800, 0.8, 0, 0)
        self.beep_gate = analog.sig_source_f(audio_rate, analog.GR_SQR_WAVE, 2, 1, 0, 0)
        self.band_sink = qtgui.freq_sink_c(
            2048, #size
            window.WIN_BLACKMAN_hARRIS, #wintype
            0, #fc
            samp_rate, #bw
            "Band being recorded", #name
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
        self.top_grid_layout.addWidget(self._band_sink_win, 0, 0, 1, 1)
        for r in range(0, 1):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.band_fall = qtgui.waterfall_sink_c(
            1024, #size
            window.WIN_BLACKMAN_hARRIS, #wintype
            0, #fc
            samp_rate, #bw
            "Waterfall", #name
            1, #number of inputs
            None # parent
        )
        self.band_fall.set_update_time(0.10)
        self.band_fall.enable_grid(False)
        self.band_fall.enable_axis_labels(True)



        labels = ['', '', '', '', '',
                  '', '', '', '', '']
        colors = [0, 0, 0, 0, 0,
                  0, 0, 0, 0, 0]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
                  1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.band_fall.set_line_label(i, "Data {0}".format(i))
            else:
                self.band_fall.set_line_label(i, labels[i])
            self.band_fall.set_color_map(i, colors[i])
            self.band_fall.set_line_alpha(i, alphas[i])

        self.band_fall.set_intensity_range(-110, -20)

        self._band_fall_win = sip.wrapinstance(self.band_fall.qwidget(), Qt.QWidget)

        self.top_grid_layout.addWidget(self._band_fall_win, 1, 0, 1, 1)
        for r in range(1, 2):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.band = blocks.add_vcc(1)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.band, 0), (self.throttle, 0))
        self.connect((self.beep_gate, 0), (self.beeps, 1))
        self.connect((self.beep_tone, 0), (self.beeps, 0))
        self.connect((self.beeps, 0), (self.fm_b, 0))
        self.connect((self.dial_tone, 0), (self.fm_a, 0))
        self.connect((self.fm_a, 0), (self.shift_a, 0))
        self.connect((self.fm_b, 0), (self.shift_b, 0))
        self.connect((self.lo_a, 0), (self.shift_a, 1))
        self.connect((self.lo_b, 0), (self.shift_b, 1))
        self.connect((self.noise, 0), (self.band, 1))
        self.connect((self.shift_a, 0), (self.band, 0))
        self.connect((self.shift_b, 0), (self.band, 2))
        self.connect((self.throttle, 0), (self.band_fall, 0))
        self.connect((self.throttle, 0), (self.band_sink, 0))
        self.connect((self.throttle, 0), (self.file_sink, 0))
        self.connect((self.tone_350, 0), (self.dial_tone, 0))
        self.connect((self.tone_440, 0), (self.dial_tone, 1))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("gnuradio/flowgraphs", "fm_band_recorder")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.band_fall.set_frequency_range(0, self.samp_rate)
        self.band_sink.set_frequency_range(0, self.samp_rate)
        self.lo_a.set_sampling_freq(self.samp_rate)
        self.lo_b.set_sampling_freq(self.samp_rate)
        self.throttle.set_sample_rate(self.samp_rate)

    def get_recording(self):
        return self.recording

    def set_recording(self, recording):
        self.recording = recording
        self.file_sink.open(self.recording)

    def get_audio_rate(self):
        return self.audio_rate

    def set_audio_rate(self, audio_rate):
        self.audio_rate = audio_rate
        self.beep_gate.set_sampling_freq(self.audio_rate)
        self.beep_tone.set_sampling_freq(self.audio_rate)
        self.tone_350.set_sampling_freq(self.audio_rate)
        self.tone_440.set_sampling_freq(self.audio_rate)




def main(top_block_cls=fm_band_recorder, options=None):

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
