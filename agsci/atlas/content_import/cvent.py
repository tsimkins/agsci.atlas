from . import BaseContentImporter
from plone.memoize.instance import memoize
import json

class CventContentImporter(BaseContentImporter):

    def __init__(self, json_str):
        self.json_data = json.loads(json_str)
        
    def get_data(self):
        return self.json_data