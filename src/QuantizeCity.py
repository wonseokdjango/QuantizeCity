# -*- coding: utf-8 -*-

__author__ = "Wonseok Lee"

from qgis.core import *
import json
from urllib2 import urlopen

# define constants
SAMPLING_RESOLUTION = 0.000001
NBGW = 2;
NBGH = 2;
NSGW = 3;
NSGH = 3;

# define system paths
QGIS_PATH = "/usr/share/qgis"
GMAP_API_KEY = "AIzaSyB-WQIcBO85Yzd5FR7jFT_f4TNJKenRT5o"
GMAP_API_URL = "https://maps.googleapis.com/maps/api/elevation/json?locations="

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
		height = feat[0]['A16'];

	_layer.setSelectedFeatures( [] )

	return height
	
def getLandElevation( _locs ):
	
	# get land elevation of designated areas
	# params
	#   _locs : list of [latitude, longitude]
	# returns
	#   list of land elevation of desiganted areas in meter
	
	ret = []

	while len( _locs ) != 0:
		PARAMS = ""
		for idx in range( 511 ):
			if len( _locs ) <= 1:
				break
			loc = _locs.pop( 0 )
			PARAMS += "%s,%s|" % ( loc[0], loc[1] )

		loc = _locs.pop( 0 )
		PARAMS += "%s,%s&key=%s" % ( loc[0], loc[1], GMAP_API_KEY )
	
		fp = urlopen( GMAP_API_URL + PARAMS )
		response = json.loads( fp.read().decode() )

		for result in response["results"]:
			ret.append( float( result["elevation"] ) )
			
	return ret

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
	
	bigGrid = [ [ 0.0 ] * NBGW for row in range( NBGH ) ]
	bg_d_x = ( _LR[1] - _UL[1] ) / float( NBGW );
	bg_d_y = ( _UL[0] - _LR[0] ) / float( NBGH );

	req = []
	for bgRow in range( NBGH ):
		for bgCol in range( NBGW ):
			x = _UL[1] + ( bgCol + 0.5 ) * bg_d_x
			y = _UL[0] - ( bgRow + 0.5 ) * bg_d_y
			req.append( [ y, x ] )
	
	elev = getLandElevation( req )
	for bgRow in range( NBGH ):
		for bgCol in range( NBGW ):
			bigGrid[bgRow][bgCol] = elev.pop( 0 )

	sg_d_x = ( _LR[1] - _UL[1] ) / float( NSGW * NBGW );
	sg_d_y = ( _UL[0] - _LR[0] ) / float( NSGH * NBGH );

	layer = QgsVectorLayer( _shpPath, "Buildings", "ogr" )

	grid = open(_gridPath, "w");
	line = "%.15lf %.15lf %.15lf %.15lf\n" % (_UL[0], _UL[1], _LR[0], _LR[1])
	grid.write(line)
	line = "%d %d %d %d\n" % (NBGH, NBGW, NSGH, NSGW)
	grid.write(line)

	for sgRow in range( NBGH * NSGH ):
		for sgCol in range( NBGW * NSGW ):
			x = _UL[1] + ( sgCol + 0.5 ) * sg_d_x
			y = _UL[0] - ( sgRow + 0.5 ) * sg_d_y
			bh = getBuildingHeight( layer, y, x )
			lh = bigGrid[sgRow % NBGH][sgCol % NBGW]
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
