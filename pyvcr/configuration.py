import yaml


def load_configuration(configuration_path):
    """Load configuration.

    :param configuration_path: `string` configuration path.
    """
    with open(configuration_path) as configuration:
        return yaml.load(configuration.read(), yaml.FullLoader)
