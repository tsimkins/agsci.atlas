from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from agsci.atlas.content.behaviors import IAtlasFilterSets
from . import StaticVocabulary

class FilterSetVocabulary(StaticVocabulary):

    def __call__(self, context):

        terms = []

        for (field_name, field_schema) in sorted(IAtlasFilterSets.namesAndDescriptions()):
            terms.append(SimpleTerm(field_name, title=field_schema.title))

        return SimpleVocabulary(terms)

class HomeOrCommercialVocabulary(StaticVocabulary):

    items = ['Home', 'Commercial', 'Classroom']

class AgronomicCropVocabulary(StaticVocabulary):

    items = ['Alternative', 'Corn', 'Soybeans', 'Small Grains', 'Grain Sorghum', 'Hemp']

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
             'Cherries', 'Currants', 'Gooseberries', 'Grapes',
             'Nectarines', 'Peaches', 'Pears', 'Plums', 'Raspberries',
             'Strawberries']

class IndustryVocabulary(StaticVocabulary):

    items = [
        'Child Care',
        'Farming',
        'Food Processing',
        'Food Service',
        'Greenhouse/Nursery',
        'Health and Wellness',
        'Landscaping/Arborist',
        'Retail Food/Grocery',
        'Turfgrass',
        'Vineyards and Wineries'
    ]

class PlantTypeVocabulary(StaticVocabulary):

    items = ['Evergreen', 'Deciduous', 'Annuals', 'Perennials', 'Houseplants']

class TurfgrassLawnVocabulary(StaticVocabulary):

    items = ['Lawn', 'Golf Course', 'Athletic Field']

class VegetableVocabulary(StaticVocabulary):

    items = ['Asparagus', 'Beets', 'Broccoli', 'Cabbage', 'Carrots',
             'Cauliflower', 'Collards', 'Cucumbers', 'Eggplant', 'Garlic',
             'Lima Beans', 'Lettuce', 'Melons', 'Okra', 'Onions', 'Peas',
             'Peppers', 'Potatoes', 'Pumpkins', 'Radishes', 'Rhubarb',
             'Snap Beans', 'Squash', 'Spinach', 'Sweet Corn', 'Tomatoes',
             'Turnips']

class WaterSourceVocabulary(StaticVocabulary):

    items = ['Well', 'Cistern', 'Reservoir']

class InsectPestsVocabulary(StaticVocabulary):

    items = [
        'Allium Leaf Miner',
        'Aphids',
        'Armyworm',
        'Billbugs',
        'Brown Marmorated Stink Bug',
        'Cereal Leaf Beetle',
        'Chinch Bugs',
        'Corn Rootworm',
        'Gypsy Moth',
        'Japanese Beetle',
        'Potato Leafhopper',
        'Sod Webworms',
        'Spotted Lanternfly',
        'Thrips',
        'Ticks',
        'White Grubs'
    ]

class PlantDiseasesVocabulary(StaticVocabulary):

    items = ['Anthracnose', 'Apple Scab', 'Bacterial Spot', 'Botrytis',
             'Downy Mildew', 'Fire Blight', 'Gray Mold', 'Late Blight',
             'Leaf Spots', 'Powdery Mildew', 'Pythium', 'Root Rots', 'Rust']

class WeedsVocabulary(StaticVocabulary):

    items = ['Burcucumber', 'Canada Thistle', 'Chickweed', 'Common Burdock',
             'Common Pokeweed', 'Crabgrass', 'Marestail Horseweed',
             'Multiflora Rose', 'Nimblewill', 'Palmer Amaranth',
             'Pigweed', 'Quackgrass', 'Yellow Nutsedge']

class FoodTypeVocabulary(StaticVocabulary):

    items = [
        'Bakery', 'Beans', 'Beverages', 'Dairy', 'Grains', 'Meats', 'Nuts',
        'Poultry', 'Produce', 'Seafood'
    ]

class CowgAgeLactationStageVocabulary(StaticVocabulary):

    items = [
        'Calves', 'Heifers', 'Dry Cows', 'Lactating Cows'
    ]

class PoultryFlockSizeVocabulary(StaticVocabulary):

    items = [
        'Commercial', 'Small Flock'
    ]

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
InsectPestsVocabularyFactory = InsectPestsVocabulary()
PlantDiseasesVocabularyFactory = PlantDiseasesVocabulary()
WeedsVocabularyFactory = WeedsVocabulary()
FoodTypeVocabularyFactory = FoodTypeVocabulary()
CowgAgeLactationStageVocabularyFactory = CowgAgeLactationStageVocabulary()
PoultryFlockSizeVocabularyFactory = PoultryFlockSizeVocabulary()