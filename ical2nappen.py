# Jonathan Berglind, 2016
# jonatber@kth.se
#
# Det här skriptet konverterar en .ics-fil (ical) till .json som nAppen
# kan läsa.
#
# ical-standarden har ganska mycket konstigt för sig, bland annat när
# ett event i ett gäng återkommande ändras.
# Det blev därför ganska rörigt :)
from icalendar import Calendar, Event
from datetime import datetime, timedelta
from pytz import timezone
from dateutil.rrule import *
from dateutil.parser import *
import json, os, pytz

TIMEZONE = pytz.timezone("Europe/Stockholm")

output_object = dict()

event_index = 0
# Lägger till ett nytt event till objektet som sedan dumpas som .json
def addEvent(title, description, locationName, allDay, startTime, endTime):
	global event_index, output_object

	if hasattr(startTime, 'tzinfo'):
		# Konvertera till UTC som nAppen tar om tidszon finns angiven.
		startTime = TIMEZONE.normalize(startTime)
		endTime = TIMEZONE.normalize(endTime)
	else:
		# Om ingen tidszon antar vi bara att det ligger 2h off.
		startTime = startTime+timedelta(hours=2*x)
		endTime = endTime+timedelta(hours=2*x)

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

	recurringEvents = dict()

	# Loopar över eventen från filen
	for event in cal.walk("VEVENT"):
		title = str(event.get("SUMMARY"))
		description = str(event.get("DESCRIPTION"))
		locationName = str(event.get("LOCATION"))

		startTime = event.get("DTSTART").dt
		endTime = event.get("DTEND").dt
		duration = endTime - startTime

		# Återkommande event?
		#
		# Dessa anges som ett event i ical-filen med en regel som säger
		# vilka dagar det händer på. Ex:
		# RRULE:FREQ=WEEKLY;COUNT=2;BYDAY=SU,MO,TU,WE,TH,FR,SA
		#
		# nAppen har ingen funktion för återkommande event, därför
		# måste dessa expanderas till ett event för varje dag.
		# Dessutom finns det fall då ett av eventen i ett gäng
		# återkommande ändras, typ får annan tid eller annan beskrivning.
		# I detta läge skapas ett separat event i ical-filen med ett
		# "RECCURENCE_ID" som pekar på eventet som skrivs över.
		#
		# Här expanderas ett återkommande event till ett för varje dag
		# och läggs sedan åt sidan för att eventuellt skrivas över sen.
		rule = event.get("RRULE")
		if rule is not None:
			rrset = rruleset()
			rrset.rrule(rrulestr(rule.to_ical().decode("utf-8"), dtstart=startTime))
			# Datum att exkludera?
			exdates = event.get("EXDATE")
			if exdates is not None and hasattr(exdates, 'dts'):
				for edate in exdates.dts:
					rrset.exdate(edate.dt)

			for date in list(rrset):
				recurringEvents[str(date)] = {
					"startTime": date,
					"endTime": date+duration,
					"location": locationName,
					"title": title,
					"description": description
				}

		# Ej återkommande event, dessa kan direkt läggas in i output.
		else:
			# Kollar om ett event ska skriva över något återkommande
			# Alltså om det har något recurrence-id.
			recurrenceID = event.get("RECURRENCE-ID")
			if recurrenceID is not None:
				recurringEvents.pop(str(recurrenceID.dt))

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

	# Lägger till de återkommande eventen som vi tidigare lade undan.
	for key, val in recurringEvents.items():
		addEvent(val["title"], val["description"], val["location"], "false", val["startTime"], val["endTime"])

	# Dumpa event-objektet till en .json-fil med liknande namn som indatafilen
	outname = filename.replace(".ics", ".json")
	print("Dumpar fil till output/"+outname)
	os.makedirs("output/", exist_ok=True)
	with open('output/'+outname, 'w') as outfile:
		json.dump(output_object, outfile, indent=4, sort_keys=True)
		print("Done!")
