# Jonathan Berglind, 2016
# jonatber@kth.se
from icalendar import Calendar, Event
from datetime import datetime, timedelta
import json, os

output_object = dict()
event_index = 0
# Lägger till ett nytt event till objektet som sedan skrivs ut som .json
def addEvent(title, description, locationName, allDay, startTime, endTime):
	global event_index, output_object

	output_object["event_%d" % event_index] = {
		"type" : "event",
		"title": title,
		"description" : description,
		"location" : {
			"lat" : "",
			"lng" : "",
			"name" : locationName
		},
		"allDay": allDay,
		"time": str(startTime.strftime("%Y-%m-%dT%H:%MZ")),
		"endTime": str(endTime.strftime("%Y-%m-%dT%H:%MZ"))
	}
	event_index += 1

# Läser in en .ics-fil i samma mapp som skriptet.
filename = input('Filnamn på indatafil i .ics, (ex: \"backstage-cal.ics\"): ') or 'backstage-cal.ics'
with open(filename) as file:   
	cal = Calendar.from_ical(file.read())

	# Loopar över eventen från filen
	for event in cal.walk("VEVENT"):
		title = str(event.get("SUMMARY"))
		description = str(event.get("DESCRIPTION"))
		locationName = str(event.get("LOCATION"))

		# nAppen tar UTC så tiden måste eventuellt justeras här beroende på .ics-filen
		startTime = event.get("DTSTART").dt+timedelta(hours=2)
		endTime = event.get("DTEND").dt+timedelta(hours=2)

		# Kollar efter heldagsevent
		daydiff = (endTime-startTime)/timedelta(hours=24)

		if daydiff % 1 == 0 and daydiff is not 0:

			# nAppen kräver ett nytt event-objekt för varje dag i heldagseventet
			for x in range(0, int(daydiff)):
				# Heldagseventet för varje dag ska vara från 00 till 00
				temp_startTime = startTime+timedelta(hours=24*x)
				temp_endTime = temp_startTime+timedelta(hours=24)
				addEvent(title, description, locationName, "true", temp_startTime, temp_endTime)
		else:
			addEvent(title, description, locationName, "false", startTime, endTime)

	# Dumpa event-objektet till en .json-fil med liknande namn som indatafilen
	outname = filename.replace(".ics", ".json")
	print("Dumpar fil till output/"+outname)
	os.makedirs("output/", exist_ok=True)
	with open('output/'+outname, 'w') as outfile:
		json.dump(output_object, outfile, indent=4, sort_keys=True)
		print("Done!")