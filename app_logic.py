from PyQt5.QtWidgets import QFileDialog
from scipy.interpolate import interp1d
import pandas as pd
import time
import numpy as np
from pyqtgraph.Qt import QtCore


#Global variable
f_max = 1

class AppLogic():
        def __init__(self, ui_instance): 
            self.ui_instance = ui_instance
            self.ui_instance.tabWidget.setCurrentIndex(0)
            self.sampled_data = None
            self.sampled_points = None
            self.t = None
            self.ploted_signal = []
            self.signals = {}
            self.max_frequancy_composer = {}
            self.signal_names = []
            self.f_max = 0
        
        def load_signal(self):
            options = QFileDialog.Options()
            file_name, _ = QFileDialog.getOpenFileName(self.ui_instance, "Open CSV File", "", "CSV Files (*.csv);;All Files (*)", options=options)
            print(file_name)
            if file_name:
                try:
                    data = pd.read_csv(file_name)
                    time_data = data.iloc[:, 0].values
                    amplitude_data = data.iloc[:, 1].values
                    time_data = time_data - time_data[0] # Normalize time_data to start at 0
                    self.ui_instance.plotSignal.clear()
                    self.ui_instance.plotSample.clear()
                    plot_data = self.ui_instance.plotSignal.plot(time_data, amplitude_data, pen='b')
                    plot_data.setData(time_data[:1000], amplitude_data[:1000])

                    self.f_max=62.5 #change according the file which we know it's f_sample
                    
                    self.ui_instance.update_labelRMax(self.f_max)                   
                    self.sampled_data = (time_data, amplitude_data)
                    self.ui_instance.sliderHz.setMinimum(1)
                    self.ui_instance.sliderHz.setMaximum(int(4*self.f_max))
                except Exception as e:
                    print(f"Error loading the CSV file: {str(e)}")
            else:
                print("No file selected")
        
        def sample_and_plot(self):
            if self.sampled_data is not None:
                if self.sampled_points is not None:
                    self.ui_instance.plotSignal.removeItem(self.sampled_points)

                time_data, amplitude_data = self.sampled_data
                f_sample = self.ui_instance.sliderHz.value()
                self.ui_instance.update_labelSlider(f_sample)
                sample_interval = max(1, int(1 / (f_sample * (time_data[1] - time_data[0]))))
                
                # Sample the data
                sampled_time = time_data[::sample_interval]
                sampled_amplitude = amplitude_data[::sample_interval]
                
                #noise calculation
                noise_percentage = self.ui_instance.sliderNoise.value()
                self.ui_instance.labelNoise2.setText(f"{noise_percentage} %")
                noise_std = (noise_percentage / 100.0) * (sampled_amplitude.max() - sampled_amplitude.min()) 
                noise_std = max(0, noise_std)
                noisy_amplitude_data = sampled_amplitude + np.random.normal(0, noise_std, len(sampled_amplitude))


               # Perform sinc interpolation
                interpolation_factor = 1000
                interpolated_time = np.linspace(sampled_time.min(), sampled_time.max(), interpolation_factor)
                interpolated_amplitude = []
                for t in interpolated_time:
                    sinc_values = np.sinc((sampled_time - t) * f_sample)
                    interpolated_value = np.sum(noisy_amplitude_data * sinc_values) / np.sum(sinc_values)
                    interpolated_amplitude.append(interpolated_value)
                self.ui_instance.plotSample.clear()
                plot_data = self.ui_instance.plotSample.plot(interpolated_time, interpolated_amplitude, pen='r')
                self.sampled_points = self.ui_instance.plotSignal.scatterPlot(sampled_time, noisy_amplitude_data, pen=None,
                                                                          symbol='o', symbolPen='r', symbolBrush='r',
                                                                          symbolSize=5)
                self.ui_instance.plotSignal.replot()
                self.ui_instance.plotSample.replot()

                # Plot the error on the plotError widget
                self.ui_instance.plotError.clear()
                error = amplitude_data[:len(interpolated_amplitude)] - interpolated_amplitude
                error_plot = self.ui_instance.plotError.plot(interpolated_time, error, pen='g')
                self.error_plot_data = error_plot
                
                #Modify the error to set small errors to zero when slider is at or above 2*f_max
                if f_sample >= 2 * self.f_max:
                    small_error_threshold = 1e-4  # Adjust this threshold as needed
                    error[abs(error) < small_error_threshold] = 0
                    

        #Remove Signal 
        def remove_signal(self):
            self.ui_instance.plotSignal.clear()
            self.ui_instance.plotSample.clear()
            self.ui_instance.plotError.clear()
            self.ui_instance.labelRMax.clear()
            self.ui_instance.sliderHz.setValue(0)
            self.ui_instance.sliderNoise.setValue(0)


        def create_and_plot_signal(self):
            self.ui_instance.plotBefore.clear()
            name = self.ui_instance.editName.text()
            freq_text = self.ui_instance.editFreq.text()
            amp_text = self.ui_instance.editAmp.text()
            phase_text = self.ui_instance.editPhase.text()
            if freq_text and amp_text and phase_text:
                try:
                    frequency = float(freq_text)
                    amplitude = float(amp_text)
                    phase_shift = float(phase_text)

                    self.t = np.linspace(0, 7.984, 1000)
                    self.t = np.around(self.t, 3)
                    signal = amplitude * np.sin(2 * np.pi * frequency * self.t + phase_shift)
                    signal = np.around(signal, 5)
                    self.ploted_signal.append(signal)
                    self.signals[name] = signal
                    self.max_frequancy_composer[name] = frequency
                    self.signal_names.append(name)

                    self.ui_instance.plotBefore.plot(self.t, signal, pen='b')
                except ValueError:
                    pass
            else:
                pass

        def composer(self):
            self.ui_instance.plotAfter.clear()
            self.ui_instance.plotBefore.clear()

            if self.signals:      
                self.mix = np.sum(self.ploted_signal, axis=0)
                self.ui_instance.plotAfter.plot(self.t, self.mix, pen='r')
                self.ui_instance.signal_composer.clear()
                self.ui_instance.signal_composer.addItems(self.signal_names)
                max_feq =str(max(self.max_frequancy_composer.values()))
                self.ui_instance.composer_freq(max_feq)

                self.ui_instance.editName.clear()
                self.ui_instance.editFreq.clear()
                self.ui_instance.editAmp.clear()
                self.ui_instance.editPhase.clear()

        def remove_signal_tab2(self):
            selected_signal_name = self.ui_instance.signal_composer.currentText()

            if selected_signal_name != "":
                selected_signal_value = np.array(self.signals[selected_signal_name])
                self.mix = np.array(self.mix)
                self.mix = self.mix - selected_signal_value
                self.mix = self.mix.tolist()
                self.ui_instance.signal_composer.removeItem(self.ui_instance.signal_composer.currentIndex())
                del self.signals[selected_signal_name]
                del self.max_frequancy_composer[selected_signal_name]
                self.signal_names.remove(selected_signal_name)
                self.ui_instance.plotAfter.clear()

                if len(self.max_frequancy_composer) != 0:
                    self.f_max = str(max(self.max_frequancy_composer.values()))
                else:
                    self.f_max = "0"

                self.ui_instance.composer_freq(self.f_max)

                if self.signal_names:
                    self.ui_instance.plotAfter.plot(self.t, self.mix, pen='b')
            else:
                self.ui_instance.plotAfter.clear()
                self.ui_instance.labelRRFreq.setText("   ")

        def plot_mix(self):
            self.ui_instance.plotSignal.clear()  
            self.ui_instance.tabWidget.setCurrentIndex(0)
            self.ui_instance.plotAfter.clear()
            self.ui_instance.labelRRFreq.setText("   ")
            df = pd.DataFrame({'Time': self.t, 'Amplitude': self.mix})
            self.f_max = max(self.max_frequancy_composer.values())
            self.ui_instance.plotSignal.plot(self.t, self.mix, pen='b')
            self.ui_instance.update_labelRMax(self.f_max)
            self.ui_instance.sliderHz.setMinimum(1)
            self.ui_instance.sliderHz.setMaximum(int(4 *self.f_max))
            self.sampled_data = (df['Time'], df['Amplitude'])
            df.to_csv("signal_composer" + '.csv', index=False)

