# set QT_API environment variable
import os 
os.environ["QT_API"] = "pyqt5"
import qtpy

# qt libraries
from qtpy.QtCore import *
from qtpy.QtWidgets import *
from qtpy.QtGui import *

# app specific libraries
import control.widgets as widgets
import control.camera_TIS as camera
import control.core as core
import control.microcontroller as microcontroller

class OctopiGUI(QMainWindow):

	# variables
	fps_software_trigger = 100

	def __init__(self, is_simulation = False, *args, **kwargs):
		super().__init__(*args, **kwargs)

		# load objects
		if is_simulation is True:
			self.camera = camera.Camera_Simulation(sn=17910089)
			self.microcontroller = microcontroller.Microcontroller_Simulation()
		else:
			self.camera = camera.Camera(sn=17910089)
			self.microcontroller = microcontroller.Microcontroller()
		
		self.configurationManager = core.ConfigurationManager()
		self.streamHandler = core.StreamHandler()
		self.liveController = core.LiveController(self.camera,self.microcontroller,self.configurationManager)
		self.imageSaver = core.ImageSaver()
		self.imageDisplay = core.ImageDisplay()

		# open the camera
		# camera start streaming
		self.camera.open()
		self.camera.set_software_triggered_acquisition() #self.camera.set_continuous_acquisition()
		self.camera.set_callback(self.streamHandler.on_new_frame)
		self.camera.enable_callback()

		# load widgets
		self.cameraSettingWidget = widgets.CameraSettingsWidget(self.camera,self.liveController)
		self.liveControlWidget = widgets.LiveControlWidget(self.streamHandler,self.liveController,self.configurationManager)
		self.recordingControlWidget = widgets.RecordingWidget(self.streamHandler,self.imageSaver)

		self.recordTabWidget = QTabWidget()
		self.recordTabWidget.addTab(self.recordingControlWidget, "Simple Recording")

		# layout widgets
		layout = QGridLayout() #layout = QStackedLayout()
		layout.addWidget(self.cameraSettingWidget,0,0)
		layout.addWidget(self.liveControlWidget,1,0)
		layout.addWidget(self.recordTabWidget,4,0)
		
		# transfer the layout to the central widget
		self.centralWidget = QWidget()
		self.centralWidget.setLayout(layout)
		self.setCentralWidget(self.centralWidget)

		# load window
		self.imageDisplayWindow = core.ImageDisplayWindow('Main Display')
		self.imageDisplayWindow.show()

		# make connections
		self.streamHandler.signal_new_frame_received.connect(self.liveController.on_new_frame)
		self.streamHandler.image_to_display.connect(self.imageDisplay.enqueue)
		self.streamHandler.packet_image_to_write.connect(self.imageSaver.enqueue)
		self.imageDisplay.image_to_display.connect(self.imageDisplayWindow.display_image) # may connect streamHandler directly to imageDisplayWindow

	def closeEvent(self, event):
		event.accept()
		# self.softwareTriggerGenerator.stop() @@@ => 
		self.liveController.stop_live()
		self.camera.close()
		self.imageSaver.close()
		self.imageDisplay.close()
		self.imageDisplayWindow.close()
