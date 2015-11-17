from agsci.common.api import BaseContainerView

class SlideshowView(BaseContainerView):

    def getData(self, recursive=True):
        # Get data from parent BaseContainerView, and add text
        data = super(SlideshowView, self).getData(recursive=True)
        data['text'] = self.context.text.raw
        return data



