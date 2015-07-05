# -*- coding: utf-8 -*-
import sys, re
import csv, json
import sqlite3
from BeautifulSoup import BeautifulStoneSoup

argvs = sys.argv
argc = len(argvs)

if (argc != 2):
    print 'Usage: # python %s uuid.xml ' % argvs[0]
    quit()

# JMAXMLのオープン
xmlFile = open(argvs[1],'r')
xml = BeautifulStoneSoup(xmlFile)

# sqlite3にcsvを都度展開する
connection = sqlite3.connect(":memory:")
cursor = connection.cursor()

# 細分区域レベルのテーブルを生成
cursor.execute("CREATE TABLE jma_area_centroid (jma_code INTEGER PRIMARY KEY, jma_name TEXT, lat REAL, lon REAL);")
with open("jma_area_centroid.csv",'rb') as fin:
    dr = csv.DictReader(fin, fieldnames = ('jma_code','jma_name','lat','lon'))
    to_db = [(c['jma_code'], unicode(c['jma_name'], "utf8"), c['lat'], c['lon']) for c in dr]
cursor.executemany("INSERT INTO jma_area_centroid (jma_code, jma_name, lat, lon) VALUES (?, ?, ?, ?);", to_db)
connection.commit()

# 市区町村レベルのテーブルを生成
cursor.execute("CREATE TABLE jma_city_centroid (jma_code INTEGER PRIMARY KEY, jma_name TEXT, lat REAL, lon REAL);")
with open("jma_city_centroid.csv",'rb') as fin:
    dr = csv.DictReader(fin, fieldnames = ('jma_code','jma_name','lat','lon'))
    to_db = [(c['jma_code'], unicode(c['jma_name'], "utf8"), c['lat'], c['lon']) for c in dr]
cursor.executemany("INSERT INTO jma_city_centroid (jma_code, jma_name, lat, lon) VALUES (?, ?, ?, ?);", to_db)
connection.commit()

# 震源の座標を取得
epicenterStr = xml.report.body.earthquake.hypocenter.area.find('jmx_eb:coordinate').string
# 分割
epicenterCoord = re.split(r'\-|\+|\/', epicenterStr)
# epicenterに入れる
epicenter = {"type":"Feature",
             "properties": {"class":"epicenter"},
             "geometry":{
                "type":"Point",
                "coordinates":[float(epicenterCoord[2]), float(epicenterCoord[1])]
                }
            }

# epicenterをfeaturesに入れる
areaLevelFeatures = [epicenter]
cityLevelFeatures = [epicenter]

# 各震度ごとにポイントを格納するリストpointsを定義
areaLevelPoints = [[] for i in range(0,9)]
cityLevelPoints = [[] for i in range(0,9)]

# 各震度ごとにpointsにまとめる
pref = xml.report.body.intensity.observation.findAll('pref')
for p in pref:
    area = p.findAll('area')
    for a in area:
        cursor.execute("SELECT lat,lon FROM jma_area_centroid WHERE jma_code=" + a.code.string)
        row = cursor.fetchone()
        maxint = a.maxint.string
        if maxint == "1":
            areaLevelPoints[0].append({"type":"Point","coordinates": [row[1],row[0]]})
        elif maxint == "2":
            areaLevelPoints[1].append({"type":"Point","coordinates": [row[1],row[0]]})
        elif maxint == "3":
            areaLevelPoints[2].append({"type":"Point","coordinates": [row[1],row[0]]})
        elif maxint == "4":
            areaLevelPoints[3].append({"type":"Point","coordinates": [row[1],row[0]]})
        elif maxint == "5-":
            areaLevelPoints[4].append({"type":"Point","coordinates": [row[1],row[0]]})
        elif maxint == "5+":
            areaLevelPoints[5].append({"type":"Point","coordinates": [row[1],row[0]]})
        elif maxint == "6-":
            areaLevelPoints[6].append({"type":"Point","coordinates": [row[1],row[0]]})
        elif maxint == "6+":
            areaLevelPoints[7].append({"type":"Point","coordinates": [row[1],row[0]]})
        elif maxint == "7":
            areaLevelPoints[8].append({"type":"Point","coordinates": [row[1],row[0]]})
        city = a.findAll('city')
        for c in city:
            cursor.execute("SELECT lat,lon FROM jma_city_centroid WHERE jma_code=" + c.code.string)
            row = cursor.fetchone()
            maxint = c.maxint.string
            if maxint == "1":
                cityLevelPoints[0].append({"type":"Point","coordinates": [row[1],row[0]]})
            elif maxint == "2":
                cityLevelPoints[1].append({"type":"Point","coordinates": [row[1],row[0]]})
            elif maxint == "3":
                cityLevelPoints[2].append({"type":"Point","coordinates": [row[1],row[0]]})
            elif maxint == "4":
                cityLevelPoints[3].append({"type":"Point","coordinates": [row[1],row[0]]})
            elif maxint == "5-":
                cityLevelPoints[4].append({"type":"Point","coordinates": [row[1],row[0]]})
            elif maxint == "5+":
                cityLevelPoints[5].append({"type":"Point","coordinates": [row[1],row[0]]})
            elif maxint == "6-":
                cityLevelPoints[6].append({"type":"Point","coordinates": [row[1],row[0]]})
            elif maxint == "6+":
                cityLevelPoints[7].append({"type":"Point","coordinates": [row[1],row[0]]})
            elif maxint == "7":
                cityLevelPoints[8].append({"type":"Point","coordinates": [row[1],row[0]]})

# featuresに各震度ごとのpointsを追加
for n in range(0, 9):
    if len(areaLevelPoints[n]) != 0:
        areaLevelFeatures.append({"type":"Feature",
                                  "properties":{"class":n+1},
                                  "geometry":{
                                     "type":"GeometryCollection",
                                     "geometries":areaLevelPoints[n]
                                     }
                                 })
for n in range(0, 9):
    if len(cityLevelPoints[n]) != 0:
        cityLevelFeatures.append({"type":"Feature",
                                  "properties":{"class":n+1},
                                  "geometry":{
                                     "type":"GeometryCollection",
                                     "geometries":cityLevelPoints[n]
                                     }
                                 })

# featuresをfeatureCollectionに追加
areaLevelFeatureCollection = {"type":"FeatureCollection","features":areaLevelFeatures}
cityLevelFeatureCollection = {"type":"FeatureCollection","features":cityLevelFeatures}

# jsonを出力
f = open('smallScalePoints.json', 'w')
f.write(json.dumps(areaLevelFeatureCollection))
f.close()

f = open('largeScalePoints.json', 'w')
f.write(json.dumps(cityLevelFeatureCollection))
f.close()

# 後処理
cursor.close()
connection.close()
xmlFile.close()