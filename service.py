#!/usr/bin/env python3
import typing as tp
import robonomicsinterface as RI
import yaml
import hashlib
import logging
import sys
import threading
from substrateinterface import SubstrateInterface, Keypair
from substrateinterface.exceptions import SubstrateRequestException
import time
import os
import ast

from pvstation import PVStation

logger = logging.getLogger(__name__)
logger.propagate = False
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

TWIN_ID = 0


class FootprintService:
    def __init__(self) -> None:
        with open("./config/config_service.yaml") as f:
            self.config = yaml.safe_load(f)
        self.interface = RI.RobonomicsInterface(
            self.config["robonomics"]["seed"], remote_ws="ws://127.0.0.1:9944")
        self.statemine_keypair = Keypair.create_from_mnemonic(
            self.config["statemine"]["seed"]
        )
        threading.Thread(target=self.launch_listener,
                         name="LaunchListener").start()

    def on_launch(self, data: tp.Tuple[str, str, bool]) -> None:
        logger.info("Add account to existing Digital Twin")
        plug_address = data[0]
        logger.info(f"Plug station address {plug_address}")
        twins_list = self.get_twins_list()
        if twins_list is None:
            twins_list = []
        topic_num = len(twins_list)
        logger.info(f"Number of existing topics: {topic_num}")
        for topic in twins_list:
            if topic[1] == plug_address:
                logger.info(
                    f"Topic with address {plug_address} already exists")
                break
        else:
            name = hashlib.sha256(bytes(topic_num)).hexdigest()
            params = {"id": TWIN_ID, "topic": f"0x{name}",
                      "source": plug_address}
            hash = self.interface.custom_extrinsic(
                "DigitalTwin", "set_source", params)
            logger.info(f"Created topic with extrinsic hash: {hash}")

    def launch_listener(self) -> None:
        RI.Subscriber(
            self.interface, RI.SubEvent.NewLaunch, self.on_launch, self.interface.define_address()
        )

    def get_twins_list(self) -> tp.List[tp.Tuple[str, str]]:
        twin = self.interface.custom_chainstate(
            "DigitalTwin", "DigitalTwin", TWIN_ID)

        if twin is None:
            return None

        twins_list = twin.value
        return twins_list

    def statemine_connect(self) -> SubstrateInterface:
        # For now I am using Westmint (it is a test network)
        interface = SubstrateInterface(
            url=self.config["statemine"]["endpoint"],
        )
        return interface

    def transfer_call(self, substrate: SubstrateInterface, power_MWh: int, power_producer_address: str) -> tp.Any:
        # call = substrate.compose_call(
        #     call_module="Assets",
        #     call_function="transfer",
        #     call_params={
        #         "id": self.config["statemine"]["token_id"],
        #         # station account who generated power
        #         "target": {"Id": power_producer_address},
        #         "amount": str(power_MWh),
        #     },
        # )

        call = substrate.compose_call(
            call_module="Assets",
            call_function="burn",
            call_params={
                "id": self.config["statemine"]["token_id"],
                "who": {"Id": self.statemine_keypair.ss58_address}, # power_producer_address
                "amount": str(power_MWh),
            },
        )

        return call

    def transfer_tokens_for_generated_power(self, power: int, power_producer_address: str) -> None:
        substrate = self.statemine_connect()
        extrinsic = substrate.create_signed_extrinsic(
            call=self.transfer_call(substrate, power, power_producer_address), keypair=self.statemine_keypair
        )
        try:
            receipt = substrate.submit_extrinsic(
                extrinsic, wait_for_inclusion=True)
            logger.info(
                f"Tokens for {power} MW paid, transaction block : {receipt.block_hash}"
            )
            return True
        except SubstrateRequestException as e:
            logger.warning(
                f"Something went wrong during extrinsic submission to Statemine: {e}"
            )
            return False

    def get_not_paid_produced_power(self, station_id: str) -> float:
        station_data_file_path = f"./data/{station_id}"
        if os.path.exists(station_data_file_path):
            with open(station_data_file_path) as f:
                produced_total = float(f.readline().split(": ")[1])  # in MW
        else:
            produced_total = 0

        return produced_total

    def save_not_paid_produced_power(self, station_id: str, produced_power: float):
        data_folder_path = "./data"
        if not os.path.isdir(data_folder_path):
            os.mkdir(data_folder_path)

        with open(f"{data_folder_path}/{station_id}", "w") as f:
            f.write(f"{time.time()}: {produced_power}")

        logger.info(
            f"Recording (not paid) {produced_power} MW for {station_id}")

    def save_produced_energy(self, station_plug_address: str, station_data: tp.Tuple[int, str]) -> None:

        station = PVStation.from_json(ast.literal_eval(station_data[1]))

        produced_sum = self.get_not_paid_produced_power(
            station.get_station_unique_id()) + station.power_generated_MWh
        produced_sum_int = int(produced_sum)

        if produced_sum_int > 0:
            # Pay to producer for generated energy
            if self.transfer_tokens_for_generated_power(produced_sum_int, station_plug_address):
                not_paid_power = produced_sum - produced_sum_int
                # Record how many tokens were transferd to whom
                # self.interface.record_datalog(
                #     f"burned: {total_burned + tons}")
        else:
            not_paid_power = produced_sum

        self.save_not_paid_produced_power(
            station.get_station_unique_id(), not_paid_power)

    def get_last_data(self) -> None:
        threading.Timer(self.config["service"]
                        ["interval"], self.get_last_data).start()
        twins_list = self.get_twins_list()

        if twins_list is None:
            logger.info(f"No existing twins with topics found")
            return

        for station_plug in twins_list:
            station_plug_address = station_plug[1]
            # Fetch datalog from plug PV power station address
            data = self.interface.fetch_datalog(station_plug_address)
            if data is not None:
                # logger.info(
                #     f"Fetched data from pluged PV power station: {data}")
                self.save_produced_energy(station_plug_address, data)


if __name__ == "__main__":
    m = FootprintService()
    threading.Thread(target=m.get_last_data).start()
