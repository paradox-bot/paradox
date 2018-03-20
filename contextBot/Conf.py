class Conf:
    def __init__(self, name):
        self.name = name
        self.settings = {}

    def setting(self, cls):
        settings[cls.name] = cls
        setattr(self, cls.name, cls)
