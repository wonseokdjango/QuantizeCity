# QuantizeCity
Quantizing city as **grid** and add **height attribute(land elevation + building height)** at single grid cell using QGIS
> **author** : won.seok.django@gmail.com  
> **last update** : 20170529
## I. 문서의 목적
---
이 문서는 서울시를 일정한 크기의 grid cell로 나누고, 각 grid cell에 cell을 대표할 수 있는 높이 정보(높이 = 지형고도 + 시설물고도)를 속성으로 붙여 raw data를 얻을 수 있는 방법에 대하여 설명합니다. 이는 아래의 목록과 같은 과정들을 포함합니다.
> 1. 위경도를 입력으로하여 해당 위치 시설물의 고도를 알아내는 방법을 개발
>> - python을 사용하여 개발하며, 행정자치부에서 공개하는 'GIS건물통합정보조회서비스' 데이터를 사용합니다. 이때, 데이터의 수월한 파싱을 위하여 QGIS 2.14.x Essen이 사용됩니다.
> 2. 위경도를 입력으로하여 해당 위치 지형의 고도를 알아내는 방법을 개발
>> - python을 사용하여 개발하며, 지형 고도를 위하여 Google Map이 제공하는 Land Elevation API가 사용됩니다.
> 3. 서울시의 특정 구간과 grid cell의 크기를 입력으로하여 서울시를 grid로 분할하고, 1, 2를 사용하여 각 grid cell에 지형 고도와 시설물 고도를 포함하는 높이 정보를 추가합니다. 이를 raw data로 추출하는 방법을 개발합니다.
>> - 전국 또는 특정 시도의 건물통합정보데이터는 다음 [링크](http://openapi.nsdi.go.kr/nsdi/eios/OpenapiList.do;jsessionid=3Z94DkIekBEEcHa5aql2LHCY.openapi11?provOrg=NIA&gubun=F)에서 .shp 포맷으로 무료 제공됩니다.

## II. 준비할 사항
---
개발 과정 전반에 python이 사용되므로 python2.7이 설치되어 있어야하며, QGIS 또한 설치되어 있어야합니다. 본 문서에서는 QGIS 2.14.x Essen을 ubuntu16.04에 설치하고, python2.7.12를 사용하는 것을 가정합니다. 사용되는 python, QGIS, OS 종류 및 버전은 얼마든지 변경하여 적용이 가능합니다. 본 문서에서 가정하는 환경에 대하여 각각의 다운로드 링크를 아래에 보입니다.
> 1. python 다운로드 [링크](https://www.python.org/downloads/)
> 2. QGIS 다운로드 [링크](http://www.qgis.org/ko/site/forusers/alldownloads.html)

## III. 함수 F : (위도, 경도) -> (시설물 고도) 개발
### III.1. 좌표변환
---
위도와 경도로 부터 시설물의 고도를 얻기 위해서는 행정자치부에서 공개하는 'GIS건물통합정보조회서비스'의 좌표계를 수정해주어야 합니다. 이는 행정자치부의 데이터는 한국 표준인 Korean 1985를 따르기 때문인데, 이는 추후 사용할 Google Map의 좌표계와 일치하지 않으므로 세계표준이자 Google Map이 차용하는 좌표계이기도 한 WGS84로 미리 변환해둡니다.
> 1. 우선 QGIS를 실행해서 '벡터 레이어 추가' -> '탐색'을 클릭하여 행정자치부의 GIS건물정보통합조회서비스 .shp 파일을 오픈합니다.
> 2. 상단 툴바에서 '레이어' -> '다른 이름으로 저장'을 클릭한 후 좌표계를 클릭합니다. 위에서 밝힌대로 Korean 1985로 지정되어 있는 것을 알 수 있습니다.
> 3. 좌표계를 WGS84로 변경해준 후 새 이름으로 저장해줍니다.
> 4. QGIS를 다시 시작하고 저장한 .shp 파일을 '벡터 레이어 추가' -> '탐색'을 클릭하여 불러옵니다. 이때 아래의 스크릿 샷이 보이는 것처럼 QGIS 최하단의 '좌표'란이 WGS84 경위도 형식으로 표현되고 있는 것을 확인합니다.  
> ![좌표변환](https://github.com/wonseokdjango/QuantizeCity/blob/master/img/CoordinateChange.png)

### III.2. Python 함수 작성
---
본격적으로 python을 이용하여 F : (위도, 경도) -> (시설물 고도)인 모듈을 작성합니다.
```python
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
```
위의 코드는 QGIS 레이어와 위경도를 입력으로 받아 해당 지점에 위치한 건물의 높이를 가져오는 코드입니다(레이어 및 QGIS 초기화에 관련한 코드는 QuantizeCity.py의 main scope에서 확인할 수 있습니다). 한편, **getBuildingHeight 함수는 입력받은 지점을 기준으로 0.000001만큼 padding을 넣은 정사각형 영역**을 선택하도록 합니다. 이러한 padding은 추후 GridMap의 resolution을 결정할 수 있는 중요한 인자이므로 상수 **SAMPLING_RESOLUTION**으로 따로 정의하도록 했습니다. 행정자치부의 데이터는 컬럼 A16에 건물의 높이 정보를 저장하고 있는데, 데이터를 확인해보니 종종 높이 값이 0.0으로 조사되지 않은 건물들이 있습니다. 이런 경우, 두 가지의 꼼수를 사용해 봅니다. 첫 번째로, 컬럼 A14에는 연면적이, 컬럼 A12에는 건축물면적이 저장되어 있으므로 두 값을 나누면 대략적인 건물의 층 수를 알 수 있습니다. 이 후 한 층의 높이를 대략 3.0m로 근사하여 건물의 높이를 구할 수 있습니다. 이 방법 역시 실패할 경우, 둘째로 용적률을 건폐율로 나눈 값을 층 수로 근사하는 꼼수를 사용해 볼 수 있습니다. 위의 코드가 이러한 꼼수를 보여줍니다.  

## IV. 함수 G : (위도, 경도) -> (지형 고도) 개발
### IV.1. Google Map API key 받기
---
위경도에 따른 지형의 고도 정보를 얻기 위해서는 우선 Google Map Elevation API의 키를 받아야 합니다. 아래 링크에 들어가서 받으면 되는데, 주의할 점으로는 **Google Map API는 반드시 Google Map에 데이터를 표시하기 위한 용도로만 사용되어야 하며**, 일일 요청이 **1건당 512개씩 2500건**으로 제한되어 있다는 점이 있습니다. 판사님 저는 분명히 이 프로젝트 마지막에는 Google Map에 데이터를 뿌려줄 겁니다.
> Google Map API key [링크](https://developers.google.com/maps/documentation/elevation/get-api-key?hl=ko)

### III.2. Python 함수 작성
---
본격적으로 python을 이용하여 F : (위도, 경도) -> (지형 고도)인 모듈을 작성합니다.

```python
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
		if response["status"] != "OK":
			keyPress = input( "url open error. continue? [y/n] : " )
			if keyPress == "n":
				exit()

		for result in response["results"]:
			ret.append( float( result["elevation"] ) )

	return ret
```
위의 코드는 경위도 리스트를 입력으로 받아 단순히 해당 지점의 지형고도를 리스트로 반환하는 예제 입니다. III.의 함수 F와 다르게 getLandElevation 함수가 리스트를 입력으로 받는 이유는 Google Map API는 하루에 한번에 최대 512개 지점을 쿼리할 수 있는 요청을 2500개만 허용하기 때문입니다. 따라서, 위의 코드와 같이 최대한 한 번에 많은(512개 씩 묶어서) 쿼리를 날리는 것이 경제적입니다.

## V. Grid 생성
### V.1. 기본 아이디어
---
위에서 정의한 함수들을 토대로 지형고도와 시설물고도를 함께 얻을 수 있는 Grid를 생성합니다. Grid를 생성하기 위한 기본 아이디어를 아래의 그림이 나타냅니다.
> ![그리드](https://github.com/wonseokdjango/QuantizeCity/blob/master/img/Grid.png)

위의 그림이 나타내는 것 처럼 지도에서 UL(Upper Left), LR(Lower Right)로 정의되는 사각형 영역을 붉은 실선이 나타내는 Big Grid와 푸른 점선이 나타내는 Small Grid로 분할합니다. 사용자가 UL과 LR의 위경도를 입력할 때, 위의 그림과 같은 Grid를 정의하기 위해 아래와 같은 상수들을 정의합니다.  
> 1. NBGH(the **N**umber of **B**ig grid along **H**eight) : 지도의 세로 방향 붉은 Grid의 갯수  
> 2. NBGW(the **N**umber of **B**ig grid along **W**idth) : 지도의 가로 방향 붉은 Grid의 갯수  
> 3. NSGH(the **N**umber of **S**mall grid along **H**eight) : 붉은 Grid 내 푸른 Grid의 세로 방향 갯수  
> 4. NSGW(the **N**umber of **S**mall grid along **W**idth) : 붉은 Grid 내 푸른 Grid의 가로 방향 갯수

위의 정의로부터 위의 그림은 (NBGH, NBGW, NSGH, NSGW) = (5, 6, 2, 2)임을 쉽게 알 수 있습니다. 특정 좌표 (lat, lng)가 주어질 때 해당지점의 높이 정보 H는 아래와 같이 정의할 수 있습니다.  
> ***H(lat, lng) = (lat, lng)이 속하는 붉은 Grid의 지형고도 + (lat, lng)이 속하는 푸른 Grid의 시설물 고도***

이는 전체 Grid가 NBGH * NBGW개의 지형고도 정보만을 사용하며, 하나의 붉은 Grid 안에 위치하는 NSGH * NSGW개의 푸른 Grid가 자신이 속하는 붉은 Grid의 지형고도 정보를 공유하는 것을 의미합니다. 추후 정밀도를 높이기 위에 위에서 밝힌 4개 상수를 tunning하거나 interpolation을 사용하는 방법을 고려해볼만 합니다. 이렇게 두 레벨의 Grid로 지도를 관리할 때는 크게 2가지의 이점이 있는데, 첫 째는 지형고도 API 일일 요청량의 균형을 조정할 수 있다는 점, 둘째, 하나의 레벨로 지도를 관리하는 경우의 superset이라는 점(NSGH, NSGW를 1로 설정하는 경우)이 있습니다.
### V.2. 출력파일 형식 정의
---
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
---
```python
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
		keyPress = input( "invalid upper left, lower right. continue? [y/n] : " )
		if keyPress == "n":
			exit()

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
	if not layer.isValid():
		keyPress = input( "QGIS layer loading is failed. continue? [y/n] : " )
		if keyPress == "n":
			exit()
	try:
		grid = open(_gridPath, "w")
	except IOError, e:
	 	keyPress = input( "file open error. continue? [y/n] : " )
	 	if keyPress == "n":
	 		exit()

	line = "%.15lf %.15lf %.15lf %.15lf\n" % (_UL[0], _UL[1], _LR[0], _LR[1])
	grid.write(line)
	line = "%d %d %d %d\n" % (NBGH, NBGW, NSGH, NSGW)
	grid.write(line)

	for sgRow in range( NBGH * NSGH ):
		for sgCol in range( NBGW * NSGW ):
			x = _UL[1] + ( sgCol + 0.5 ) * sg_d_x
			y = _UL[0] - ( sgRow + 0.5 ) * sg_d_y
			bh = getBuildingHeight( layer, y, x )
			lh = bigGrid[sgRow / NBGH][sgCol / NBGW]
			line = "%d %d %.15f %.15f %.15f %.15f\n" % (sgRow, sgCol, y, x, bh, lh)
			grid.write(line)
	grid.close()
```