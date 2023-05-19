DEST:=/usr/bin
THUMB_FOLDER:=/usr/share/thumbnailers
MIME:=/usr/share/mime

install:
	/usr/bin/pip3 install -r requirements.txt
	cp ${CURDIR}/src/ansi-thumbnailer.py ${DEST}/ansi-thumbnailer
	chmod a+rx ${DEST}/ansi-thumbnailer

	cp ${CURDIR}/src/ansi-thumbnailer.xml ${MIME}/packages/
	update-mime-database ${MIME}

	cp ${CURDIR}/src/ansi.thumbnailer ${THUMB_FOLDER}/
	echo "Installation completed!"

uninstall:
	rm ${DEST}/ansi-thumbnailer
	rm ${THUMB_FOLDER}/ansi.thumbnailer
	rm ${MIME}/packages/ansi-thumbnailer.xml

update: uninstall install
