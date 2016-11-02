###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
#           http://ilastik.org/license.html
##############################################################################
from functools import partial
from contextlib import contextmanager
import threading
import os

import numpy as np

import sip
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QWidget, QLabel, QSpinBox, QDoubleSpinBox, QVBoxLayout, \
                        QHBoxLayout, QSpacerItem, QSizePolicy, QColor, QPen, QComboBox, QPushButton
from PyQt4.Qt import QCheckBox, QLineEdit, QButtonGroup, QRadioButton, pyqtSlot



from ilastik.utility.gui import threadRouted
from volumina.pixelpipeline.datasources import LazyflowSource, ArraySource
from volumina.layer import GrayscaleLayer, ColortableLayer, generateRandomColors
#from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui
from ilastik.applets.labeling.labelingGui import LabelingGui


from lazyflow.request import Request
from lazyflow.utility import TransposedView

import logging
from PyQt4.Qt import QCheckBox
logger = logging.getLogger(__name__)

#LayerViewerGui->LabelingGui->WatershedSegmentationGui
#class WatershedSegmentationGui(LayerViewerGui):
class WatershedSegmentationGui(LabelingGui):

    ###########################################
    ### AppletGuiInterface Concrete Methods ###
    ###########################################
    
    def appletDrawer(self):
        return self._drawer

    def stopAndCleanUp(self):
        # Unsubscribe to all signals
        for fn in self.__cleanup_fns:
            fn()

        # Base class
        super( WatershedSegmentationGui, self ).stopAndCleanUp()
    
    ###########################################
    ###########################################
    
    def __init__(self, parentApplet, topLevelOperatorView, labelingDrawerUiPath=None ):
    #def __init__(self, parentApplet, topLevelOperatorView, drawerUiPath=None, rawInputSlot=None, crosshair=True):
    #def __init__(self, parentApplet, topLevelOperatorView):

        #TODO
        #labeling slots
        #logging.info("\n vor \n")
        self.RawDataName = "Seeds"
        self.__cleanup_fns = []
        self._currently_updating = False
        self.topLevelOperatorView = topLevelOperatorView

        #super(WatershedSegmentationGui, self).__init__( parentApplet, topLevelOperatorView )
        #labelingDrawerUiPath = drawerUiPath
        super(WatershedSegmentationGui, self).__init__( parentApplet, labelingSlots, topLevelOperatorView, drawerUiPath )    

        self._sp_colortable = generateRandomColors(256, clamp={'v': 1.0, 's' : 0.5}, zeroIsTransparent=True)
        
        self._threshold_colortable = [ QColor(0, 0, 0, 0).rgba(),      # transparent
                                       QColor(0, 255, 0, 255).rgba() ] # green

        # Any time watershed is re-computed, re-update the layer set, in case the set of debug layers has changed.
        '''
        self.topLevelOperatorView.watershed_completed.subscribe( self.updateAllLayers )
        '''

    #slightly faster with pyqtSlot
    @pyqtSlot(int)
    def on_SpinBox_valueChanged(self, i):
        """
        executed when x,y or z is changed
        get the current values and change the view for the pixel-value
        The spinbox has updated its value, 
        so the new value i (of signal) == x.SpinBox.value() (for y,z as well)
        i remains unused

        """
        x = self.volumeEditorWidget.quadViewStatusBar.xSpinBox.value()
        y = self.volumeEditorWidget.quadViewStatusBar.ySpinBox.value()
        z = self.volumeEditorWidget.quadViewStatusBar.zSpinBox.value()
        t = self.volumeEditorWidget.quadViewStatusBar.timeSpinBox.value()
        #TODO take channels into account, not always looking at the first channel
        c = self.channel_box.value()
        self.changeToNewPixelValue(x, y, z, t, c)

    def changeToNewPixelValue(self, x, y, z, t, c):
        op = self.topLevelOperatorView
        data = op.RawData
        tags = data.meta.axistags
        if data.ready():
            count = 0
            array = [0,0,0,0,0]
            # rearrangement of the indices of x,y,z,t,c to have the correct axis-order
            # indices always start with 0,1,...
            # if the dimensions are tagged, then they are ordered like: 0,1,2
            # and not like 1, 2, 3
            # so that the section with e.g. count == 3 makes sense
            
            tupl = (('x', x, tags.index('x')),
                    ('y', y, tags.index('y')),
                    ('z', z, tags.index('z')),
                    ('t', t, tags.index('t')),
                    ('c', c, tags.index('c')))

            #copy the axis-value into the array at the right index for all axes
            for (letter, value, index) in tupl:
                if (letter in tags):
                    count+=1
                    array[index] = value


            """ worse performance than if..elif..
            def f(count, data, array):
                for i in range(count):
                    data = data[array[i]]
                return data
            newValue = f(count, data.value, array)
            """
            if (count == 2):
                newValue = data.value[array[0],array[1]]
            elif (count == 3):
                newValue = data.value[array[0],array[1],array[2]]
            elif (count == 4):
                newValue = data.value[array[0],array[1],array[2],array[3]]
            elif (count == 5):
                newValue = data.value[array[0],array[1],array[2],array[3],array[4]]

            #show the value of the pixel under the curser on the gui
            self.pixelValue.setText(str(newValue))

            """print infos
            print xIndex, ":", yIndex, ":", zIndex, ":", tIndex
            print tags
            print data
            print "array:", array
            print "pixelValue:", newValue
            """






    @pyqtSlot()
    def toggleConnectionPixelValue(self):
        """
        connect or disconnect the valueChanged signals from 
        coordinates x,y,z,t,c with the slot: on_SpinBox_valueChanged
        so that changes can be registered or not
        Additionally: change the label of the pixelValue

        Explanation for the x,y,z,timeSpinBox:
        # Connect the standard signal, that is emitted, when a QSpinBox changes its value, 
        # 'valueChanged' with the function that handles this change
        # to compute the changed value of the pixel with the new coordinates
        # Origin for better understanding:
        # volumina/volumina/sliceSelctorHud.py:
        # QuadStatusBar.xSpinBox (and y,z)
        # with standard signal: valueChanged
        # /volumina/volumina/volumeEditorWidget.py
        # self=VolumneEditorWidget
        # self.quadViewStatusBar = QuadStatusBar()
        # e.g. 
        #self.volumeEditorWidget.quadViewStatusBar.zSpinBox.valueChanged.connect( self.on_SpinBox_valueChanged )
        """

        #tuple with x,y,z,t,c and their spinBoxes
        sBar = self.volumeEditorWidget.quadViewStatusBar
        tupl = (sBar.xSpinBox,  sBar.ySpinBox, sBar.zSpinBox, sBar.timeSpinBox, self.channel_box)
        if self.showPixelValue.isChecked():
            #connect x,y,z,t,c
            for box in tupl:
                box.valueChanged.connect(self.on_SpinBox_valueChanged)

            #emit signal (of local widget) to read in the pixel values immediately 
            #number is irrelevant, see on_SpinBox_valueChanged
            self.channel_box.valueChanged.emit(0)
        else:
            #disconnect x,y,z,t,c
            for box in tupl:
                box.valueChanged.disconnect(self.on_SpinBox_valueChanged)
            #reset pixelValue-Label
            self.pixelValue.setText("unused")




    def initAppletDrawerUi(self):
        """
        Overridden from base class (LayerViewerGui)
        """
        op = self.topLevelOperatorView
        
        #handler which takes the qt_signal and the slot that fits to this signal and connects them
        # clean-up and dirty-Notification will be done here too
        def configure_update_handlers( qt_signal, op_slot ):
            qt_signal.connect( self.configure_operator_from_gui )
            op_slot.notifyDirty( self.configure_gui_from_operator )
            self.__cleanup_fns.append( partial( op_slot.unregisterDirty, self.configure_gui_from_operator ) )

        def control_layout_wlw( widget1, label_text, widget2 ):
            """
            Define the way, how the labels for input widgets are shown in the gui
            They are added to a horizontal BoxLayout and afterwards 
            this layout is added to a vertivalLayoutBox
            """
            row_layout = QHBoxLayout()
            row_layout.addWidget(widget1)
            row_layout.addWidget( QLabel(label_text) )
            row_layout.addSpacerItem( QSpacerItem(10, 0, QSizePolicy.Expanding) )
            row_layout.addWidget(widget2)
            return row_layout

        def control_layout(*args):
            """
            Define the way, how the input widgets are shown in the gui
            They are added to a horizontal BoxLayout and afterwards 
            this layout is added to a vertivalLayoutBox
            """
            space=10
            row_layout = QHBoxLayout()
            begin = True
            # Add all arguments passed on
            for widget in args:
                #convert strings to QLabel
                #for python3.x add:
                #basestring = str
                if isinstance(widget, basestring):
                    widget = QLabel(widget)
                #only add space after first widget
                if not begin:
                    row_layout.addSpacerItem( QSpacerItem(space, 0, QSizePolicy.Expanding) )
                row_layout.addWidget(widget)
                begin = False
            return row_layout



        ############################################################
        #Configure the Gui
        ############################################################
        drawer_layout = QVBoxLayout()

            ############################################################
            # additional seeds
            ############################################################
        drawer_layout.addLayout( control_layout("Set additional seeds:") )
        drawer_layout.addLayout( control_layout("Caution: no effect in Batch Processing") )
        drawer_layout.addLayout( control_layout("") )

        #channel Selection
        channel_box = QSpinBox()
        def set_channel_box_range(*args):
            if sip.isdeleted(channel_box):
                return
            channel_box.setMinimum(0)
            #throws an exception, if probabilities in input data aren't there, 
            #Fixed with op.Input.ready()
            if op.RawData.ready():
                channel_box.setMaximum( op.RawData.meta.getTaggedShape()['c']-1 )
            else:
                #only showed in debug mode
                #TODO not good, because emitted everytime when Input Data is changed
                logging.warning( "RawData not ready (maybe not existing)" )

        set_channel_box_range()
        op.RawData.notifyMetaChanged( set_channel_box_range )
        configure_update_handlers( channel_box.valueChanged, op.ChannelSelection )
        drawer_layout.addLayout( control_layout( self.RawDataName + " Channel", channel_box ) )
        self.channel_box = channel_box
        #connect the channel spinbox with the layer channel box
        self.channel_box.valueChanged.connect(self.on_RawData_channelChanged)


        #show pixel value
        pixelValue = QLabel('unused')
        showPixelValue = QCheckBox()
        #configure_update_handlers not necessary here, 
        #because no information is passed on for calculations
        drawer_layout.addLayout( control_layout_wlw(showPixelValue, "Show Pixel-Value:", pixelValue) )
        self.pixelValue = pixelValue
        self.showPixelValue = showPixelValue
        self.showPixelValue.stateChanged.connect(self.toggleConnectionPixelValue)
        
        

        #brush value dropdown or similar
        brush_value_box = QSpinBox()
        
        def set_brush_value_box_range(*args):
            if sip.isdeleted(brush_value_box):
                return
            brush_value_box.setMinimum(0)
            #throws an exception, if probabilities in input data aren't there, 
            #Fixed with op.Input.ready()
            if op.RawData.ready():
                if op.RawData.meta.drange:
                    #set min and max to the value range of the image
                    brush_value_box.setMinimum( op.RawData.meta.drange[0] )
                    brush_value_box.setMaximum( op.RawData.meta.drange[1] )
            else:
                #only showed in debug mode
                #TODO not good, because emitted everytime when Input Data is changed
                logging.warning( "RawData not ready (maybe not existing)" )
        set_brush_value_box_range()
        op.RawData.notifyMetaChanged( set_brush_value_box_range )
        configure_update_handlers( brush_value_box.valueChanged, op.BrushValue )
        drawer_layout.addLayout( control_layout("Brush value:", brush_value_box) )
        self.brush_value_box = brush_value_box
        #self.showPixelValue.stateChanged.connect(self.toggleConnectionPixelValue)

        ############################################################
        # BEGIN TODO
        ############################################################

        #pixel classification training applets
        # We provide our own UI file (which adds an extra control for interactive mode)
        #labelingDrawerUiPath = os.path.split(__file__)[0] + '/labelingDrawer.ui'

        #SIEHE TODO LISTE AUF BLOCK

        #toolBar = QToolBar()
        #first =  QToolButton()
        #arrowToolButton
        #paintToolButton
        #eraserToolButton
        #thresToolButton
        #brushSizeCaption
        #brushSizeComboBox
        
        #c++
        #button->setIcon(QIcon("<imagePath>"));
        #button->setIconSize(QSize(65,65));


        ############################################################
        # END TODO
        ############################################################

            ############################################################
            # seeded watershed
            ############################################################
        drawer_layout.addLayout( control_layout("") )
        drawer_layout.addLayout( control_layout("Seeded watershed:") )



        '''
        threshold_box = QDoubleSpinBox()
        threshold_box.setDecimals(2)
        threshold_box.setMinimum(0.00)
        threshold_box.setMaximum(1.0)
        threshold_box.setSingleStep(0.1)
        configure_update_handlers( threshold_box.valueChanged, op.Pmin )
        drawer_layout.addLayout( control_layout( "Threshold", threshold_box ) )
        self.threshold_box = threshold_box

        membrane_size_box = QSpinBox()
        membrane_size_box.setMinimum(0)
        membrane_size_box.setMaximum(1000000)
        configure_update_handlers( membrane_size_box.valueChanged, op.MinMembraneSize )
        drawer_layout.addLayout( control_layout( "Min Membrane Size", membrane_size_box ) )
        self.membrane_size_box = membrane_size_box

        seed_presmoothing_box = QDoubleSpinBox()
        seed_presmoothing_box.setDecimals(1)
        seed_presmoothing_box.setMinimum(0.0)
        seed_presmoothing_box.setMaximum(10.0)
        seed_presmoothing_box.setSingleStep(0.1)
        configure_update_handlers( seed_presmoothing_box.valueChanged, op.SigmaMinima )
        drawer_layout.addLayout( control_layout( "Presmooth before seeds", seed_presmoothing_box ) )
        self.seed_presmoothing_box = seed_presmoothing_box

        seed_method_combo = QComboBox()
        seed_method_combo.addItem("Connected")
        seed_method_combo.addItem("Clustered")
        configure_update_handlers( seed_method_combo.currentIndexChanged, op.GroupSeeds )
        drawer_layout.addLayout( control_layout( "Seed Labeling", seed_method_combo ) )
        self.seed_method_combo = seed_method_combo
        
        watershed_presmoothing_box = QDoubleSpinBox()
        watershed_presmoothing_box.setDecimals(1)
        watershed_presmoothing_box.setMinimum(0.0)
        watershed_presmoothing_box.setMaximum(10.0)
        watershed_presmoothing_box.setSingleStep(0.1)
        configure_update_handlers( watershed_presmoothing_box.valueChanged, op.SigmaWeights )
        drawer_layout.addLayout( control_layout( "Presmooth before watershed", watershed_presmoothing_box ) )
        self.watershed_presmoothing_box = watershed_presmoothing_box

        superpixel_size_box = QSpinBox()
        superpixel_size_box.setMinimum(0)
        superpixel_size_box.setMaximum(1000000)
        configure_update_handlers( superpixel_size_box.valueChanged, op.MinSegmentSize )
        drawer_layout.addLayout( control_layout( "Min Superpixel Size", superpixel_size_box ) )
        self.superpixel_size_box = superpixel_size_box

        enable_debug_box = QCheckBox()
        configure_update_handlers( enable_debug_box.toggled, op.EnableDebugOutputs )
        drawer_layout.addLayout( control_layout( "Show Debug Layers", enable_debug_box ) )
        self.enable_debug_box = enable_debug_box

        compute_button = QPushButton("Update Watershed", clicked=self.onUpdateWatershedsButton)
        drawer_layout.addWidget( compute_button )
        '''

        
        ############################################################
        #Init the drawer for the Applet
        ############################################################
        # Finally, the whole drawer widget
        # which means all widgets created before are initilized to one widget, 
        # that is saved as a class member
        drawer = QWidget(parent=self)
        drawer.setLayout(drawer_layout)

        # Save these members for later use
        self._drawer = drawer

        # Initialize everything with the operator's initial values
        self.configure_gui_from_operator()

        # Delete space, so that the Layout lies on top of the page and not on bottom
        drawer_layout.setSpacing(0)
        drawer_layout.addSpacerItem( QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Expanding) )

    @contextmanager
    def set_updating(self):
        assert not self._currently_updating
        self._currently_updating = True
        yield
        self._currently_updating = False

    def configure_gui_from_operator(self, *args):
        """
        see configure_update_handlers
        """
        #TODO don't now, why to do this
        if self._currently_updating:
            return False
        with self.set_updating():
            op = self.topLevelOperatorView
            self.channel_box.setValue( op.ChannelSelection.value )
            
            rawData_layer = self.getLayerByName(self.RawDataName)
            if rawData_layer:
                rawData_layer.channel = op.ChannelSelection.value
            
            self.brush_value_box.setValue( op.BrushValue.value )
            #self.threshold_box.setValue( op.Pmin.value )
            #self.membrane_size_box.setValue( op.MinMembraneSize.value )
            #self.superpixel_size_box.setValue( op.MinSegmentSize.value )
            #self.seed_presmoothing_box.setValue( op.SigmaMinima.value )
            #self.watershed_presmoothing_box.setValue( op.SigmaWeights.value )
            #self.seed_method_combo.setCurrentIndex( int(op.GroupSeeds.value) )
            #self.enable_debug_box.setChecked( op.EnableDebugOutputs.value )

    def configure_operator_from_gui(self):
        """
        see configure_update_handlers
        """
        if self._currently_updating:
            return False
        with self.set_updating():
            op = self.topLevelOperatorView
            op.ChannelSelection.setValue( self.channel_box.value() )
            op.BrushValue.setValue( self.brush_value_box.value() )

            #op.Pmin.setValue( self.threshold_box.value() )
            #op.MinMembraneSize.setValue( self.membrane_size_box.value() )
            #op.MinSegmentSize.setValue( self.superpixel_size_box.value() )
            #op.SigmaMinima.setValue( self.seed_presmoothing_box.value() )
            #op.SigmaWeights.setValue( self.watershed_presmoothing_box.value() )
            #op.GroupSeeds.setValue( bool(self.seed_method_combo.currentIndex()) )
            #op.EnableDebugOutputs.setValue( self.enable_debug_box.isChecked() )

    '''
    def onUpdateWatershedsButton(self):
        def updateThread():
            """
            Temporarily unfreeze the cache and freeze it again after the views are finished rendering.
            """
            self.topLevelOperatorView.FreezeCache.setValue(False)
            
            # This is hacky, but for now it's the only way to do it.
            # We need to make sure the rendering thread has actually seen that the cache
            # has been updated before we ask it to wait for all views to be 100% rendered.
            # If we don't wait, it might complete too soon (with the old data).
            ndim = len(self.topLevelOperatorView.Superpixels.meta.shape)
            self.topLevelOperatorView.Superpixels((0,)*ndim, (1,)*ndim).wait()

            # Wait for the image to be rendered into all three image views
            for imgView in self.editor.imageViews:
                if imgView.isVisible():
                    imgView.scene().joinRenderingAllTiles()
            self.topLevelOperatorView.FreezeCache.setValue(True)

        self.getLayerByName("Superpixels").visible = True
        th = threading.Thread(target=updateThread)
        th.start()
    '''

    @pyqtSlot(int)
    def on_RawData_channelChanged(self, channel):
        """
        update the layer-channel after the channel_box has changed its value
        """
        rawData_layer = self.getLayerByName(self.RawDataName)
        if rawData_layer:
            rawData_layer.channel = self.channel_box.value()
        


    def setupLayers(self):
        """
        Responsable for the elements in the 'Viewer Controls'
        These are the views (e.g. opacitiy of Raw Data)
        that can be adjusted in the left corner of the program
        And for the Elements, that can be seen in the 'Central Widget', 
        these are excactly the one, that are shown in the Viewer Controls

        """

        layers = []
        op = self.topLevelOperatorView

        '''
        # Superpixels
        if op.Superpixels.ready():
            layer = ColortableLayer( LazyflowSource(op.Superpixels), self._sp_colortable )
            layer.name = "Superpixels"
            layer.visible = True
            layer.opacity = 0.5
            layers.append(layer)
            del layer

        # Debug layers
        if op.debug_results:
            for name, compressed_array in op.debug_results.items():
                axiskeys = op.Superpixels.meta.getAxisKeys()[:-1] # debug images don't have a channel axis
                permutation = map(lambda key: axiskeys.index(key) if key in axiskeys else None, 'txyzc')
                arraysource = ArraySource( TransposedView(compressed_array, permutation) )
                if compressed_array.dtype == np.uint32:
                    layer = ColortableLayer(arraysource, self._sp_colortable)
                else:
                    layer = GrayscaleLayer(arraysource)
                    # TODO: Normalize? Maybe the drange should be included with the debug image.
                layer.name = name
                layer.visible = False
                layer.opacity = 1.0
                layers.append(layer)
                del layer

        # Threshold
        if op.ThresholdedInput.ready():
            layer = ColortableLayer( LazyflowSource(op.ThresholdedInput), self._threshold_colortable )
            layer.name = "Thresholded Input"
            layer.visible = True
            layer.opacity = 1.0
            layers.append(layer)
            del layer
        '''

        # Input Data (grayscale) (Probabilities)
        if op.Input.ready():
            layer = self._create_grayscale_layer_from_slot( op.Input, op.Input.meta.getTaggedShape()['c'] )
            layer.name = "Input"
            layer.visible = False
            layer.opacity = 1.0
            layers.append(layer)
            del layer

        """
        # Raw Data (grayscale)
        if op.RawData.ready():
            layer = self.createStandardLayerFromSlot( op.RawData )
            layer.name = "Raw Data"
            layer.visible = True
            layer.opacity = 1.0
            layers.append(layer)
            del layer
        """

        # Raw Data (grayscale) (should be seeds)
        if op.RawData.ready():
            layer = self._create_grayscale_layer_from_slot( op.RawData, op.RawData.meta.getTaggedShape()['c'] )
            #changing the Channel in the layer, 
            #changes the RawData Channel in the applet gui as well
            layer.channelChanged.connect(self.channel_box.setValue)
            #setValue() will emit valueChanged() if the new value is different from the old one.
            #not necessary: self.channel_box.valueChanged.emit(i)

            layer.name = self.RawDataName
            layer.visible = True
            layer.opacity = 1.0
            layers.append(layer)
            del layer


        return layers
