#-*- coding: utf-8 -*-

__author__ = "Wonseok Lee"

import math
import pymysql

def getMeta( _gridPath ):

	grid = open( _gridPath, "r" )
	ul_lat, ul_lng, lr_lat, lr_lng = grid.readline().split()
	nbgh, nbgw, nsgh, nsgw = grid.readline().split()
	grid.close()

	ul_lat = float( ul_lat )
	ul_lng = float( ul_lng )
	lr_lat = float( lr_lat )
	lr_lng = float( lr_lng )
	nbgh = float( nbgh )
	nbgw = float( nbgw )
	nsgh = float( nsgh )
	nsgw = float( nsgw )

	d_lat = ( ul_lat - lr_lat ) / ( nbgh * nsgh )
	d_lng = ( lr_lng - ul_lng ) / ( nbgw * nsgw )

	return [ [ ul_lat, ul_lng ], [ lr_lat, lr_lng ], [ d_lat, d_lng ] ]

def getRecord( _cur, _ul, _lr, _delta, _lat, _lng ):

	# get Record at _lat, _lng from DB
	# params
	#	_cur   : current cursor of _con
	#	_ul    : upper left latitude, longitude
	#	_lr    : lower right latitude, longitude
	#	_delta : delta latitude, logitude between two adjacent grid
	#	_lat   : latitude of designated area
	#	_lng   : longitude of designated area
	# returns
	#	none. print selected record

	query = "select * from Seoul_40x40_500x500 where ROW = %s and COL = %s"
	
	row = int( ( _ul[0] - _lat ) / _delta[0] )
	col = int( ( _lng - _ul[1] ) / _delta[1] )

	_cur.execute( query, ( row, col ) )
	result = _cur.fetchall()

	print( result )

if __name__ == "__main__":

	# main starts here !!!

	con = pymysql.connect(
			host    = "Your DB host" ,
			port    = 3306           ,
			user    = "Your DB user" ,
			passwd  = "Your DB pswd" ,
			db      = "Your DB name" ,
			charset = "utf8" )
	
	cursor = con.cursor()
	
	gridPath = raw_input( "insert grid file path : " )

	ul, lr, delta = getMeta( gridPath )

	while True:
		lat = float( input( "lat : " ) )
		lng = float( input( "lng : " ) )
		if lat == -1.0 or lng == -1.0:
			break;
		getRecord( cursor, ul, lr, delta, lat, lng )

	cursor.close()
