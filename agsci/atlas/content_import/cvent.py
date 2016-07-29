from . import BaseContentImporter

class CventContentImporter(BaseContentImporter):

    def __init__(self, json_data):
        self.json_data = json_data
        
    def get_data(self):
        return self.json_data
