from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from agsci.atlas.content.behaviors import IAtlasFilterSets
from . import StaticVocabulary

class FilterSetVocabulary(StaticVocabulary):

    def __call__(self, context):

        terms = []

        for (field_name, field_schema) in sorted(IAtlasFilterSets.namesAndDescriptions()):
            terms.append(SimpleTerm(field_name,title=field_schema.title))

        return SimpleVocabulary(terms)

class HomeOrCommercialVocabulary(StaticVocabulary):

    items = ['Home', 'Commercial', 'Classroom']

class AgronomicCropVocabulary(StaticVocabulary):

    items = ['Alternative', 'Corn', 'Soybeans', 'Small Grains', 'Grain Sorghum']

class BusinessTopicVocabulary(StaticVocabulary):

    items = ['Getting Started', 'Financial Management', 'Marketing',
             'Land and Equipment', 'Insurance', 'Human Resource Management']

class CoverCropVocabulary(StaticVocabulary):

    items = ['Grasses', 'Legumes', 'Broadleaves']

class DisasterVocabulary(StaticVocabulary):

    items = ['Biosecurity', 'Floods', 'Droughts', 'Hurricanes', 'Blizzards',
             'Earthquakes', 'Wildfires']

class EnergySourceVocabulary(StaticVocabulary):

    items = ['Biomass', 'Solar', 'Wind', 'Wood', 'Waste']

class FarmEquipmentStructureVocabulary(StaticVocabulary):

    items = ['Barns', 'Greenhouses', 'High Tunnels', 'Manure Pits',
             'Silos/Grain Bins', 'Tractors/Machinery', 'ATV/Other Vehicles']

class ForageCropVocabulary(StaticVocabulary):

    items = ['Alfalfa', 'Corn', 'Birdsfoot Trefoil', 'Clovers',
             'Cool-Season Grasses', 'Warm-Season Grasses']

class FruitVocabulary(StaticVocabulary):

    items = ['Apricots', 'Apples', 'Blackberries', 'Blueberries', 'Brambles',
             'Cherries', 'Currants', 'Gooseberries', 'Grapes', 'Melons',
             'Nectarines', 'Peaches', 'Pears', 'Plums', 'Raspberries',
             'Strawberries']

class IndustryVocabulary(StaticVocabulary):

    items = ['Farming', 'Greenhouse/Nursery', 'Landscaping/Arborist',
             'Food Processing', 'Food Service', 'Retail Food/Grocery',
             'Turfgrass', 'Vineyards and Wineries']

class PlantTypeVocabulary(StaticVocabulary):

    items = ['Evergreen', 'Deciduous', 'Annuals', 'Perennials', 'Houseplants']

class TurfgrassLawnVocabulary(StaticVocabulary):

    items = ['Lawn', 'Golf Course', 'Athletic Field']

class VegetableVocabulary(StaticVocabulary):

    items = ['Asparagus', 'Beets', 'Broccoli', 'Cabbage', 'Carrots',
             'Cauliflower', 'Collards', 'Cucumbers', 'Eggplant', 'Garlic',
             'Lima Beans', 'Lettuce', 'Okra', 'Onions', 'Peas', 'Peppers',
             'Potatoes', 'Pumpkins', 'Radishes', 'Rhubarb', 'Snap Beans',
             'Squash', 'Spinach', 'Sweet Corn', 'Tomatoes', 'Turnips']

class WaterSourceVocabulary(StaticVocabulary):

    items = ['Well', 'Cistern', 'Reservoir']

FilterSetVocabularyFactory = FilterSetVocabulary()

HomeOrCommercialVocabularyFactory = HomeOrCommercialVocabulary()
AgronomicCropVocabularyFactory = AgronomicCropVocabulary()
BusinessTopicVocabularyFactory = BusinessTopicVocabulary()
CoverCropVocabularyFactory = CoverCropVocabulary()
DisasterVocabularyFactory = DisasterVocabulary()
EnergySourceVocabularyFactory = EnergySourceVocabulary()
FarmEquipmentStructureVocabularyFactory = FarmEquipmentStructureVocabulary()
ForageCropVocabularyFactory = ForageCropVocabulary()
FruitVocabularyFactory = FruitVocabulary()
IndustryVocabularyFactory = IndustryVocabulary()
PlantTypeVocabularyFactory = PlantTypeVocabulary()
TurfgrassLawnVocabularyFactory = TurfgrassLawnVocabulary()
VegetableVocabularyFactory = VegetableVocabulary()
WaterSourceVocabularyFactory = WaterSourceVocabulary()
