from PyQt5 import QtWidgets
from PyQt5.QtCore import QThread, pyqtSignal
from pylab import *
import visa
import time
import math
from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.figure import Figure

from CoMeter_GUI import Ui_MainWindow                                          # Import der GUI

class measDMM(QThread):

    measMode = 'VOLT'
    measUpdate = pyqtSignal(str)
    
    def __init__(self,arduino):
        QThread.__init__(self)
        self.arduino = arduino

    def run(self):
        while True:
            if self.measMode == 'CURR':
                readString = self.arduino.query('MEAS:CURR?')
                measString = readString.strip() + ' A'
            else:
                readString = self.arduino.query('MEAS:VOLT?')
                measString = readString.strip() + ' V'
                
            self.measUpdate.emit(measString)
            time.sleep(1)

class measDSO(QThread):
        
    def __init__(self,arduino,MplWidget,vertical,position):
        QThread.__init__(self)
        self.arduino = arduino
        self.MplWidget = MplWidget
        self.vertical = vertical;
        self.position = position;

    def run(self):
        while True:
            zeitString = self.arduino.query('TIM:SCAL?') 
            dataString = self.arduino.query('WAV:DATA?')
            
            if dataString[0] == "#":
                dataString = dataString[10:]
                
            dataList = dataString.split(',')
            Waveform1 = zeros(size(dataList)/2)
            Waveform2 = zeros(size(dataList)/2)
            for i in range(size(dataList)/2):
                Waveform1[i] = float(dataList[i])
            
            for i in range(size(dataList)/2):
                Waveform2[i] = float(dataList[i+size(dataList)/2])

            Zeit = linspace(0,float(zeitString)*10,size(Waveform1)/2)
            
            self.MplWidget.canvas.axes.clear()
            self.MplWidget.canvas.axes.plot(Zeit,Waveform1+self.position)
            self.MplWidget.canvas.axes.plot(Zeit,Waveform2+self.position)
            self.MplWidget.canvas.axes.plot(0, self.position, marker='>', markersize=12, c='C0')
            self.MplWidget.canvas.axes.plot(float(zeitString)*10, self.position, marker='<', markersize=12, c='C0')
            self.MplWidget.canvas.axes.set_xlabel('Time (s)')
            self.MplWidget.canvas.axes.set_ylabel('Voltage (V)')
            self.MplWidget.canvas.axes.grid(True, color='white', linestyle=':')
            self.MplWidget.canvas.axes.set_xlim(0,float(zeitString)*10)
            self.MplWidget.canvas.axes.set_ylim(-5*self.vertical,5*self.vertical)
            self.MplWidget.canvas.draw()
            
class CoMeter_window(QtWidgets.QMainWindow):
    
    rm = visa.ResourceManager('@py')
    
    dial_FGEN_Freq_lastValue = 0;
    FGEN_Freq_currentValue = 10;
    dial_FGEN_Amp_lastValue = 0;
    FGEN_Amp_currentValue = 2;
    dial_FGEN_Offset_lastValue = 0;
    FGEN_Offset_currentValue = 0;
    dial_DSO_position_lastValue = 0;
    DSO_position_currentValue = 0;
    
    def __init__(self):
        super(CoMeter_window, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.comboBox_device.addItems(self.rm.list_resources())
        self.ui.tabWidget.setEnabled(False)
        self.ui.pushButton_connect.clicked.connect(self.arduino_connect)
        self.ui.pushButton_disconnect.clicked.connect(self.arduino_disconnect)
        
        self.ui.pushButton_DMM_start.clicked.connect(self.DMM_start)
        self.ui.pushButton_DMM_stop.clicked.connect(self.DMM_stop)
        self.ui.radioButton_DMM_VOLT.toggled.connect(self.DMM_set_mode)
        self.ui.radioButton_DMM_CURR.toggled.connect(self.DMM_set_mode)
        
        self.ui.pushButton_FGEN_start.clicked.connect(self.FGEN_start)
        self.ui.pushButton_FGEN_stop.clicked.connect(self.FGEN_stop)
        self.ui.dial_FGEN_Freq.valueChanged.connect(self.FGEN_freq)
        self.ui.dial_FGEN_Freq.sliderReleased.connect(self.FGEN_freq_release)
        self.ui.dial_FGEN_Amp.valueChanged.connect(self.FGEN_amp)
        self.ui.dial_FGEN_Amp.sliderReleased.connect(self.FGEN_amp_release)
        self.ui.dial_FGEN_Offset.valueChanged.connect(self.FGEN_offset)
        self.ui.dial_FGEN_Offset.sliderReleased.connect(self.FGEN_offset_release)
        self.ui.radioButton_FGEN_Sine.toggled.connect(self.FGEN_waveform)
        self.ui.radioButton_FGEN_Square.toggled.connect(self.FGEN_waveform)
        
        self.ui.pushButton_DSO_start.clicked.connect(self.DSO_start)
        self.ui.pushButton_DSO_stop.clicked.connect(self.DSO_stop)
        self.ui.pushButton_DSO_start.setEnabled(True)
        self.ui.dial_DSO_hor.sliderReleased.connect(self.DSO_horizontal_update)
        self.ui.dial_DSO_vert.sliderReleased.connect(self.DSO_vertical_update)
        self.ui.dial_DSO_pos.valueChanged.connect(self.DSO_position)
        self.ui.dial_DSO_pos.sliderReleased.connect(self.DSO_position_update)
        
        self.ui.MplWidget.canvas.figure.patch.set_facecolor('black')
        self.ui.MplWidget.canvas.axes.set_facecolor('black')
        self.ui.MplWidget.canvas.axes.spines['left'].set_color('white')
        self.ui.MplWidget.canvas.axes.spines['right'].set_color('white')
        self.ui.MplWidget.canvas.axes.spines['bottom'].set_color('white')
        self.ui.MplWidget.canvas.axes.spines['top'].set_color('white')
        self.ui.MplWidget.canvas.axes.tick_params(axis='x',colors='white')
        self.ui.MplWidget.canvas.axes.tick_params(axis='y',colors='white')
        self.ui.MplWidget.canvas.axes.xaxis.label.set_color('white')
        self.ui.MplWidget.canvas.axes.yaxis.label.set_color('white')
        self.ui.MplWidget.canvas.axes.grid(True, color='white', linestyle=':')
        self.ui.MplWidget.canvas.axes.set_position([0.14,0.2,0.85,0.78])
        self.ui.MplWidget.canvas.axes.set_xlabel('Time (s)')
        self.ui.MplWidget.canvas.axes.set_ylabel('Voltage (V)')
        self.ui.MplWidget.canvas.axes.grid(True, color='white', linestyle=':')

    def arduino_connect(self): 
        self.arduino = self.rm.open_resource(self.ui.comboBox_device.currentText())

        self.ui.comboBox_device.setEnabled(False)
        self.ui.pushButton_connect.setEnabled(False)
        self.ui.pushButton_disconnect.setEnabled(True)
        self.ui.tabWidget.setEnabled(True)

    def arduino_disconnect(self):      
        self.arduino.close()
        self.ui.comboBox_device.setEnabled(True)
        self.ui.pushButton_connect.setEnabled(True)
        self.ui.pushButton_disconnect.setEnabled(False)
        self.ui.tabWidget.setEnabled(False)
            
    def DMM_start(self):      
        self.ui.pushButton_DMM_start.setEnabled(False)
        self.ui.pushButton_DMM_stop.setEnabled(True)
        self.ui.label_DMM_measValue.setEnabled(True)
        self.measurement_DMM = measDMM(self.arduino)
        self.measurement_DMM.measUpdate.connect(self.ui.label_DMM_measValue.setText)
        self.DMM_set_mode()
        self.measurement_DMM.start()

    def DMM_stop(self):      
        self.ui.pushButton_DMM_start.setEnabled(True)
        self.ui.pushButton_DMM_stop.setEnabled(False)
        self.ui.label_DMM_measValue.setEnabled(False)
        self.measurement_DMM.terminate()
        
    def DMM_set_mode(self):      
        if self.ui.radioButton_DMM_CURR.isChecked():
            self.measurement_DMM.measMode = 'CURR'
        else:                
            self.measurement_DMM.measMode = 'VOLT'
        
    def FGEN_start(self):      
        self.ui.pushButton_FGEN_start.setEnabled(False)
        self.ui.pushButton_FGEN_stop.setEnabled(True)
        self.ui.label_FGEN_Freq.setEnabled(True)
        self.ui.label_FGEN_Amp.setEnabled(True)
        self.ui.label_FGEN_Offset.setEnabled(True)
        
        self.arduino.write('FREQ '+self.ui.label_FGEN_Freq.text())
        self.arduino.write('VOLT '+self.ui.label_FGEN_Amp.text())
        self.arduino.write('VOLT:OFFSET '+self.ui.label_FGEN_Offset.text())
        self.FGEN_waveform()
        
        self.arduino.write('OUTP ON')
            
    def FGEN_stop(self):      
        self.ui.pushButton_FGEN_start.setEnabled(True)
        self.ui.pushButton_FGEN_stop.setEnabled(False)
        self.ui.label_FGEN_Freq.setEnabled(False)
        self.ui.label_FGEN_Amp.setEnabled(False)
        self.ui.label_FGEN_Offset.setEnabled(False)

        self.arduino.write('OUTP OFF')
        
    def FGEN_freq(self):
        dial_FGEN_Freq_currentValue = self.ui.dial_FGEN_Freq.value()
        dial_FGEN_Freq_diffValue = dial_FGEN_Freq_currentValue-self.dial_FGEN_Freq_lastValue
        if(abs(dial_FGEN_Freq_diffValue)<50):
            self.FGEN_Freq_currentValue = self.FGEN_Freq_currentValue*(1+dial_FGEN_Freq_diffValue/200)
            self.ui.label_FGEN_Freq.setText("%.3f Hz" % (self.FGEN_Freq_currentValue))
        self.dial_FGEN_Freq_lastValue = dial_FGEN_Freq_currentValue
        
    def FGEN_freq_release(self):      
        if(self.ui.pushButton_FGEN_stop.isEnabled()):
            self.arduino.write('FREQ '+self.ui.label_FGEN_Freq.text())

    def FGEN_amp(self):      
        dial_FGEN_Amp_currentValue = self.ui.dial_FGEN_Amp.value()
        dial_FGEN_Amp_diffValue = dial_FGEN_Amp_currentValue-self.dial_FGEN_Amp_lastValue
        if(abs(dial_FGEN_Amp_diffValue)<50):
            self.FGEN_Amp_currentValue = self.FGEN_Amp_currentValue+dial_FGEN_Amp_diffValue/200
            self.ui.label_FGEN_Amp.setText("%.3f V" % (self.FGEN_Amp_currentValue))
        self.dial_FGEN_Amp_lastValue = dial_FGEN_Amp_currentValue
        
    def FGEN_amp_release(self):
        if(self.ui.pushButton_FGEN_stop.isEnabled()):
            self.arduino.write('VOLT '+self.ui.label_FGEN_Amp.text())

    def FGEN_offset(self):      
        dial_FGEN_Offset_currentValue = self.ui.dial_FGEN_Offset.value()
        dial_FGEN_Offset_diffValue = dial_FGEN_Offset_currentValue-self.dial_FGEN_Offset_lastValue
        if(abs(dial_FGEN_Offset_diffValue)<50):
            self.FGEN_Offset_currentValue = self.FGEN_Offset_currentValue+dial_FGEN_Offset_diffValue/200
            self.ui.label_FGEN_Offset.setText("%.3f V" % (self.FGEN_Offset_currentValue))
        self.dial_FGEN_Offset_lastValue = dial_FGEN_Offset_currentValue
        
    def FGEN_offset_release(self):      
        if(self.ui.pushButton_FGEN_stop.isEnabled()):
            self.arduino.write('VOLT:OFFS '+self.ui.label_FGEN_Offset.text())
   
    def FGEN_waveform(self):      
        if self.ui.radioButton_FGEN_Sine.isChecked():
            self.arduino.write('FUNC SIN')
        if self.ui.radioButton_FGEN_Square.isChecked():
            self.arduino.write('FUNC SQU')

    def DSO_start(self):
        self.ui.pushButton_DSO_start.setEnabled(False)
        self.ui.pushButton_DSO_stop.setEnabled(True)
        self.arduino.write('WAV:FORM ASCII')
        self.arduino.write('WAV:POIN 100')
        self.arduino.write('TIM:SCAL '+str(round(10**(float(self.ui.dial_DSO_hor.value())/3),-math.floor(self.ui.dial_DSO_hor.value()/3),)))
        self.measurement_DSO = measDSO(self.arduino,self.ui.MplWidget,round(10**(float(self.ui.dial_DSO_vert.value())/3),-math.floor(self.ui.dial_DSO_vert.value()/3)),self.dial_DSO_position_lastValue)
        self.measurement_DSO.start()   

    def DSO_stop(self):
        self.ui.pushButton_DSO_start.setEnabled(True)
        self.ui.pushButton_DSO_stop.setEnabled(False)
        self.measurement_DSO.terminate()
        
    def DSO_horizontal_update(self):    
        if(self.ui.pushButton_DSO_stop.isEnabled()):
            self.arduino.write('TIM:SCAL '+str(round(10**(float(self.ui.dial_DSO_hor.value())/3),-math.floor(self.ui.dial_DSO_hor.value()/3),)))

    def DSO_vertical_update(self):    
        if(self.ui.pushButton_DSO_stop.isEnabled()):
            self.measurement_DSO.vertical = round(10**(float(self.ui.dial_DSO_vert.value())/3),-math.floor(self.ui.dial_DSO_vert.value()/3))

    def DSO_position(self):
        dial_DSO_position_currentValue = self.ui.dial_DSO_pos.value()
        dial_DSO_position_diffValue = dial_DSO_position_currentValue-self.dial_DSO_position_lastValue
        if(abs(dial_DSO_position_diffValue)<50):
            self.DSO_position_currentValue = self.DSO_position_currentValue+dial_DSO_position_diffValue/200
        self.dial_DSO_position_lastValue = dial_DSO_position_currentValue
        
    def DSO_position_update(self):    
        if(self.ui.pushButton_DSO_stop.isEnabled()):
            self.measurement_DSO.position = self.DSO_position_currentValue

app = QtWidgets.QApplication([])
application = CoMeter_window()
application.show()

app.exec_()
