import json
class db_utils:
    @staticmethod
    def json_Reader(path: str, mode: str) -> any:
        with open(path, mode) as file:
            config_data = json.load(file)
        db_config = config_data.get('db_config')
        db_config
        db_config = config_data.get('db_config', {})

        return db_config