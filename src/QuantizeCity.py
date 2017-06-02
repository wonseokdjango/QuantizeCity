# -*- coding: utf-8 -*-

__author__ = "Wonseok Lee"

from qgis.core import *

import json
from urllib2 import urlopen

# define tunning constants
SAMPLING_RESOLUTION = 0.0000001
NBGW = 20 * 2;
NBGH = 20 * 2;
NSGW = 250 * 2;
NSGH = 250 * 2;

# define system paths
QGIS_PATH = "Your QGIS installation path"
GMAP_API_KEY = "Your Google Map Elevation API key"
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

def interpolation( _lat, _lng, _sgRow, _sgCol, _bgGrid):
	
	# bilinear interpolation of small grid
	# params
	#	_lat    : latitude of designated area
	#	_lng    : longitude of designated area
	#	_sgRow  : row index of small grid in row-major order
	#	_sgCol  : col index of small grid in row-major order
	#	_bgGrid : big grid
	# returns
	#	bilinear interpolated value of _lat, _lng area
	
	bgRow = _sgRow / NSGH
	bgCol = _sgCol / NSGW

	refer = [ [ 0, 0 ], [ 0, 0 ], [ 0, 0 ], [ 0, 0 ] ]
	if _sgRow % NSGH < NSGH / 2 and _sgCol % NSGW < NSGW / 2:
		refer[0] = [ bgRow - 1, bgCol - 1 ]
		refer[1] = [ bgRow - 1, bgCol ]
		refer[2] = [ bgRow, bgCol - 1 ]
		refer[3] = [ bgRow, bgCol ]
	elif _sgRow % NSGH < NSGH / 2 and _sgCol % NSGW >= NSGW / 2:
		refer[0] = [ bgRow - 1, bgCol ]
		refer[1] = [ bgRow - 1, bgCol + 1 ]
		refer[2] = [ bgRow, bgCol ]
		refer[3] = [ bgRow, bgCol + 1 ]
	elif _sgRow % NSGH >= NSGH / 2 and _sgCol % NSGW < NSGW / 2:
		refer[0] = [ bgRow, bgCol - 1 ]
		refer[1] = [ bgRow, bgCol ]
		refer[2] = [ bgRow + 1, bgCol - 1 ]
		refer[3] = [ bgRow + 1, bgCol ]
	elif _sgRow % NSGH >= NSGH / 2 and _sgCol % NSGW >= NSGW / 2:
		refer[0] = [ bgRow, bgCol ]
		refer[1] = [ bgRow, bgCol + 1 ]
		refer[2] = [ bgRow + 1, bgCol ]
		refer[3] = [ bgRow + 1, bgCol + 1]
	
	for r in refer:
		if r[0] < 0 or r[0] >= NBGH or r[1] < 0 or r[1] >= NBGW:
			return _bgGrid[bgRow][bgCol][2]

	x1 = _bgGrid[refer[0][0]][refer[0][1]][0]
	x2 = _bgGrid[refer[1][0]][refer[1][1]][0]
	y1 = _bgGrid[refer[0][0]][refer[0][1]][1]
	y2 = _bgGrid[refer[2][0]][refer[2][1]][1]
	q11 = _bgGrid[refer[0][0]][refer[0][1]][2]
	q21 = _bgGrid[refer[1][0]][refer[1][1]][2]
	q12 = _bgGrid[refer[2][0]][refer[2][1]][2]
	q22 = _bgGrid[refer[3][0]][refer[3][1]][2]

	if x1 == x2 or y1 == y2:
		return _bgGrid[bgRow][bgCol][2]

	term1 = ( ( x2 - _lng ) * ( y2 - _lat ) / float( ( x2 - x1 ) * ( y2 - y1 ) ) ) * q11
	term2 = ( ( _lng - x1 ) * ( y2 - _lat ) / float( ( x2 - x1 ) * ( y2 - y1 ) ) ) * q21
	term3 = ( ( x2 - _lng ) * ( _lat - y1 ) / float( ( x2 - x1 ) * ( y2 - y1 ) ) ) * q12
	term4 = ( ( _lng - x1 ) * ( _lat - y1 ) / float( ( x2 - x1 ) * ( y2 - y1 ) ) ) * q22

	return term1 + term2 + term3 + term4

def getBuildingHeight( _layer, _index, _lat, _lng ):
	
	# get builing height of designated area
	# params
	#	_layer : layer of QGIS data
	#   _index : spatial index of QGIS layer
	#   _lat   : latitude of designated area
	#   _lng   : longitude of designated area
	# returns
	#   builing height of designated area in meter

	rect = QgsRectangle(
			_lng - SAMPLING_RESOLUTION, _lat - SAMPLING_RESOLUTION,
			_lng + SAMPLING_RESOLUTION, _lat + SAMPLING_RESOLUTION)
	
	featIDs = _index.intersects( rect )
	if len( featIDs ) == 0:
		return 0.0
	
	_layer.setSelectedFeatures( featIDs )
	feat = _layer.selectedFeatures()

	height = 0.0
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
	#   none. output file will be generated

	# make big grid using Google Map Elevation API
	bigGrid = [ [ [ 0.0 for k in range( 3 ) ] for j in range( NBGW ) ] for i in range( NBGH ) ]
	bg_d_x = ( _LR[1] - _UL[1] ) / float( NBGW );
	bg_d_y = ( _UL[0] - _LR[0] ) / float( NBGH );

	for bgRow in range( NBGH ):
		for bgCol in range( NBGW ):
			x = _UL[1] + ( bgCol + 0.5 ) * bg_d_x
			y = _UL[0] - ( bgRow + 0.5 ) * bg_d_y
			bigGrid[bgRow][bgCol][0] = x
			bigGrid[bgRow][bgCol][1] = y
			bigGrid[bgRow][bgCol][2] = getLandElevation( y, x )

	# write grid
	grid = open( _gridPath, "w" )
	header0 = "%.15lf %.15lf %.15lf %.15lf\n" % ( _UL[0], _UL[1], _LR[0], _LR[1] )
	header1 = "%d %d %d %d\n" % ( NBGH, NBGW, NSGH, NSGW )
	grid.write( header0 + header1 )

	layer = QgsVectorLayer( _shpPath, "buildings", "ogr" )
	if not layer.isValid():
		notifyError( "QGIS layer loading is failed" )
	index = QgsSpatialIndex( layer.getFeatures() )
	
	sg_d_x = ( _LR[1] - _UL[1] ) / float( NSGW * NBGW );
	sg_d_y = ( _UL[0] - _LR[0] ) / float( NSGH * NBGH );

	for sgRow in range( NBGH * NSGH ):
		for sgCol in range( NBGW * NSGW ):
			x = _UL[1] + ( sgCol + 0.5 ) * sg_d_x
			y = _UL[0] - ( sgRow + 0.5 ) * sg_d_y
			bh = getBuildingHeight( layer, index, y, x )
			lh = interpolation( y, x, sgRow, sgCol, bigGrid )
			line = "%d %d %.15f %.15f %.15f %.15f\n" % (sgRow, sgCol, y, x, bh, lh)
			grid.write( line )
	grid.close()

if __name__ == "__main__":

	# main starts here !!!

	QgsApplication.setPrefixPath( QGIS_PATH, True )
	qcApp = QgsApplication( [], False )
	
	qcApp.initQgis()

	UL_lat = float( input( "Enter the upper left latitude   : " ) )
	UL_lng = float( input( "Enter the upper left longitude  : " ) )
	LR_lat = float( input( "Enter the lower right latitude  : " ) )
	LR_lng = float( input( "Enter the lower right longitude : " ) )
	shpPath = raw_input( "Enter the input shape file path : " )
	grdPath = raw_input( "Enter the output grid file path : " )

	if UL_lat <= LR_lat or UL_lng >= LR_lng:
		notifyError( "invalid upper left / lower right" )
	if NBGH % 2 != 0 or NBGW % 2 != 0 or NSGH % 2 != 0 or NSGW % 2 != 0:
		notifyError( "the number of grid is odd number" )
	
	generateGrid( [ UL_lat, UL_lng ], [ LR_lat, LR_lng ], shpPath, grdPath )

	qcApp.exitQgis()
