# QuantizeCity

Quantizing city as **grid** and adding **height attribute(land elevation + building height)** at single grid cell using QGIS

> **author** : won.seok.django@gmail.com

> **last update** : 20170602

## I. 문서의 목적

이 문서는 서울시를 일정한 크기의 grid cell로 나누고, 각 grid cell에 cell을 대표할 수 있는 높이 정보(높이 = 지형고도 + 시설물고도)를 속성으로 붙여 raw data를 얻을 수 있는 방법에 대하여 설명합니다. 이는 아래의 목록과 같은 과정들을 포함합니다.

> * 위경도를 입력으로하여 해당 위치 **시설물의 고도**를 알아내는 방법을 개발

>>> python을 사용하여 개발하며, 행정자치부에서 공개하는 'GIS건물통합정보조회서비스' 데이터를 사용합니다. 이때, 데이터의 수월한 파싱을 위하여 QGIS 2.14.x Essen이 사용됩니다.

> * 위경도를 입력으로하여 해당 위치 **지형의 고도**를 알아내는 방법을 개발

>>> python을 사용하여 개발하며, 지형 고도를 위하여 Google Map이 제공하는 Land Elevation API가 사용됩니다.

> * 서울시의 특정 구간과 grid cell의 크기를 입력으로하여 서울시를 grid로 분할하고, 1, 2를 사용하여 각 grid cell에 지형 고도와 시설물 고도를 포함하는 높이 정보를 추가합니다. 이를 raw data로 추출하는 방법을 개발합니다.

>>> 전국 또는 특정 시도의 건물통합정보데이터는 다음 [링크](http://openapi.nsdi.go.kr/nsdi/eios/OpenapiList.do;jsessionid=3Z94DkIekBEEcHa5aql2LHCY.openapi11?provOrg=NIA&gubun=F)에서 .shp 포맷으로 무료 제공됩니다.

추가적으로 Appendix에서는 다음과 같은 사항에 대하여 기술합니다.

> * 구해진 raw data를 DB에 업로드하고 조작하기

> * 구성한 DB에 날린 쿼리와 실측값을 통해 검증하기

> * 한계

## II. 준비할 사항

개발 과정 전반에 python이 사용되므로 python2.7이(대부분의 linux 배포판에 기본으로 설치되어 있음) 설치되어 있어야하며, QGIS 또한 설치되어 있어야합니다. 본 문서에서는 QGIS 2.14.x Essen을 ubuntu16.04에 설치하고, python2.7.12를 사용하는 것을 가정합니다. 사용되는 QGIS, OS 종류 및 버전은 얼마든지 변경하여 적용이 가능합니다. 본 문서에서 가정하는 환경에 대하여 각각의 다운로드 링크를 아래에 보입니다.

> 1. python 다운로드 [링크](https://www.python.org/downloads/)
> 2. QGIS 다운로드 [링크](http://www.qgis.org/ko/site/forusers/alldownloads.html)

## III. 함수 F : (위도, 경도) -> (시설물 고도) 개발

### III.1. 좌표변환

위도와 경도로 부터 시설물의 고도를 얻기 위해서는 행정자치부에서 공개하는 'GIS건물통합정보조회서비스'의 좌표계를 수정해주어야 합니다. 이는 행정자치부의 데이터는 한국 표준인 Korean 1985를 따르기 때문인데, 이는 추후 사용할 Google Map의 좌표계와 일치하지 않으므로 세계표준이자 Google Map이 차용하는 좌표계이기도 한 WGS84로 미리 변환해둡니다.

> 1. 우선 QGIS를 실행해서 '벡터 레이어 추가' -> '탐색'을 클릭하여 행정자치부의 GIS건물정보통합조회서비스 .shp 파일을 오픈합니다.

> 2. 상단 툴바에서 '레이어' -> '다른 이름으로 저장'을 클릭한 후 좌표계를 클릭합니다. 위에서 밝힌대로 Korean 1985로 지정되어 있는 것을 알 수 있습니다.

> 3. 좌표계를 WGS84로 변경해준 후 새 이름으로 저장해줍니다.

> 4. QGIS를 다시 시작하고 저장한 .shp 파일을 '벡터 레이어 추가' -> '탐색'을 클릭하여 불러옵니다. 이때 아래의 스크릿 샷이 보이는 것처럼 QGIS **최하단의 '좌표'란이 WGS84 경위도 형식으로 표현**되고 있는 것을 확인합니다.  

> ![좌표변환](https://github.com/wonseokdjango/QuantizeCity/blob/master/img/CoordinateChange.png)

### III.2. Python 함수 작성

본격적으로 python을 이용하여 F : (위도, 경도) -> (시설물 고도)인 모듈을 작성합니다.

```python

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

```

위의 코드는 QGIS 레이어와 위경도를 입력으로 받아 해당 지점에 위치한 건물의 높이를 가져오는 코드입니다(QGIS 초기화에 관련한 코드는 QuantizeCity.py의 main scope에서 확인할 수 있습니다). 한편, **getBuildingHeight 함수는 입력받은 지점을 기준으로 0.000001만큼 padding을 넣은 정사각형 영역**을 선택하도록 합니다. 이러한 padding은 추후 GridMap의 resolution을 결정할 수 있는 중요한 인자이므로 상수 **SAMPLING_RESOLUTION**으로 따로 정의하도록 했습니다. 행정자치부의 데이터는 컬럼 A16에 건물의 높이 정보를 저장하고 있는데, 데이터를 확인해보니 종종 높이 값이 0.0으로 조사되지 않은 건물들이 있습니다. 이런 경우, 두 가지의 꼼수를 사용해 봅니다. 첫 번째로, 컬럼 A14에는 연면적이, 컬럼 A12에는 건축물면적이 저장되어 있으므로 두 값을 나누면 대략적인 건물의 층 수를 알 수 있습니다. 이 후 한 층의 높이를 대략 3.0m로 근사하여 건물의 높이를 구할 수 있습니다. 이 방법 역시 실패할 경우, 둘째로 용적률을 건폐율로 나눈 값을 층 수로 근사하는 꼼수를 사용해 볼 수 있습니다. 위의 코드가 이러한 꼼수를 보여줍니다.  

## IV. 함수 G : (위도, 경도) -> (지형 고도) 개발

### IV.1. Google Map API key 받기

위경도에 따른 지형의 고도 정보를 얻기 위해서는 우선 Google Map Elevation API의 키를 받아야 합니다. 아래 링크에 들어가서 받으면 되는데, 주의할 점으로는 **Google Map API는 반드시 Google Map에 데이터를 표시하기 위한 용도로만 사용되어야 하며**, 일일 요청이 **1건당 최대 512개씩 2500개**로 제한되어 있다는 점이 있습니다. 판사님 저는 분명히 이 프로젝트 마지막에는 Google Map에 데이터를 뿌려줄 겁니다.

> Google Map API key [링크](https://developers.google.com/maps/documentation/elevation/get-api-key?hl=ko)

### III.2. Python 함수 작성

본격적으로 python을 이용하여 G : (위도, 경도) -> (지형 고도)인 모듈을 작성합니다.

```python

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

```

딱히 코멘트를 달 이유가 없을 정도로 straigt forward합니다. 위에서 밝혔던 2가지 꼼수가 적용되고 있는 것을 알 수 있습니다.

## V. Grid 생성

### V.1. 기본 아이디어

위에서 정의한 함수들을 토대로 지형고도와 시설물고도를 함께 얻을 수 있는 Grid를 생성합니다. Grid를 생성하기 위한 기본 아이디어를 아래의 그림이 나타냅니다.

> ![그리드](https://github.com/wonseokdjango/QuantizeCity/blob/master/img/Grid.png)

위의 그림이 나타내는 것 처럼 지도에서 UL(Upper Left), LR(Lower Right)로 정의되는 사각형 영역을 붉은 실선이 나타내는 Big Grid와 푸른 점선이 나타내는 Small Grid로 분할합니다. 사용자가 UL과 LR의 위경도를 입력할 때, 위의 그림과 같은 Grid를 정의하기 위해 아래와 같은 상수들을 정의합니다.  

> 1. NBGH(the **N**umber of **B**ig grid along **H**eight) : 지도의 세로 방향 붉은 Grid의 갯수  

> 2. NBGW(the **N**umber of **B**ig grid along **W**idth) : 지도의 가로 방향 붉은 Grid의 갯수  

> 3. NSGH(the **N**umber of **S**mall grid along **H**eight) : 붉은 Grid 내 푸른 Grid의 세로 방향 갯수  

> 4. NSGW(the **N**umber of **S**mall grid along **W**idth) : 붉은 Grid 내 푸른 Grid의 가로 방향 갯수

위의 정의로부터 위의 그림은 (NBGH, NBGW, NSGH, NSGW) = (5, 6, 2, 2)임을 쉽게 알 수 있습니다. 특정 좌표 (lat, lng)가 주어질 때 해당지점의 높이 정보 H는 아래와 같이 정의할 수 있습니다.  

> ***H(lat, lng) = (lat, lng)이 속하는 붉은 Grid의 지형고도 + (lat, lng)이 속하는 푸른 Grid의 시설물 고도***

붉은 Grid를 듬성듬성 구성함으로써 Google Map API의 일일 요청량 제한을 맞출 수는 있게 되었지만, 하나의 붉은 Grid에 존재하는 모든 푸른 Grid가 하나의 지형 고도 값(자신이 속하는 붉은 Grid)을 공유하는 건 비합리적입니다. 따라서, 하나의 붉은 Grid안에 존재하는 각각의 푸른 Grid들에 대해서는 bilnear interpolation을 수행해줍니다. bilinear interpolation을 위해 하나의 푸른 Grid는 4개의 점을 bilinear interploation을 위한 reference로 삼아야합니다. 4개의 referene의 선정기준은 다음과 같습니다.  

> 자신이 속한 붉은 Grid의 지형 고도 값을 1개의 reference로 삼습니다.  

> 자신이 속한 붉은 Grid에서 가장 가까운 붉은 Grid 3개를 나머지 referene로 삼습니다.

위의 기준은 그림으로 나타내보면 이해가 쉬운데, 아래의 그림에서 노란색 Grid의 지형고도를 보간하게 되는 경우에는 빨간색과 파란색 점을 reference로, 노란색 Grid의 우측에 위치한 Grid를 보간하게 되는 경우 파란색과 초록색 점을 reference로 삼게됩니다.   

> ![보간](https://github.com/wonseokdjango/QuantizeCity/blob/master/img/Interpolation.png)  

이러한 보간 과정은 소스코드의 interpolation 함수에서 확인할 수 있습니다.

### V.2. 출력파일 형식 정의

파일로 Grid정보를 출력할 때 출력파일의 포맷은 다음과 같습니다. 아래에서 모든 부동소수점은 소수점 아래 15자리까지 표현됩니다.

```

UL위도 UL경도 LR위도 LR경도

NBGH NBGW NSGH NSGW

SmallGrid행번호 SmallGrid열번호 SmallGrid중심위도 SmallGrid중심경도 SmallGrid중심시설물고도 SmallGrid중심지형고도

SmallGrid행번호 SmallGrid열번호 SmallGrid중심위도 SmallGrid중심경도 SmallGrid중심시설물고도 SmallGrid중심지형고도

...

SmallGrid행번호 SmallGrid열번호 SmallGrid중심위도 SmallGrid중심경도 SmallGrid중심시설물고도 SmallGrid중심지형고도

```

### V.3. Python 함수 구현

```python

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

```

## Appendix

### Appendix.1. DB에 데이터 업로드

서울시에 대해 (NBGH, NBGW, NSGH, NSGW) = (40, 40, 500, 500)정도로 위에서 작성한 프로그램을 수행하면 대략 30GB 정도되는 텍스트파일이 만들어집니다. 이는 in-memory로 처리하기에는 매우 빡세보입니다. 따라서, DB를 구성하도록 합니다. 서버에 DB설치, python 연동을 위한 package 받기 등은 아래의 링크에 매우 친절히 설명되어 있습니다.

> ![MariaDB-python 연동](https://mariadb.com/resources/blog/how-connect-python-programs-mariadb)

아래 그림은 schema라고 부르기도 창피할 정도로 간단한 GridMap schema입니다. 아래 스키마를 그대로 서버에 업로드 합니다.

> ![스키마](https://github.com/wonseokdjango/QuantizeCity/blob/master/img/ERD.png)

이제 서버에서 gird 파일의 내용을 읽어 생성한 데이터베이스에 업로드 합니다. DB와의 연동에는 PyMySQL 패키지가 사용됩니다. 아래는 Server에서 grid 파일의 내용을 DB에 업로드하는 python 코드입니다.

```python

#-*- coding: utf-8 -*-

__author__ = "Wonseok Lee"

import pymysql

MAXCHUNK = 100000	# tune this constant

if __name__ == "__main__":

	# main starts here !!!

	con = pymysql.connect(
			host    = "localhost"    ,
			port    = 3306           ,
			user    = "Your DB user" ,
			passwd  = "Your DB pswd" ,
			db      = "Your DB name" ,
			charset = "utf8" )
	
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

	cursor.close()

```

### Appendix.2. 검증

열심히 database에 구한 grid를 업로드 했으니 이제 DB에 select 쿼리를 요청하는 client 코드를 만들어보고 옳은 값을 반환하는지 확인해 봅니다. 사용자가 위도와 경도를 입력했을 때, 해당 grid의 높이 정보를 반환하는 client 코드는 아래와 같습니다. 아래는 예제코드로 UL, LR, 그리드 갯수 등을 파일에서 얻어오고 있지만, 추후에 meta table을 사용하여 해당 정보를 얻어올 수도 있습니다.

```python

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

```

> ![검증입력](https://github.com/wonseokdjango/QuantizeCity/blob/master/img/v_ref.png)

위의 서울시 3D 지도를 보면 봉천초등학교 (37.480837, 126.960076) 지역에는 17.4m 짜리의 건물이 64.7m의 지형 위에 세워져있습니다.

> ![검증출력](https://github.com/wonseokdjango/QuantizeCity/blob/master/img/v_chk.png)

해당 좌표를 Client.py를 사용해서 조회해보니 위와 같이 결과를 얻을 수 있습니다. 비교적 적은 오차로 정보가 얻어진 것을 알 수 있습니다.


### Appendix.3. 한계점

이 문서에서 밝힌 grid map 데이터 구성은 아래와 같은 한계점을 갖습니다.

> - 지형 고도를 얻기 위한 grid가 40x40으로 interpolation을 해도 무시할 수 없을 정도의 지형고도 오차가 존재합니다.

> - 건물 하나는 모양과 상관 없이 단 하나의 건물 높이 정보를 갖습니다.

