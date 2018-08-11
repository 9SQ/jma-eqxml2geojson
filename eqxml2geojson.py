# -*- coding: utf-8 -*-
import sys, re
import csv, json
import sqlite3
from BeautifulSoup import BeautifulStoneSoup

argvs = sys.argv
argc = len(argvs)

if (argc != 4):
    print 'Usage: # python %s [centroid csvs dir] [input file(uuid.xml)] [output dir] ' % argvs[0]
    quit()

# JMAXMLのオープン
xmlFile = open(argvs[2],'r')
xml = BeautifulStoneSoup(xmlFile)

csvDir = argvs[1]
outputDir = argvs[3]

# sqlite3にcsvを都度展開する
connection = sqlite3.connect(":memory:")
cursor = connection.cursor()

# 細分区域レベルのテーブルを生成
cursor.execute("CREATE TABLE jma_area_centroid (jma_code INTEGER PRIMARY KEY, jma_name TEXT, lat REAL, lon REAL);")
with open(csvDir + "jma_area_centroid.csv",'rb') as fin:
    dr = csv.DictReader(fin, fieldnames = ('jma_code','jma_name','lat','lon'))
    to_db = [(c['jma_code'], unicode(c['jma_name'], "utf8"), c['lat'], c['lon']) for c in dr]
cursor.executemany("INSERT INTO jma_area_centroid (jma_code, jma_name, lat, lon) VALUES (?, ?, ?, ?);", to_db)
connection.commit()

# 市区町村レベルのテーブルを生成
cursor.execute("CREATE TABLE jma_city_centroid (jma_code INTEGER PRIMARY KEY, jma_name TEXT, lat REAL, lon REAL);")
with open(csvDir + "jma_city_centroid.csv",'rb') as fin:
    dr = csv.DictReader(fin, fieldnames = ('jma_code','jma_name','lat','lon'))
    to_db = [(c['jma_code'], unicode(c['jma_name'], "utf8"), c['lat'], c['lon']) for c in dr]
cursor.executemany("INSERT INTO jma_city_centroid (jma_code, jma_name, lat, lon) VALUES (?, ?, ?, ?);", to_db)
connection.commit()

# 震源の座標を取得
epicenterStr = xml.report.body.earthquake.hypocenter.area.find('jmx_eb:coordinate').string
# 分割
epicenterCoord = re.split(r'(\-|\+|\/)', epicenterStr)
# epicenterに入れる
epicenter = {"type":"Feature",
             "properties": {"class":"epicenter"},
             "geometry":{
                "type":"Point",
                "coordinates":[float(epicenterCoord[3] + epicenterCoord[4]), float(epicenterCoord[1] + epicenterCoord[2])]
                }
            }

# epicenterをfeaturesに入れる
areaLevelFeatures = [epicenter]
cityLevelFeatures = [epicenter]

# 各震度ごとにポイントを格納するリストpointsを定義
areaLevelPoints = [[] for i in range(0,9)]
cityLevelPoints = [[] for i in range(0,9)]

if xml.report.body.find('intensity'):

    # 各震度ごとにpointsにまとめる
    pref = xml.report.body.intensity.observation.findAll('pref')
    for p in pref:
        area = p.findAll('area')
        for a in area:
            cursor.execute("SELECT lat,lon,jma_name FROM jma_area_centroid WHERE jma_code=" + a.code.string)
            row = cursor.fetchone()
            if a.maxint is not None:
                maxint = a.maxint.string
            else:
                maxint = ""
            areaLevelFeatures.append({"type":"Feature","properties":{"class": maxint, "name": row[2]},"geometry":{"type":"Point","coordinates": [row[1],row[0]]}})
            city = a.findAll('city')
            for c in city:
                cursor.execute("SELECT lat,lon,jma_name FROM jma_city_centroid WHERE jma_code=" + c.code.string)
                row = cursor.fetchone()
                if c.maxint is not None:
                    maxint = c.maxint.string
                else:
                    maxint = ""
                cityLevelFeatures.append({"type":"Feature","properties":{"class": maxint, "name": row[2]},"geometry":{"type":"Point","coordinates": [row[1],row[0]]}})

# featuresをfeatureCollectionに追加
areaLevelFeatureCollection = {"type":"FeatureCollection","features":areaLevelFeatures}
cityLevelFeatureCollection = {"type":"FeatureCollection","features":cityLevelFeatures}

# jsonを出力
f = open(outputDir+'smallScalePoints.json', 'w')
f.write(json.dumps(areaLevelFeatureCollection))
f.close()

f = open(outputDir+'largeScalePoints.json', 'w')
f.write(json.dumps(cityLevelFeatureCollection))
f.close()

# 後処理
cursor.close()
connection.close()
xmlFile.close()