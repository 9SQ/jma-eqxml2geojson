jma-eqxml2geojson
======

Earthquake Information XML from JMA(Japan Meteorological Agency) to GeoJSON

気象庁防災情報XML電文の**震度速報**、**震源・震度に関する情報**から、区域別の震度(数値)情報と重心(緯度経度)をGeoJSONで出力します。
これにより、地図上の当該区域の上に震度をマッピングしたりできます。

出力されるのは**smallScalePoints.json**と**largeScalePoints.json**です。

smallScalePoints.json : 震源地と細分区域(188区域)の重心座標、震度を含むGeoJSON  
largeScalePoints.json : 震源地と市町村等(1898区域)の重心座標、震度を含むGeoJSON  

### ファイル

* eqxml2geojson.py : プログラム(python2)
* f0e017f4-d9df-3741-8e7a-fc7837cbeffc.xml : サンプルXML電文  
(2016年4月14日 21:26分頃に熊本県熊本地方で発生した、最大震度7を観測した地震のXML電文)

## 実行方法

※要 BeautifulSoup (BeautifulStoneSoup)

[jma-eqarea-centroid](https://github.com/9SQ/jma-eqarea-centroid) から jma_area_centroid.csv と jma_city_centroid.csv を取得し、 eqxml2geojson.py と同じディレクトリに入れて実行

※jma-eqarea-centroidは市制移行や市区町村の統廃合などがあった際に追従して更新予定です。Watchしておくことをお勧めします。

```
python eqxml2geojson.py [centroid csvs dir] [input file(uuid.xml)] [output dir] 
```

例：同梱のサンプル電文からGeoJSONを得る
```
git clone https://github.com/9SQ/jma-eqarea-centroid.git
python eqxml2geojson.py ./jma-eqarea-centroid/ f0e017f4-d9df-3741-8e7a-fc7837cbeffc.xml ./
```

指定したディレクトリに smallScalePoints.json と largeScalePoints.json が出力されます。

## 出力されるGeoJSONのフォーマット
```
{
   "type":"FeatureCollection",
   "features":[
      {
         "geometry":{
            "type":"Point",
            "coordinates":[
               <震源地の経度>,
               <震源地の緯度>
            ]
         },
         "type":"Feature",
         "properties":{
            "class":"epicenter"
         }
      },
      {
         "geometry":{
            "type":"GeometryCollection",
            "geometries":[
               {
                  "type":"Point",
                  "coordinates":[
                     <震度Nの地域の経度>,
                     <震度Nの地域の緯度>
                  ]
               },
               ...(中略)...
               {
                  "type":"Point",
                  "coordinates":[
                     <震度Nの地域の経度>,
                     <震度Nの地域の緯度>
                  ]
               }
            ]
         },
         "type":"Feature",
         "properties":{
            "class":<震度(1,2,3,4,5-,5+,6-,6+,7)>,
            "name":<地域名>
         }
      },
      ...(中略)...
      {
         "geometry":{
            "type":"GeometryCollection",
            "geometries":[
               {
                  "type":"Point",
                  "coordinates":[
                     <震度Nの地域の経度>,
                     <震度Nの地域の緯度>
                  ]
               }
            ]
         },
         "type":"Feature",
         "properties":{
            "class":<震度(1,2,3,4,5-,5+,6-,6+,7)>,
            "name":<地域名>
         }
      }
   ]
}
```
