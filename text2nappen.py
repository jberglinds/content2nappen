# Jonathan Berglind, 2016
# jonatber@kth.se
#
# Det här skriptet konverterar .json i en form till .json på den formen
# som nAppen kan läsa. Se typ links.json som är en indatafil.
#
# Varför? firebase som nAppen använder klarar av någon anledning inte
# av arrayer, bara dicts. Det gör allt onödigt komplicerat när man ska
# skriva det själv. Det här är ett försök att göra det lite enklare att
# lägga in just text till info-modulen.
import json, os

# Läser in en .json-fil i samma mapp som skriptet.
filename = input('Filnamn på indatafil i .json, (ex: \"games.json\"): ') or 'games.json'
with open(filename) as data_file:
	data = json.load(data_file)

	output_object = {}
	# Traverserar indata och bygger utdata som nAppen kan tolka
	index = 0
	for item in data["content"]:

		text_groups = dict()
		item_index = 0
		for textitem in item["textitems"]:
			text_groups["g_%d" % item_index] = {
				"items": {
					"i_0": {
						"content": textitem["text"],
						"type": "text"
					}
				},
				"title": textitem["text_title"]
			}
			item_index += 1


		output_object["group_%d" % index] = {
			"groups": text_groups,
			"image": item["image"],
			"subtitle": item["subtitle"],
			"title": item["title"]
		}
		index += 1

	# Dumpar objektet med utdata till en .json-fil med liknande namn som indatafilen
	outname = filename.replace(".json", "-out.json")
	print("Dumpar fil till output/"+outname)
	os.makedirs("output/", exist_ok=True)
	with open('output/'+outname, 'w') as outfile:
		json.dump(output_object, outfile, indent=4, sort_keys=True)
		print("Done!")
