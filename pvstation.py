import json
import yaml

class PVStation:
    def __init__(self, company_registry_number="", power_station_id="", power_generated_MWh=0, power_generation_timestamp=0) -> None:
        self.company_registry_number = company_registry_number
        self.power_station_id = power_station_id
        self.power_generated_MWh = power_generated_MWh
        self.power_generation_timestamp = power_generation_timestamp

    def __iter__(self):
        yield from {
            "company_registry_number": self.company_registry_number,
            "power_station_id": self.power_station_id,
            "power_generated_MWh": self.power_generated_MWh,
            "power_generation_timestamp": self.power_generation_timestamp
        }.items()

    def __str__(self):
        return json.dumps(dict(self), ensure_ascii=False)

    def __repr__(self):
        return self.__str__()

    def to_json(self):
        return self.__str__()
    
    def get_station_unique_id(self) -> str:
        return f"{self.company_registry_number}_{self.power_station_id}"

    @staticmethod
    def from_json(json_dct):
        return PVStation(json_dct["company_registry_number"],
                         json_dct["power_station_id"],
                         json_dct["power_generated_MWh"],
                         json_dct["power_generation_timestamp"])

    @staticmethod
    def from_yaml(file_path):
        with open(file_path) as f:
            yaml_config = yaml.safe_load(f)

        return PVStation(yaml_config["company_registry_number"],
                         yaml_config["power_station_id"],
                         0 if "power_generated_MWh" not in yaml_config else yaml_config[
                             "power_generated_MWh"],
                         0 if "power_generation_timestamp" not in yaml_config else yaml_config["power_generation_timestamp"])
