import yaml


class ConfigHelper(object):
    """Helper class to load configuration from a YAML file"""

    def __init__(self, config_file_path):
        """Load input config file"""
        
        self.file = config_file_path
        with open(self.file, 'r') as stream:
            self.config = yaml.load(stream)

    def get_configuration(self):
        """Returns a dictionary w/ data loaded from YAML file"""

        value = self.config
        if value == None:
            raise KeyError("Missing data in file {}\n".format(self.file))
        else:
            return value
