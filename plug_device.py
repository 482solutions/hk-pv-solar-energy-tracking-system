from socket import timeout
import sys
import time
import robonomicsinterface as RI
import json
import yaml
import random
import logging
import argparse
import threading
import hashlib
import solar_panel_connector.mqtt_client as mqttc

from queue import Queue
from substrateinterface import Keypair
from pv_station import PVStation
from threading import Thread

logger = logging.getLogger(__name__)
logger.propagate = False
handler = logging.StreamHandler()
logger.addHandler(handler)
logger.setLevel(logging.INFO)

class custom_thread(Thread):
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs={}, Verbose=None):
        Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None
    def run(self):
        print(type(self._target))
        if self._target is not None:
            self._return = self._target(*self._args,
                                                **self._kwargs)
    def join(self, *args):
        Thread.join(self, *args)
        return self._return

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
        if info.value["data"]["free"] > 0:
            logger.info(f"Balance is OK")
            balance = True
        else:
            logger.info(f"Waiting for tokens on account balance")
            balance = False
        while not balance:
            info = self.load_account_balance(self.ss58_address)
            if info.value["data"]["free"] > 0:
                balance = True
                logger.info(f"Balance OK")

    def send_launch(self) -> None:
        logger.info(f"Check if topic for plug device exists")

        twins_num = self.interface.custom_chainstate("DigitalTwin", "Total")
        if twins_num.value is None:
            logger.error(
                "Please create digital twin from service_address account to proceed with station plug communication and restart service!")
            exit(1)

        twin_id = None

        for i in range(twins_num.value):
            owner = self.interface.custom_chainstate(
                "DigitalTwin", "Owner", int(i))
            logger.info(f"Twin owner: {owner}")
            if owner.value == self.service_address:
                twin_id = i
                logger.info(f"Owner twin found (id {twin_id})")
                break

        if twin_id is None:
            logger.error(
                f"Twin id where owner is {self.service_address} was not found. Please create digital twin to proceed!")
            sys.exit(1)

        topics = self.interface.custom_chainstate(
            "DigitalTwin", "DigitalTwin", twin_id)
        plug_address = Keypair.create_from_mnemonic(
            self.plug_seed, ss58_format=32).ss58_address
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
                self.service_address, hex(int.from_bytes(hashlib.sha256(b"H").digest()[:32], "little")))
            logger.info(f"Launch created with hash {hash}")

    def send_datalog(self, data: dict) -> None:
        hash = self.interface.record_datalog(str(data))
        logger.info(f"Datalog : {data}\n"
                    f"Created with hash {hash}")

    def solar_panel_data_simulator(self, message: str) -> None:
        pv_station = PVStation(**json.loads(message))
        # logger.info(f"Received PV power station data : {pv_station}")
        if (time.time() - self.prev_time_sending) > self.config["sending_timeout"] and \
                pv_station.power_reserved > 1:
            pv_station.power_generated_for_sale = int(
                pv_station.power_reserved)
            pv_station.power_reserved -= pv_station.power_generated_for_sale
            pv_station.update_produced_power_data()
            self.prev_time_sending = time.time()
            threading.Thread(target=self.send_datalog,
                             name="DatalogSender", args=[pv_station]).start()

    def load_config(self, path: str):
        with open(path) as f:
            config_file = yaml.safe_load(f)
        if "plug_seed" not in config_file:
            mnemonic = Keypair.generate_mnemonic()
            logger.info(
                f"Generated account with address: {Keypair.create_from_mnemonic(mnemonic, ss58_format=32).ss58_address}")
            config_file["plug_seed"] = mnemonic
            with open(path, "w") as f:
                yaml.dump(config_file, f)
        else:
            logger.info(
                f"Your station plug address is {Keypair.create_from_mnemonic(config_file['plug_seed'], ss58_format=32).ss58_address}")

        return config_file

    def solar_panel_emulator(self, station, queue):
        while True:
            station.power_generation_timestamp = time.time()
            station.update_produced_power_data(random.uniform(0, 1))
            queue.put(station.to_json)
            time.sleep(0.5)

    def send_datalog_from_queue(self, queue) -> None:
        logger.info(f"Queue size: {queue.qsize()}")
        logger.info(f"Value: {queue.get()}")
        hash = self.interface.record_datalog(str(queue.get()))
        logger.info(f"Datalog : {queue.get()}\n"
                    f"Created with hash {hash}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Parse argument for PV power station plug module.")
    parser.add_argument("--yaml-station-data", dest="yaml_station_data",
                        help="Path to YAML configuration file with test data for PV power station configuration",
                        required=True)
    parser.add_argument("--station-config", dest="station_config",
                        help="Path to YAML file with parachain configuration for PV power station",
                        required=True)
    args = parser.parse_args()

    monitor = PlugMonitoring(args.station_config)

    queue = Queue()    
    station_1 = PVStation.from_yaml(args.yaml_station_data)
    station_2 = PVStation.from_yaml(args.yaml_station_data)
    
    t1 = custom_thread(target=mqttc.run)

    t2 = custom_thread(target=monitor.solar_panel_emulator,
                                name="Solar_Panel_Emulator", args=[station_2, queue])

    t3 = custom_thread(target=monitor.solar_panel_emulator,
                                name="Solar_Panel_Emulator", args=[station_2, queue])

    t4 = threading.Thread(target=monitor.send_datalog,
                                name="DatalogSender", args=[queue])

    t4_status = False
    
    logger.info(f"starting t1")
    t1.start()

    logger.info(f"starting t2")
    t2.start()

    logger.info(f"starting t3")
    t3.start()

    logger.info(f"starting t4")
    t4.start()
                                    
    while True:
        if t1.is_alive() == False:
            logger.info(f"ending t1")
            t1_json = t1.join()
            t1 = custom_thread(target=mqttc.run)
            logger.info(f"{t1_json}")
            station_1.power_generation_timestamp = t1_json['Timestamp']
            station_1.update_produced_power_data(float(t1_json['Power']))
            queue.put(station_1.to_json)
            logger.info(f"starting t1")
            t1.start()
            # threading.Thread(target=monitor.send_datalog,
            #                  name="DatalogSender", args=[station.to_json]).start()
            # monitor.solar_panel_data_simulator(station.to_json())

        # simulate 2nd solar panel with emulator
        # if not t2.is_alive():
        #     emulator_json = t2.join()
        #     logger.info(f"emulator json {emulator_json}")
        #     logger.info(f"t2 status {t2.is_alive()}")
        #     queue.put(emulator_json)
        #     t2 = custom_thread(target=monitor.solar_panel_emulator,
        #                         name="Solar_Panel_Emulator", args=[station_2])
        #     t2.start()

        # # simulate 3rd solar panel with emulator
        # if not t3.is_alive():
        #     emulator_json = t3.join()
        #     logger.info(f"emulator json {emulator_json}")
        #     logger.info(f"t3 status {t3.is_alive()}")
        #     queue.put(emulator_json)
        #     t3 = custom_thread(target=monitor.solar_panel_emulator,
        #                         name="Solar_Panel_Emulator", args=[station_2])
        #     t3.start()
        
        # if queue.empty() == False and t4_status == False:
        #     # monitor.send_datalog(queue.get())
        #     logger.info(f"queue size {queue.qsize()}")
        #     t4 = threading.Thread(target=monitor.send_datalog,
        #                         name="DatalogSender", args=[queue])
        #     logger.info(f"queue size {queue.qsize()}")
        #     logger.info(f"starting t4")
        #     t4.start()
        #     t4_status = t4.is_alive()

        # if t4_status == True:
        #     logger.info(f"ending t4")
        #     t4.join()
        #     t4_status = t4.is_alive()
        
        # station.power_generation_timestamp = time.time()
        # station.update_produced_power_data(random.uniform(0, 1))
        # monitor.solar_panel_data_simulator(station.to_json())
        # Update generated value each 360 seconds
        # time.sleep(15)

# there was timeout for 6 mins (create new datalog each 6 mins)