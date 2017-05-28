# -*- coding: utf-8 -*-

__author__ = "Wonseok Lee"
__email__  = "won.seok.django@gmail.com"

from qgis.core import *

QgsApplication.setPrefixPath( "/usr/share/qgis", True )
qcApp = QgsApplication( [], False )

qcApp.initQgis()

layerName     = "Buildings"
shapeFilePath = "/home/wonseok/git/QuantizeCity/BuildingData/BuildingData.shp"
layer = QgsVectorLayer( shapeFilePath, layerName, "ogr" )

if not layer.isValid():
	print "layer loading is failed"
else:
	print "layer loading successes"

qcApp.exitQgis()
