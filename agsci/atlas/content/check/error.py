class Error(object):
    
    level = 'Medium'
    
    def __init__(self, check='', msg=''):
        self.check = check
        self.msg = msg
    
    def klass(self):
        return 'error-check-%s' % self.level.lower()
    
    def __repr__(self):
        return self.msg

class LowError(Error):
    
    level = "Low"    

class MediumError(Error):
    pass

class HighError(Error):

    level = "High"