import MySQLdb as mariadb
import json

# Det används HTML i vissa länkar från STÖn vilket nAppen inte har stöd för
from html.parser import HTMLParser
class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.strict = False
        self.convert_charrefs= True
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()

# Databasen är mySQL av typen mariadb
DB_NAME = "ston"
# Används i databasen och representerar året. 2016 = 11. Inkrementeras varje år
OCCURENCE_ID = 11 

mariadb_connection = mariadb.connect(user='root', db=DB_NAME)
cursor = mariadb_connection.cursor()

# Skapar en map från ett personal-id till en titel, typ "Dadderiet"/"Drifveriet"/"Lillasyster"
cursor.execute("SELECT staff_id, name, position_name, titel from participations p, branches b WHERE p.occurrence_id=%s AND p.branch_id=b.id", (OCCURENCE_ID,))
titleForStaff = dict()
for staff_id, name, position_name, titel in cursor:
	if titel == 1:
		# Om titel, namn på position istället för gren
		# Notera att titel tycker om att döpa sin position till något annat internt, typ "Mamma" -> "Soccer mom" 
		# vilket kanske inte blir så bra i nAppen
		titleForStaff[staff_id] = position_name
	else:
		titleForStaff[staff_id] = name

# Skapar en map från ett personal-id till ett person-objekt, som nAppen direkt kan tolka.
cursor.execute("SELECT id, email, first_name, last_name, cell_phone, login FROM staff")
staff = dict()
for id, email, first_name, last_name, cell_phone, login in cursor:
	staff[id] = {
			"email": email, 
			"name": first_name + " " + last_name,  
			"phone": cell_phone,
			"title": titleForStaff[id] if id in titleForStaff else "",
			"image": "https://zfinger.datasektionen.se/user/%s/image/" % login,
			"type": "person"
		}

# Skapar en map från ett ansvarsområdes-id till en array av personal-id'n som är ansvariga för området.
cursor.execute("SELECT responsibility_id, staff_id FROM assignments")
staffForResponsibility = dict()
for responsibility_id, staff_id in cursor:
	if responsibility_id in staffForResponsibility:
		staffForResponsibility[responsibility_id].append(staff_id)
	else: 
		staffForResponsibility[responsibility_id] = [staff_id]

# Plockar ut alla asnvarsområden som är aktiva för året (ej gömda) och skapar ett grupp-objekt som nAppen direkt kan tolka.
cursor.execute("SELECT id, title, description, notes, titel_contact_id FROM responsibilities WHERE occurrence_id=%s AND titel=0 AND upper(title) NOT LIKE \"%%LEGACY%%\" ORDER BY title", (OCCURENCE_ID,))
responsibilities_group = {}
for id, title, description, notes, titel_contact_id in cursor:
	responsible_staff = dict()
	if id in staffForResponsibility:
		for staffID in staffForResponsibility[id]:
			staffData = staff[staffID]
			responsible_staff[staffData["name"]] = staffData

	responsibilities_group[id] = {
		"groups": {
			"g_0": {
				"items" : {
					"i_0" : {
					"content" : strip_tags(description),
					"type" : "text"
		  			}
				}, 
				"title": "Beskrivning"
			},
			"g_1": {
				"items" : {
					"i_0" : {
					"content" : strip_tags(notes),
					"type" : "text"
		  			}
				}, 
				"title": "Att tänka på"
			},
			"g_2": {
				"items": responsible_staff,
				"title": "Ansvariga"
			},
			"g_3": {
				"items": {
					"i_0" : staff[titel_contact_id] if titel_contact_id in staff else None
				},
				"title": "Kontaktperson i Titel"
			},
			"g_4": {
				"items" : {
					"i_0" : {
					"content" : "http://ston.datasektionen.se/responsibilities/%d" % id,
					"type" : "text"
		  			}
				}, 
				"title": "STÖn"
			}
		},
		"image": "",
		"subtitle": "",
		"title": title
	}
	if notes == "":
		# Om "Att tänka på"-avsnittet inte fanns - Ta bort den gruppen helt.
		responsibilities_group[id]["groups"].pop("g_1", None)
		
# Dumpar objektet för ansvarsområden till en .json-fil
with open('responsibilities.json', 'w') as outfile:
	json.dump(responsibilities_group, outfile)
