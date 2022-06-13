import time
import robonomicsinterface as RI
import json
import yaml
import random
import logging
import argparse
import threading

from substrateinterface import Keypair
from pvstation import PVStation

logger = logging.getLogger(__name__)
logger.propagate = False
handler = logging.StreamHandler()
logger.addHandler(handler)
logger.setLevel(logging.INFO)


class PlugMonitoring:
    def __init__(self, config_file_path) -> None:
        self.prev_time_sending = time.time()
        self.config = self.load_config(config_file_path)
        self.plug_seed = self.config["plug_seed"]
        self.service_address = self.config["service_address"]
        self.interface = RI.RobonomicsInterface(
            seed=self.plug_seed, remote_ws="ws://127.0.0.1:9944")
        self.ss58_address = self.interface.define_address()
        self.check_balance()
        self.send_launch()

    def load_account_balance(self, ss58_address):
        return self.interface.custom_chainstate(
            "System", "Account", ss58_address)

    def check_balance(self) -> None:
        info = self.load_account_balance(self.ss58_address)
        if info.value['data']['free'] > 0:
            logger.info(f"Balance is OK")
            balance = True
        else:
            logger.info(f"Waiting for tokens on account balance")
            balance = False
        while not balance:
            info = self.load_account_balance(self.ss58_address)
            if info.value['data']['free'] > 0:
                balance = True
                logger.info(f"Balance OK")

    def send_launch(self) -> None:
        logger.info(f"Check topic exists")

        twins_num = self.interface.custom_chainstate("DigitalTwin", "Total")
        if twins_num.value is None:
            logger.error(
                "Please create digital twin from service_address account to proceed with station plug communication!")
            return

        twin_id = None
        for i in range(twins_num.value):
            owner = self.interface.custom_chainstate(
                "DigitalTwin", "Owner", int(i))
            logger.info(f"Twin owner: {owner}")
            if owner.value == self.service_address:
                twin_id = i
                break

        if twin_id is None:
            logger.error(
                f"Twin id where owner is {self.service_address} was not found. Please create digital twin to proceed!")
            return

        logger.info(f"Twin id : {twin_id}")
        topics = self.interface.custom_chainstate(
            "DigitalTwin", "DigitalTwin", twin_id)
        plug_address = Keypair.create_from_mnemonic(
            self.plug_seed).ss58_address
        if topics.value is None:
            topics_list = []
        else:
            topics_list = topics.value
        for topic in topics_list:
            if topic[1] == plug_address:
                logger.info(f"Topic exists")
                break
        else:
            logger.info(f"Sending launch to add topic")
            hash = self.interface.send_launch(
                self.service_address, "0x0000000000000000000000000000000000000000000000000000000000000002")
            logger.info(f"Launch created with hash {hash}")

    def send_datalog(self, data: dict) -> None:
        hash = self.interface.record_datalog(str(data))
        logger.info(f"Datalog : {data}\n"
                    f"Created with hash {hash}")

    def solar_panel_data_simulator(self, message: str) -> None:
        pv_station = PVStation(**json.loads(message))
        # logger.info(f"Received PV power station data : {pv_station}")
        # Idea is that we are sending data each hour, as we measure of generated PV power in MW per hour
        if (time.time() - self.prev_time_sending) > self.config['sending_timeout']:
            self.prev_time_sending = time.time()
            threading.Thread(target=self.send_datalog,
                             name="DatalogSender", args=[pv_station]).start()

    def load_config(self, path: str):
        with open(path) as f:
            config_file = yaml.safe_load(f)
        if "plug_seed" not in config_file:
            mnemonic = Keypair.generate_mnemonic()
            logger.info(
                f"Generated account with address: {Keypair.create_from_mnemonic(mnemonic).ss58_address}")
            config_file["plug_seed"] = mnemonic
            with open(path, "w") as f:
                yaml.dump(config_file, f)
        else:
            logger.info(
                f"Your station plug address is {Keypair.create_from_mnemonic(config_file['plug_seed']).ss58_address}")

        return config_file


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Parse argument for PV power station plug module.')
    parser.add_argument('--yaml-station-data', dest='yaml_station_data',
                        help='Path to YAML configuration file with test data for PV power station configuration',
                        required=True)
    parser.add_argument('--station-config', dest='station_config',
                        help='Path to YAML file with parachain configuration for PV power station',
                        required=True)
    args = parser.parse_args()

    monitor = PlugMonitoring(args.station_config)

    while True:
        station = PVStation.from_yaml(args.yaml_station_data)
        station.power_generated_MWh = random.uniform(0, 1)
        station.power_generation_timestamp = time.time()

        monitor.solar_panel_data_simulator(station.to_json())
        time.sleep(60)
