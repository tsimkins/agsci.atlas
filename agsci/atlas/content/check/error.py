class Error(object):
    
    level = 'Medium'
    
    def __init__(self, check='', msg=''):
        self.check = check
        self.msg = msg
    
    def klass(self):
        return 'error-check-%s' % self.level.lower()
    
    def __repr__(self):
        return self.msg
    
    def render(self):

        if self.check and hasattr(self.check, 'render'):
            return self.check.render
        
        return False

    @property
    def error_code(self):
        return self.check.error_code

class LowError(Error):
    
    level = "Low"    

class MediumError(Error):
    pass

class HighError(Error):

    level = "High"