@echo off
call "C:\OSGeo4W64\bin\o4w_env.bat"
call "C:\OSGeo4W64\bin\qt5_env.bat"
call "C:\OSGeo4W64\bin\py3_env.bat"

@echo on
C:\Program Files\QGIS 3.10\apps\Python37\Scripts\pyrcc5 -o resources.py resources.qrc