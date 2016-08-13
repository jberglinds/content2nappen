# Jonathan Berglind, 2016
# jonatber@kth.se
from icalendar import Calendar, Event
from datetime import datetime, timedelta
import json, os

# Läser in en .ics-fil i samma mapp som skriptet.
filename = input('Filnamn på indatafil i .ics, (ex: \"backstage-cal.ics\"): ') or 'backstage-cal.ics'
with open(filename) as file:   
	cal = Calendar.from_ical(file.read())

	calendar_output = dict()
	index = 0
	for event in cal.walk("VEVENT"):
		startTime = event.get("DTSTART").dt+timedelta(hours=2) # nAppen tar UTC
		endTime = event.get("DTEND").dt+timedelta(hours=2)

		# Kollar efter heldagsevent, stödjer bara 1dags-event nu.
		daydiff = (endTime-startTime)/timedelta(hours=24)
		if daydiff % 1 == 0:
			allDay = "true"
		else:
			allDay = "false"

		calendar_output["event_%d" % index] = {
			"type" : "event",
			"title": str(event.get("SUMMARY")),
			"description" : str(event.get("DESCRIPTION")),
			"location" : {
				"lat" : "",
				"lng" : "",
				"name" : str(event.get("LOCATION"))
			},
			"allDay": allDay,
			"time": str(startTime.strftime("%Y-%m-%dT%H:%MZ")),
			"endTime": str(endTime.strftime("%Y-%m-%dT%H:%MZ"))
		}
		index = index+1

	outname = filename.replace(".ics", ".json")
	print("Dumpar fil till output/"+outname)
	os.makedirs("output/", exist_ok=True)
	with open('output/'+outname, 'w') as outfile:
		json.dump(calendar_output, outfile, indent=4, sort_keys=True)
		print("Done!")