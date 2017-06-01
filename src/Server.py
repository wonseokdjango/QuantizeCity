#-*- coding: utf-8 -*-

__author__ = "Wonseok Lee"

import pymysql

MAXCHUNK = 100000

if __name__ == "__main__":

	# main starts here !!!

	con = pymysql.connect(
			host       = "localhost" ,
			port       = 3306        ,
			user       = "Your ID"	 ,
			passwd     = "Your PW"   ,
			db         = "Your DB"   ,
			charset    = "utf8" )
	
	cursor = con.cursor()
	query = """	insert into 
				Seoul_40x40_500x500(ROW, COL, LAT, LNG, LAND_ELEVATION, BUILDING_HEIGHT) 
				values (%s, %s, %s, %s, %s, %s) """

	gridPath = raw_input( "insert grid file path : " )
	
	lineNo = 0
	with open( gridPath ) as grid:
		for line in grid:
			
			if len( line.split() ) != 6:
				continue
			
			r, c, lat, lng, bh, lh = line.split()
			r = int( r )
			c = int( c )
			lat = float( lat )
			lng = float( lng )
			bh = float( bh )
			lh = float( lh )
			
			cursor.execute( query, ( r, c, lat, lng, lh, bh ) )
			
			lineNo = lineNo + 1
			if lineNo % MAXCHUNK == 0:
				con.commit()
				print "commit !"

	cursor.close()
