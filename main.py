import requests
from requests.auth import HTTPBasicAuth
import configparser
import os
import re
from tqdm import tqdm

# Konfigurationsdatei laden
config = configparser.ConfigParser()
config.read('config.ini')

api_url = 'https://elearning.uni-oldenburg.de/api.php/'
username = config['API']['Username']
password = config['API']['Passwort']

numberOfTutors = int(config['Tutoren']['AnzahlDerTutoren'])
tutorNumber = 0
blattnummer = "01"
tutorBuchstabe = config['Tutoren']['TutoriumBuchstabe']
folder = {
    "01" : "ecf95c808f6de460e2e83967f6fdbf63",
    "02" : "2f6769357a73b6c9ac05d3211ba31506",
    "03" : "ee25e8aa068ebe1ab58179535e7c86df", # true 3
    #"03" : "ba5ae74b68c42a71151622485dcb7c95", # Test Dir
    "04" : "de9389fa5ff655544ad466cf85c3ef2c",
    "05" : "ed8d814bf7194fb20a1e16f3280e244b",
    "06" : "4c6060f0dabd520a335fc918e98ea4ca",
    "07" : "757e87a92fd31b89e66132479d906800",
    "08" : "2363f537d1e31267608865ffe55d6633",
    "09" : "b16c0331fd035e92a460e46704e63b29",
    "10" : "ccaffde24683bfe7a162f6ff842fe097",
    "11" : "983a93d9c057721e7c5d7176a9b0d9f4",
    "12" : "ccf26d8dba03104091f1a02c595af097",
    "13" : "c54e3e6d8684b78940d14a6841895669",
    
}
# ADFIBJGC
tuturBuchstabeInNummer = {
    "A": 0,
    "D": 1,
    "F": 2,
    "I": 3,
    "B": 4,
    "J": 5,
    "G": 6,
    "C" :7
}

tutorNumberPicker = {
    "01" : [0, 1, 2, 3, 4, 5, 6, 7],
    "02" : [7, 0, 1, 2, 3, 4, 5, 6],
    "03" : [6, 7, 0, 1, 2, 3, 4, 5], 
    "04" : [5, 6, 7, 0, 1, 2, 3, 4],
    "05" : [4, 5, 6, 7, 0, 1, 2, 3],
    "06" : [3, 4, 5, 6, 7, 0, 1, 2],
    "07" : [2, 3, 4, 5, 6, 7, 0, 1],
    "08" : [1, 2, 3, 4, 5, 6, 7, 0],
    "09" : [1, 2, 3, 4, 5, 6, 7, 0],
    "10" : [0, 1, 2, 3, 4, 5, 6, 7],
    "11" : [7, 0, 1, 2, 3, 4, 5, 6],
    "12" : [6, 7, 0, 1, 2, 3, 4, 5],
    "13" : [5, 6, 7, 0, 1, 2, 3, 4]
}



genFalscheAbgaben = True

# Blattnummer, Tutornummer, Falsche Abgaben 
print("Wilkommen beim AutoDownloader!")
numberInputIncomplete = True
tutorInputIncomplete = True
genFalscheAbgabenIncomplete = True

while numberInputIncomplete:
    try:
        number = int(input("Welches Übungsblatt? UE"))
        if(number <= 0 or number > 100):
            raise ValueError
        numberInputIncomplete = False
        if number < 10:
            blattnummer = "0"+str(number)
        else:
            blattnummer = str(number)    
    except ValueError:
        print("Ungültige Eingabe. Bitte geben eine Zahl zwichen 0 und 14 ein.")
print(f"Übungsblatt UE{blattnummer} ausgewählt.")

if(config['Tutoren']['UseTutoriumBuchstabe'] == True):
    tutorInputIncomplete = False

valdidCofig = True
while tutorInputIncomplete:
    tutorien = "ADFIBJGC"
    if(config['Tutoren']['UseTutoriumBuchstabe'] == 'Ja' and valdidCofig):
        tutorInputIncomplete = False
        print(f"Willkommen zurück Tutor {tutorBuchstabe}")
    else:
        try:
            tutorBuchstabe = input("Welcher Tutor bist du? ")
            tutorBuchstabe = tutorBuchstabe.upper()
            if(tutorBuchstabe not in tutorien):
                raise ValueError
            tutorInputIncomplete = False
            print(f"Willkommen zurück Tutor {tutorBuchstabe}")
        except ValueError:
            print("Ungültige Eingabe. Bitte geben einen Buchstaben zwichen A und J ein.")
            continue
    try:
        number = tuturBuchstabeInNummer[tutorBuchstabe]
        tutorNumber = tutorNumberPicker[blattnummer][number]
    except Exception:
        tutorInputIncomplete = True
        valdidCofig = False
        print("Etwas ist schief gelaufen :/ Bitte versuche es manuell")


while genFalscheAbgabenIncomplete:
    try:
        str = input("E-Mail-Liste mit den falschen Abgaben generieren (y/n)? ")
        if str == 'n':
            genFalscheAbgaben = False
        elif str == 'y':
            genFalscheAbgaben = True
        else:        
            raise ValueError
        genFalscheAbgabenIncomplete = False
    except ValueError:
        print("Ungültige Eingabe. Wähle y = ja oder n = nein.")

# Restliche Config
pattern = f"^UE{blattnummer}_\w+(\[\d+\])?\.zip$" #^UE\d{2}_\w+(\[\d+\])?\.zip$
#patternTeam = f'UE{blattnummer}_(.*?)\.zip' 

patternTeam = f'UE{blattnummer}_([\w\s]+)(?:\[.*\])?\.zip'
targetDir = os.path.normpath(config['Dateien']['Speicherort']) 

try:
   os.makedirs(targetDir)
   print(f'Downloadordner mit dem Pfad {targetDir} erstellt')
except FileExistsError:
   # Ordner gibt es schon
   pass


class Abgabe:
    def __init__(self, id, name, userID, date):
        self.id = id
        self.name = name
        self.userID = userID
        self.date = date
    def __repr__(self):
        return repr(self.name)
    def fileExtension(self):
        return os.path.splitext(self.name)
    def getNameID(self):
        return extract_team_name(self.name)
    #   return self.userID
    def equals(self, abgabe) -> bool:
        if self.userID == abgabe.userID and self.name != abgabe.name:
            return True
        else:
            return False

# Sortiert die Abgaben in gleich große Stücke
def split_list(lst):
    avg = len(lst) // numberOfTutors
    remainder = len(lst) % numberOfTutors
    result = [lst[i * avg + min(i, remainder):(i + 1) * avg + min(i + 1, remainder)] for i in range(numberOfTutors)]
    return result

# Extrahiert den Teamnamen aus dem Dateiname
def extract_team_name(file_name):
    match = re.match(patternTeam, file_name)
    if match:
        extracted_text = match.group(1)
        return extracted_text
    else:
        return None

def extract_team_name_from_Abgabe(abgabe):
    return abgabe.userID
    match = re.match(patternTeam, abgabe.name)
    if match:
        extracted_text = match.group(1)
        return extracted_text
    else:
        return None

def getDate(abgabe):
    return abgabe.date


response = requests.get(f'{api_url}/folder/{folder[blattnummer]}/files?limit=500', auth=HTTPBasicAuth(username, password))

if response.status_code == 200:
    data = response.json()
    lenght = len(data['collection'])
    files = []
    fileNames = []
    illegalFiles = []
    illegalUserIDs = []
    #pbar = tqdm(total=lines, unit="files")
    print(f"Es gibt {lenght} Dateien im Abgabeordner. Schätzung: {lenght}/{numberOfTutors} = {lenght/numberOfTutors}.")
    print("Analysiere alle Dateien im Abgabeordner auf korrektem Namen.", end="")
    for i in range(0, lenght):
        fileName = data['collection'][i]['name']
        fileID = data['collection'][i]['id']
        userID = data['collection'][i]['user_id']
        date = data['collection'][i]['chdate']

        match = re.search(pattern, fileName)
        if match:
            files.append(Abgabe(fileID, fileName, userID, date))
            fileNames.append(fileName)
        else:
            illegalFiles.append(Abgabe(fileID, fileName, userID, date))
    print(" - Fertig!")

    # Keep latest Version
    print("Behalte nur die neuste Abgabe von jedem Team.", end="")
    #files.sort(key=extract_team_name_from_Abgabe)
    filebyID = {}
    for file in files:
        filebyID[file.getNameID()] = file

    uniqueID = filebyID.keys()
    filebyID = {}
    for id in uniqueID:
        filebyID[id] = []
    
    for file in files:
        temparray = filebyID[file.getNameID()]
        temparray.append(file)
        filebyID[file.getNameID()] = temparray

    newestfiles = []

    for id in uniqueID:
        filebyID[id].sort(key=getDate, reverse=True)
        newestfiles.append(filebyID[id][0])
    print(" - Fertig!")

    files = sorted(newestfiles, key=lambda abgabe: abgabe.name, reverse=True)    
    print(f"Dateien sind sortiert! Es gibt {len(files)} valide Abgaben. Schätzung: {len(files)}/{numberOfTutors} = {len(files)/numberOfTutors}.") 
    
    if genFalscheAbgaben:
        for file in illegalFiles:
            if file.userID not in illegalUserIDs:
                illegalUserIDs.append(file.userID)

        emails = ""
        count = 0
        filePath = os.path.join(targetDir,'falscheAbgaben.txt')
        pbar = tqdm(illegalUserIDs, unit="User")
        pbar.set_description("Erstelle Liste von Usern mit falscher Abgabe.")
        for user in pbar:
            response = requests.get(api_url+'/user/'+user, auth=HTTPBasicAuth(username, password)).json()
            emails = emails + response['email']+";"
            count = count + 1
        if emails != '':
            with open(filePath, "w") as file:
                file.write(emails)
            print(f"Die Falschen-Abgaben-Datei wurde erfolgreich gespeichert. Es haben insgesamt {count} Personen eine falsche Datei hochgeladen.")
        else:
            print(f"Die Falschen-Abgaben-Datei wird nicht erzeugt. Es haben keine Personen eine falsche Datei hochgeladen.")


    filesToDownload = split_list(files)
    allAbgaben = files
    teams = ""
    emailList = {}
    print(f"Du bekommst heute den {tutorNumber}. Teil. Es gibt die Teile 0 bis 7")
    if len(filesToDownload[tutorNumber]) > 0:
        pbar = tqdm(filesToDownload[tutorNumber], unit="Datei")
        pbar.set_description("Lade Dateien herunter")
        for file in pbar:
            team = extract_team_name(file.name)
            pbar.set_description(f"Lade {team}")
            dowloadrequest = requests.get(f'{api_url}file/{file.id}/download', auth=HTTPBasicAuth(username, password))
            if dowloadrequest.status_code == 200:
                if teams == "":
                    teams = team+";"
                else:
                    teams = teams+"\n"+team+";"
                filePath = os.path.join(targetDir, file.name)    
                with open(filePath, "wb") as downloadedfile:
                    downloadedfile.write(dowloadrequest.content)
                    #print(f"Die Datei {file.id} wurde erfolgreich heruntergeladen und als '{file.name}' gespeichert. Sie gehört dem Team {team}")
            else:
                print(f"Fehler beim Herunterladen der Datei {file.id}. Statuscode: {response.status_code}")
            request = requests.get(api_url+'/user/'+file.userID, auth=HTTPBasicAuth(username, password))
            if request.status_code == 200:
                emailList[team] = request.json()['email']
        print("Alle Dateien wurden erfolgreich heruntergeladen.")
    else:
        print("Es gibt keine Dateien zum Runterladen.")
    filePath = os.path.join(targetDir, f'mailList_{blattnummer}.txt') 
    with open(filePath, "w") as file:
        emailList_string = "\n".join([f'{key}: {value}' for key, value in emailList.items()])
        file.write(emailList_string)
    print(f"Die E-Mail-Liste für die Rückgabe wurde erfolgreich erstellt.")
    
    filePath = os.path.join(targetDir,f'score_{tutorBuchstabe}_{blattnummer}.csv')
    with open(filePath, "w") as file:
        file.write(teams)
    print(f"Die score.csv-Datei wurde erfolgreich erstellt.")


    filePath = os.path.join(targetDir,f'Verteilung_UE{blattnummer}.txt')
    tutoren = "ADFIBJGC"
    string = "" 
    with open(filePath, "w") as file:
        

        for buchstabe in tutoren:
            number = tuturBuchstabeInNummer[buchstabe]
            tutorNumber = tutorNumberPicker[blattnummer][number]
            files = filesToDownload[tutorNumber]
            file.write(f"Korrekturen für Tutor {buchstabe} - [TutorBuchstabe: {tutorNumber} - Anzahl: {len(files)}]\n")
            for abgabe in files:
                team_name = extract_team_name(abgabe.name)
                file.write(team_name + '\n')
            file.write('\n')
        file.write(f"Es gibt insgesamt {len(allAbgaben)} Teams. Hier sind die Datei- und Teamnamen:\n")
        count = 1
        
        
        for abgabe in allAbgaben:
            file.write(f"{count}: {abgabe.name} - {extract_team_name(abgabe.name)}\n")
            count = count +1
    print(f"Die Verteilungs-Datei wurde erfolgreich erstellt.")          
else:
    print(f"Fehler bei der Anfrage: {response.status_code}")
    print(response.text)

input("Drücke Enter zum Schließen")