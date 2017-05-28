# QuantizeCity
Quantizing city as **grid** and add **height attribute** at single grid cell using QGIS
> author : won.seok.django@gmail.com

> last update : 20170528

## I. 문서의 목적

이 문서는 서울시를 일정한 크기의 grid cell로 나누고, 각 grid cell에 cell을 대표할 수 있는 높이 정보(높이 = 지형고도 + 시설물고도)를 속성으로 붙여 raw data를 얻을 수 있는 방법에 대하여 설명합니다. 이는 아래의 목록과 같은 과정을 포함합니다.

> 1. 위경도를 입력으로하여 해당 위치 시설물의 고도를 알아내는 방법을 개발
>> * *python을 사용하여 개발하며, 행정자치부에서 공개하는 'GIS건물통합정보조회서비스' 데이터를 사용합니다. 이때, 데이터의 수월한 파싱을 위하여 QGIS 2.14.x Essen이 사용됩니다.*

> 2. 위경도를 입력으로하여 해당 위치 지형의 고도를 알아내는 방법을 개발
>> * *python을 사용하여 개발하며, 지형 고도를 위하여 Google Map이 제공하는 API가 사용됩니다.*

> 3. 서울시의 특정 구간과 grid cell의 크기를 입력으로하여 서울시를 grid로 분할하고, 1, 2를 사용하여 각 grid cell에 높이 정보를 추가합니다. 이를 raw data로 추출하는 방법을 개발합니다.
>> * *전국 또는 특정 시도의 건물통합정보데이터는 다음 [링크](http://openapi.nsdi.go.kr/nsdi/eios/OpenapiList.do;jsessionid=3Z94DkIekBEEcHa5aql2LHCY.openapi11?provOrg=NIA&gubun=F)에서 .shp 포맷으로 무료 제공됩니다.*

## II. 준비할 사항

개발 과정 전반에 python이 사용되므로 python이 설치되어 있어야하며, QGIS 또한 설치되어 있어야합니다. 본 문서에서는 QGIS 2.14.x Essen을 ubuntu16.04에 설치하고, python2.7.12를 사용하는 것을 가정합니다. 사용되는 python, QGIS, OS 종류 및 버전은 얼마든지 변경하여 적용이 가능합니다. 본 문서에서 가정하는 환경에 대하여 각각의 다운로드 링크를 아래에 보입니다.

> 1. python 다운로드 [링크](https://www.python.org/downloads/)

> 2. QGIS 다운로드 [링크](http://www.qgis.org/ko/site/forusers/alldownloads.html)

## III. F : (위도, 경도) -> (시설물 고도) 개발

### III.1. 좌표변환

위도와 경도로 부터 시설물의 고도를 얻기 위해서는 행정자치부에서 공개하는 'GIS건물통합정보조회서비스'의 좌표계를 수정해주어야 합니다. 이는 행정자치부의 데이터는 한국 표준인 Korean1985를 따르기 때문인데, 이는 추후 사용할 Google Map의 좌표계와 일치하지 않으므로 세계표준이자 Google Map이 차용하는 좌표계이기도 한 WGS84로 미리 변환합니다.

> 1. 우선 QGIS를 실행해서 '벡터 레이어 추가' -> '탐색'을 클릭해서 행정자치부의 GIS건물정보통합조회서비스 쉐이프 파일을 오픈합니다.

> 2. 상단 툴바에서 '레이어' -> '다른 이름으로 저장'을 클릭한 후 좌표계를 클릭합니다. 위에서 밝힌대로 Korean1985로 지정되어 있는 것을 알 수 있습니다.

> 3. 좌표계를 표준이자 구글 맵에서 사용되는 WGS84로 변경해준 후 새 이름으로 저장해줍니다.

> 4. QGIS를 다시 시작하고 저장한 쉐이프파일을 '벡터 레이어 추가' -> '탐색'을 클릭하여 불러옵니다. 이때 아래의 스크릿 샷이 보이는 것처럼 QGIS 최하단의 '좌표'란이 WGS84 경위도 형식으로 표현되고 있는 것을 확인합니다.

> ![좌표변환](깃헙이미지/CoordinateChange.png)

### III.2. Python 함수 작성

본격적으로 python을 이용하여 F : (위도, 경도) -> (시설물 고도)인 모듈을 작성합니다. 



