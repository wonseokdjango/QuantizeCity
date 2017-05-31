# -*- coding: utf-8 -*-

__author__ = "Wonseok Lee"

from qgis.core import *
import json
from urllib2 import urlopen

# define tunning constants
SAMPLING_RESOLUTION = 0.0000001
NBGW = 25 * 2;
NBGH = 25 * 2;
NSGW = 250 * 2;
NSGH = 250 * 2;

# define system paths
QGIS_PATH = "Your QGIS Installation Path"
GMAP_API_KEY = "Your Google Map Elevation API Key"
GMAP_API_URL = "https://maps.googleapis.com/maps/api/elevation/json?locations="

def notifyError( _msg ):
	
	# notify error and request user input
	# params
	#	_msg : error message want to show
	# returns
	#	none. program is suspended when user input is not "y"

	keyPress = input( _msg + " continue? [y/n]" )
	if keyPress != "y":
		exit()

def interpolation( _locs ):



def getBuildingHeight( _layer, _lat, _lng ):
	
	# get builing height of designated area
	# params
	#   _layer : layer of QGIS
	#   _lat   : latitude of designated area
	#   _lng   : longitude of designated area
	# returns
	#   builing height of designated area in meter

	rect = QgsRectangle(
			_lng - SAMPLING_RESOLUTION, _lat - SAMPLING_RESOLUTION,
			_lng + SAMPLING_RESOLUTION, _lat + SAMPLING_RESOLUTION)
	
	_layer.select( rect, False )
	feat = _layer.selectedFeatures()

	height = 0.0
	if len(feat) == 1:
		if feat[0]['A16'] != 0:
			height = feat[0]['A16'];
		elif feat[0]['A12'] != 0.0:
			height = 3.0 * ( feat[0]['A14'] / feat[0]['A12'] )
		elif feat[0]['A17'] != 0.0:
			height = 3.0 * ( feat[0]['A18'] / feat[0]['A17'] )

	_layer.setSelectedFeatures( [] )

	return height
	
def getLandElevation( _lat, _lng ):
	
	# get land elevation of designated areas
	# params
	#	_lat : latitude of designated area
	#	_lng : latitude of designated area
	# returns
	#   land elevation of designated area in meter

	addr = GMAP_API_URL + "%s,%s&key=%s" % ( _lat, _lng, GMAP_API_KEY )
	
	fp = urlopen( addr )
	response = json.loads( fp.read().decode() )
	if response["status"] != "OK":
		notifyError( "url open error" )

	for result in response["results"]:
		return float( result["elevation"] )	

def generateGrid( _UL, _LR, _shpPath, _gridPath ):

	# generate grid map and store it as file
	# params
	#   _UL        : [latitude, longitude] of upper left corner
	#   _LR        : [latitude, longitude] of upper left corner
	#   _shpPath   : shape file path
	#   _gridPath  : output grid file path
	# returns
	#   none. output file is generated
	
	_UL = [ float( i ) for i in _UL ]
	_LR = [ float( i ) for i in _LR ]
	if ( _LR[1] - _UL[1] ) <= 0.0 or ( _UL[0] - _LR[0] ) <= 0.0:
		notifyError( "invalid upper left, lower right" )
	
	bigGrid = [ [ 0.0 ] * NBGW for row in range( NBGH ) ]
	bg_d_x = ( _LR[1] - _UL[1] ) / float( NBGW );
	bg_d_y = ( _UL[0] - _LR[0] ) / float( NBGH );

	for bgRow in range( NBGH ):
		for bgCol in range( NBGW ):
			x = _UL[1] + ( bgCol + 0.5 ) * bg_d_x
			y = _UL[0] - ( bgRow + 0.5 ) * bg_d_y
			bigGrid[bgRow][bgCol] = getLandElevation( y, x )
	
	try:
		grid = open( _gridPath, "w" )
	except IOError, e:
	 	notifyError( "file open error" )

	header0 = "%.15lf %.15lf %.15lf %.15lf\n" % ( _UL[0], _UL[1], _LR[0], _LR[1] )
	header1 = "%d %d %d %d\n" % ( NBGH, NBGW, NSGH, NSGW )
	grid.write( header0 + header1 )

	layer = QgsVectorLayer( _shpPath, "buildings", "ogr" )
	if not layer.isValid():
		notifyError( "QGIS layer loading is failed" )
	
	sg_d_x = ( _LR[1] - _UL[1] ) / float( NSGW * NBGW );
	sg_d_y = ( _UL[0] - _LR[0] ) / float( NSGH * NBGH );

	for sgRow in range( NBGH * NSGH ):
		for sgCol in range( NBGW * NSGW ):
			x = _UL[1] + ( sgCol + 0.5 ) * sg_d_x
			y = _UL[0] - ( sgRow + 0.5 ) * sg_d_y
			bh = getBuildingHeight( layer, y, x )
			lh = bigGrid[sgRow / NSGH][sgCol / NSGW]
			line = "%d %d %.15f %.15f %.15f %.15f\n" % (sgRow, sgCol, y, x, bh, lh)
			grid.write(line)
	
	grid.close()
			
if __name__ == "__main__":

	# main starts here !!!

	QgsApplication.setPrefixPath( QGIS_PATH, True )
	qcApp = QgsApplication( [], False )
	
	qcApp.initQgis()

	UL_lat = input( "Enter the upper left latitude   : " )
	UL_lng = input( "Enter the upper left longitude  : " )
	LR_lat = input( "Enter the lower right latitude  : " )
	LR_lng = input( "Enter the lower right longitude : " )
	shpPath = raw_input( "Enter the input shape file path : " )
	grdPath = raw_input( "Enter the output grid file path : " )

	generateGrid( [ UL_lat, UL_lng ], [ LR_lat, LR_lng ], shpPath, grdPath )

	qcApp.exitQgis()
