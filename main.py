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
    "00" : "4e41298c8fa595b706c66c377ca1a6df",
    "01" : "4e41298c8fa595b706c66c377ca1a6df",
    "02" : "993ada6d5700be0607ddd1c4d052998c",
    "03" : "f73e6fb5737e0c12aefce4c3bca1a89b",
    "04" : "58d685997019802d2d161d3e4d830e06",
    "05" : "",
    "06" : "",
    "07" : "",
    "08" : "",
    "09" : "",
    "10" : "",
    "11" : "",
    "12" : "",
    "13" : "",
    "14" : "",
    "15" : "",
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
        if(number < 0 or number > 15):
            raise ValueError
        numberInputIncomplete = False
        if number < 10:
            blattnummer = "0"+str(number)
        else:
            blattnummer = str(number)    
    except ValueError:
        print("Ungültige Eingabe. Bitte geben eine Zahl zwichen 0 und 15 ein.")

while tutorInputIncomplete:
    try:
        number = int(input("Welcher Tutor bist du? "))
        if(number < 0 or number > 8):
            raise ValueError
        tutorInputIncomplete = False
        tutorNumber = number
    except ValueError:
        print("Ungültige Eingabe. Bitte geben eine Zahl zwichen 0 und 8 ein.")

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
        tutorNumber = number
    except ValueError:
        print("Ungültige Eingabe. Wähle y = ja oder n = nein.")

# Restliche Config
pattern = f"^UE{blattnummer}_\w+(\[\d+\])?\.zip$" #^UE\d{2}_\w+(\[\d+\])?\.zip$
patternTeam = f'UE{blattnummer}_(.*?)\.zip'
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



response = requests.get(f'{api_url}/folder/{folder[blattnummer]}/files?limit=500', auth=HTTPBasicAuth(username, password))

if response.status_code == 200:
    data = response.json()
    #print(data)

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
    for file in files:
        for cfile in files:
            if file.equals(cfile):
                if file.date > cfile.date:
                    files.remove(cfile)
                else:
                    files.remove(file)
    print(" - Fertig!")

    files = sorted(files, key=lambda abgabe: abgabe.name, reverse=True)    
    print(f"Dateien sind sortiert! Es gibt {len(files)} valide Abgaben. Schätzung: {len(files)}/{numberOfTutors} = {len(files)/numberOfTutors}.") 
    
    if genFalscheAbgaben:
        for file in illegalFiles:
            if file.userID not in illegalUserIDs:
                illegalUserIDs.append(file.userID)

        emails = ""
        count = 0
        filePath = os.path.join(targetDir,'falscheAbgaben.txt')
        with open(filePath, "w") as file:
            pbar = tqdm(illegalUserIDs, unit="User")
            pbar.set_description("Erstelle Liste von Usern mit falscher Abgabe.")
            for user in pbar:
                response = requests.get(api_url+'/user/'+user, auth=HTTPBasicAuth(username, password)).json()
                emails = emails + response['email']+";"
                count = count + 1
            file.write(emails)
        print(f"Die Falschen-Abgaben-Datei wurde erfolgreich gespeichert. Es haben insgesamt {count} Personen eine falsche Datei hochgeladen.")



    filesToDownload = split_list(files)
    teams = ""
    emailList = {}
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
    
    filePath = os.path.join(targetDir,f'score{tutorBuchstabe}_{blattnummer}.csv')
    with open(filePath, "w") as file:
        file.write(teams)
    print(f"Die score.csv-Datei wurde erfolgreich erstellt.")

else:
    print(f"Fehler bei der Anfrage: {response.status_code}")
    print(response.text)

input("Drücke Enter zum Schließen")