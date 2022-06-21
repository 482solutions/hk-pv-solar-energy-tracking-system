import os
import time
import json
import yaml


class PVStation:
    def __init__(self, company_registry_number="", power_station_id="", power_generation_timestamp=0, power_reserved=0, power_generated_for_sale=0) -> None:
        self.company_registry_number = company_registry_number
        self.power_station_id = power_station_id
        self.power_generation_timestamp = power_generation_timestamp
        self.power_reserved = power_reserved
        self.power_generated_for_sale = power_generated_for_sale

    def __iter__(self):
        yield from {
            "company_registry_number": self.company_registry_number,
            "power_station_id": self.power_station_id,
            "power_generation_timestamp": self.power_generation_timestamp,
            "power_reserved": self.power_reserved,
            "power_generated_for_sale": self.power_generated_for_sale
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
                         json_dct["power_generation_timestamp"],
                         json_dct["power_reserved"],
                         json_dct["power_generated_for_sale"])

    @staticmethod
    def from_yaml(file_path):
        with open(file_path) as f:
            yaml_config = yaml.safe_load(f)

        return PVStation(yaml_config["company_registry_number"],
                         yaml_config["power_station_id"],
                         0 if "power_generation_timestamp" not in yaml_config else yaml_config[
                             "power_generation_timestamp"],
                         0 if "power_reserved" not in yaml_config else yaml_config["power_reserved"],
                         0 if "power_generated_for_sale" not in yaml_config else yaml_config["power_generated_for_sale"])

    def load_produced_power_data(self) -> float:
        station_data_file_path = f"./data/{self.company_registry_number}/{self.power_station_id}"
        if os.path.exists(station_data_file_path):
            with open(station_data_file_path) as f:
                produced_total = float(f.readline().split(": ")[1])  # in MW
        else:
            produced_total = 0

        self.power_reserved = produced_total

        return self.power_reserved

    def update_produced_power_data(self, new_produced_power=0):
        data_folder_path = f"./data/{self.company_registry_number}"
        if not os.path.isdir(data_folder_path):
            os.makedirs(data_folder_path, exist_ok=True)
        else:
            if self.power_reserved == 0:
                self.load_produced_power_data()

        self.power_reserved += new_produced_power

        with open(f"{data_folder_path}/{self.power_station_id}", "w") as f:
            f.write(f"{time.time()}: {self.power_reserved}")
