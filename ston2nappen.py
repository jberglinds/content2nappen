# Jonathan Berglind, 2016
# jonatber@kth.se
import MySQLdb as mariadb
import json, os

# Det används HTML i vissa länkar från STÖn vilket nAppen inte har stöd för.
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

# Plockar bort all HTML från en sträng.
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

# Skapar en map från ett personal-id till ett person-objekt i nAppen
cursor.execute("SELECT id, email, first_name, last_name, cell_phone, login FROM staff")
staff = dict()
for id, email, first_name, last_name, cell_phone, login in cursor:
	staff[id] = {
			"email": email, 
			"name": first_name + " " + last_name,  
			"phone": cell_phone,
			"title": titleForStaff[id] if id in titleForStaff else "",
			"image": "https://zfinger.datasektionen.se/user/%s/image/320" % login,
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

# Skapar en map från ett ansvarsområdes-id till en array av personal-id'n som är ansvariga för området.
cursor.execute("SELECT responsibility_id, name FROM branches_responsibilities r, branches b WHERE r.branch_id = b.id")
branchnameForResponsibility = dict()
for responsibility_id, name in cursor:
		branchnameForResponsibility[responsibility_id] = name

def responsibilities2json():
	# Plockar ut alla ansvarsområden som är aktiva för året (ej de gömda) och skapar ett grupp-objekt i nAppen
	cursor.execute("SELECT id, title, description, notes, titel_contact_id FROM responsibilities WHERE occurrence_id=%s AND titel=0 AND upper(title) NOT LIKE \"%%LEGACY%%\" ORDER BY title", (OCCURENCE_ID,))
	responsibilities_group = {}
	for id, title, description, notes, titel_contact_id in cursor:

		# Skapar ett objekt som består av person-objekten för de ansvariga personerna
		responsible_staff = dict()
		if id in staffForResponsibility:
			for staffID in staffForResponsibility[id]:
				staffData = staff[staffID]
				responsible_staff[staffData["name"]] = staffData

		# Skapar själva sidan för ett ansvarsområde
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
						# Lägger till person-objektet för ansvarig titel om det finns någon
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
			"subtitle": branchnameForResponsibility[id] if id in branchnameForResponsibility else "",
			"title": title
		}
		if notes == "":
			# Om "Att tänka på"-avsnittet inte fanns - Ta bort den gruppen helt.
			responsibilities_group[id]["groups"].pop("g_1", None)
			
	# Dumpar objektet för ansvarsområden till en .json-fil
	os.makedirs("output/", exist_ok=True)
	print("Dumpar fil till output/responsibilities-out.json")
	with open('output/responsibilities-out.json', 'w') as outfile:
		json.dump(responsibilities_group, outfile, indent=4, sort_keys=True)
		print("Done!")


# Skapar en map från ett n0lle-id till ett person-objekt i nAppen
cursor.execute("SELECT id, first_name, last_name, username FROM n0llan")
n0llan = dict()
for id, first_name, last_name, username in cursor:
	n0llan[id] = { 
			"name": first_name + " " + last_name,  
			"title": "nØllan",
			"number": "",
			"email": "",
			"image": "https://zfinger.datasektionen.se/user/%s/image/320" % username if ((username is not "") and (username is not None)) else "",
			"type": "person"
		}

# Skapar en map från ett n0llegrupps-id till en array av n0lle-id'n som är med i gruppen.
cursor.execute("SELECT n0llegroup_id, id FROM n0llan")
n0llanFor0group = dict()
for n0llegroup_id, id in cursor:
	if n0llegroup_id in n0llanFor0group:
		n0llanFor0group[n0llegroup_id].append(id)
	else: 
		n0llanFor0group[n0llegroup_id] = [id]

# Skapar en map från ett n0llegrupps-id till en array av personal-id'n som är favvodaddor för gruppen.
cursor.execute("SELECT n0llegroup_id, id FROM staff WHERE n0llegroup_id IS NOT NULL;")
daddorFor0group = dict()
for n0llegroup_id, id in cursor:
	if n0llegroup_id in daddorFor0group:
		daddorFor0group[n0llegroup_id].append(id)
	else: 
		daddorFor0group[n0llegroup_id] = [id]

def n0llegroups2json():
	# Skapar en map från ett 0-grupps id till ett namn, typ 7 -> "Gubben i Månen"
	cursor.execute("SELECT id, name FROM n0llegroups")
	n0llegroups_group = {}
	for id, name in cursor:

		# Skapar ett objekt som består av person-objekten för de ansvariga personerna (favvodaddor)
		responsible_staff = dict()
		if id in daddorFor0group:
			for staffID in daddorFor0group[id]:
				staffData = staff[staffID]
				responsible_staff[staffData["name"]] = staffData

		# Skapar ett objekt som består av person-objekten medlemmarna i gruppen
		members = dict()
		if id in n0llanFor0group:
			for n0lleID in n0llanFor0group[id]:
				memberData = n0llan[n0lleID]
				members[memberData["name"]] = memberData

		n0llegroups_group[name] = {
			"groups": {
				"g_0": {
					"items": responsible_staff,
					"title": "Favoritdaddor"
				},
				"g_1": {
					"items": members,
					"title": "nØllan"
				}
			},
			"image": "",
			"subtitle": "",
			"title": name
		}
		
	# Dumpar objektet för n0llegrupper till en .json-fil
	print("Dumpar fil till output/n0llegroups-out.json")
	os.makedirs("output/", exist_ok=True)
	with open('output/n0llegroups-out.json', 'w') as outfile:
		json.dump(n0llegroups_group, outfile, indent=4, sort_keys=True)
		print("Done!")


def main():
	responsibilities2json()
	n0llegroups2json()

main()