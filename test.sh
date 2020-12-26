folders=("/" "/modules" "/Web_Server")

for path in ${folders[@]}
do
	for entrypy in "$PWD""$path"/*.py
	do
		sudo chmod 511 "$entrypy"
	done
	sudo chmod 511 "$PWD""$path"
done

for entrysh in "$PWD"/*.sh
do
	sudo chmod 511 "$entrysh"
done

sudo chmod 777 "$PWD""/config.json"
