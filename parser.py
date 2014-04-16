import sys
import codecs
import os
import dataset

class Parser(object):
    SKIP = "skip"

    def __init__(self):
        self.state = self.s_initial
        self.data = {}

    def s_initial(self, row):
        if row.startswith("Facility:"):
            self.state = self.s_facility
            return Parser.SKIP

    def s_facility(self, row):
        if row.startswith("Facility:"):
            self.data["facility"] = row.split(":")[1].strip()
            self.state = self.s_overview 

    def s_overview(self, row):
        if row.startswith("1. Facility Overview"):
            self.state = self.s_overview_text

    def s_overview_text(self, row):
        if "Surrounding Area" in row:
            self.state = self.s_surrounding
            return Parser.SKIP 

        if not "overview" in self.data:
            self.data["overview"] = ""
        self.data["overview"] += " " + row
        self.data["overview"] = " ".join(self.data["overview"].strip().split())

    def s_surrounding(self, row):
        if row.startswith("Surrounding Area"):
            self.data["surrounding"] = row.split(":")[1].strip()
            self.state = self.s_gps 

    def s_gps(self, row):
        if row.startswith("GPS -"):
            parts = row.split(",")
            if not ("Latitude" in parts[0] and "Longitude" in parts[1]):
                raise Exception("Unexpected Row")

            self.data["lat"] = float(parts[0].split(":")[1].strip())
            self.data["lng"] = float(parts[1].split(":")[1].strip())

            self.state = self.s_street

    def s_street(self, row):
        if "Street Address" in row: 
            self.data["street_address"] = row.replace("Street Address", "").strip()
            self.state = self.s_postal

    def s_postal(self, row):
        if "Postal Address" in row: 
            self.data["postal_address"] = row.replace("Postal Address", "").strip()
            self.state = self.s_postal_area

    def s_postal_area(self, row):
        if "Postal Area" in row: 
            self.data["postal_area"] = row.replace("Postal Area", "").strip()
            self.state = self.s_telephone

    def s_telephone(self, row):
        if "Telephone number" in row: 
            self.data["telephone"] = row.replace("Telephone number", "").strip()
            self.state = self.s_cell
        
    def s_cell(self, row):
        if "Cell number" in row: 
            self.data["cell"] = row.replace("Cell number", "").strip()
            self.state = self.s_fax

    def s_fax(self, row):
        if "Fax number" in row: 
            self.data["fax"] = row.replace("Fax number", "").strip()
            self.state = self.s_email

    def s_email(self, row):
        if "Email address" in row: 
            self.data["email"] = row.replace("Email address", "").strip()
            self.state = self.s_manager

    def s_manager(self, row):
        if "Manager Name" in row: 
            self.data["manager"] = row.replace("Manager Name", "").strip()
        
    def parse(self, fp):
        for row in fp:
            while True:
                emit = self.state(row)
                if emit != Parser.SKIP: break
    

def from_pdf(fname):
    cmd = 'pdftotext -layout "%s" tmp.txt' % fname
    os.system(cmd)
    return codecs.open("tmp.txt", "r", "utf8")
    
db = dataset.connect('sqlite:///clinics.db')
clinics = db["clinics"]
for dir, _, files in os.walk("/home/adi/Data/CityPress - Hospitals/facility_profile"):
    for file in files:
        parser = Parser()
        fname = os.path.join(dir, file)
        parser.parse(from_pdf(fname))
        if parser.data:
            clinics.upsert(parser.data, ["facility"])
