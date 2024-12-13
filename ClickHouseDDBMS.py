import xml.etree.ElementTree as gfg
import os
import shutil
import yaml

import sys

class ShardingReplicationFileSystem:
    shardsN = None
    replicasN = None
    keepersN = None
    directory = None

    def __init__(self, shardsN: int, replicasN: int, keepersN: int):
        self.shardsN = shardsN
        self.replicasN = replicasN
        self.keepersN = keepersN

        path = os.path.dirname(os.path.abspath(__file__))
        self.directory = os.path.join(path, "clickhouse_config_filesystem")
        if os.path.exists(self.directory):
            shutil.rmtree(self.directory)
        os.makedirs(self.directory)

    def make_keeper_filesystems(self):
        directory = os.path.join(self.directory, "keepers_config_files")
        if os.path.exists(directory):
            shutil.rmtree(directory)
        os.makedirs(directory)
        for i in range(self.keepersN):
            currentKeeperDirectory = os.path.join(directory, f"keeper{i}")
            os.makedirs(currentKeeperDirectory)
            with open(os.path.join(currentKeeperDirectory, "enable-keeper.xml"), 'wb+') as file:
                gfg.ElementTree(self.enable_keeper_xml_file(i)).write(file)
            with open(os.path.join(currentKeeperDirectory, "network-and-logging.xml"), 'wb+') as file:
                gfg.ElementTree(self.network_and_logging_xml_file()).write(file)
    
    def network_and_logging_xml_file(self):
        root = gfg.Element('clickhouse')

        logger = gfg.Element('logger')
        root.append(logger)
        level = gfg.SubElement(logger, 'level')
        level.text = 'debug'
        log = gfg.SubElement(logger, 'log')
        log.text = '/var/log/clickhouse-server/clickhouse-server.log'
        errorlog = gfg.SubElement(logger, 'errorlog')
        errorlog.text = '/var/log/clickhouse-server/clickhouse-server.err.log'
        size = gfg.SubElement(logger, 'size')
        size.text = '1000M'
        count = gfg.SubElement(logger, 'count')
        count.text = '3'

        display_name = gfg.Element('display_name')
        display_name.text = 'clickhouse'
        root.append(display_name)

        listen_host = gfg.Element('listen_host')
        listen_host.text = '0.0.0.0'
        root.append(listen_host)

        http_port = gfg.Element('http_port')
        http_port.text = '8123'
        root.append(http_port)

        tcp_port = gfg.Element('tcp_port')
        tcp_port.text = '9000'
        root.append(tcp_port)

        interserver_http_port = gfg.Element('interserver_http_port')
        interserver_http_port.text = '9009'
        root.append(interserver_http_port)

        return root
    
    def enable_keeper_xml_file(self, serverId: int):
        root = gfg.Element('clickhouse')

        keeper_server = gfg.Element('keeper_server')
        root.append(keeper_server)

        tcp_port = gfg.SubElement(keeper_server, 'tcp_port')
        tcp_port.text = '9181'
        server_id = gfg.SubElement(keeper_server, 'server_id')
        server_id.text = f'{serverId}'
        log_storage_path = gfg.SubElement(keeper_server, 'log_storage_path')
        log_storage_path.text = '/var/lib/clickhouse/coordination/log'
        snapshot_storage_path = gfg.SubElement(keeper_server, 'snapshot_storage_path')
        snapshot_storage_path.text = '/var/lib/clickhouse/coordination/snapshots'

        coordination_settings = gfg.SubElement(keeper_server, 'coordination_settings')
        operation_timeout_ms = gfg.SubElement(coordination_settings, 'operation_timeout_ms')
        operation_timeout_ms.text = '10000'
        session_timeout_ms = gfg.SubElement(coordination_settings, 'session_timeout_ms')
        session_timeout_ms.text = '30000'
        raft_logs_level = gfg.SubElement(coordination_settings, 'raft_logs_level')
        raft_logs_level.text = 'trace'

        raft_configuration = gfg.SubElement(keeper_server, 'raft_configuration')
        for i in range(self.keepersN):
            server = gfg.SubElement(raft_configuration, 'server')
            id = gfg.SubElement(server, 'id')
            id.text = f'{i}'
            hostname = gfg.SubElement(server, 'hostname')
            hostname.text = f'keeper{i}'
            port = gfg.SubElement(server, 'port')
            port.text = '9234'

        return root
    
    def make_chnode_filesystems(self):
        directory = os.path.join(self.directory, "chnodes_config_files")
        if os.path.exists(directory):
            shutil.rmtree(directory)
        os.makedirs(directory)

        k = 0
        for i in range(self.shardsN):
            for j in range(self.replicasN):
                currentKeeperDirectory = os.path.join(directory, f"chnode{k}")
                os.makedirs(currentKeeperDirectory)
                with open(os.path.join(currentKeeperDirectory, "macros.xml"), 'wb+') as file:
                    gfg.ElementTree(self.macros_xml_file(i,j)).write(file)
                with open(os.path.join(currentKeeperDirectory, "network-and-logging.xml"), 'wb+') as file:
                    gfg.ElementTree(self.network_and_logging_xml_file()).write(file)
                with open(os.path.join(currentKeeperDirectory, "remote-servers.xml"), 'wb+') as file:
                    gfg.ElementTree(self.remote_servers_xml_file()).write(file)
                with open(os.path.join(currentKeeperDirectory, "use-keeper.xml"), 'wb+') as file:
                    gfg.ElementTree(self.use_keeper_xml_file()).write(file)
                k+=1

    def use_keeper_xml_file(self):
        root = gfg.Element('clickhouse')

        zookeeper = gfg.Element('zookeeper')
        root.append(zookeeper)

        for i in range(self.keepersN):
            node = gfg.SubElement(zookeeper, 'node')
            node.attrib = {'index':"1"}
            host = gfg.SubElement(node, 'host')
            host.text = f'keeper{i}'
            port = gfg.SubElement(node, 'port')
            port.text = '9181'

        return root
    
    def macros_xml_file(self, shardi: int, replicaj: int):
        root = gfg.Element('clickhouse')

        macros = gfg.Element('macros')
        root.append(macros)

        shard = gfg.SubElement(macros, 'shard')
        shard.text = f'shard_{shardi}'
        replica = gfg.SubElement(macros, 'replica')
        replica.text = f'replica_{replicaj}'

        return root
    
    def remote_servers_xml_file(self):
        root = gfg.Element('clickhouse')

        remote_servers = gfg.Element('remote_servers')
        remote_servers.attrib = {'replace':"true"}
        root.append(remote_servers)

        cluster = gfg.SubElement(remote_servers, f'cluster_{self.shardsN}S_{self.replicasN}R')
  
        secret = gfg.SubElement(cluster, 'secret')
        secret.text = 'mysecretphrase'

        i = 0
        round = 0
        for shardJ in range(self.shardsN):
            shard = gfg.SubElement(cluster, 'shard')
            internal_replication = gfg.SubElement(shard, 'internal_replication')
            internal_replication.text = 'true'
            for replicaK in range(self.replicasN):
                replica = gfg.SubElement(shard, 'replica')
                host = gfg.SubElement(replica, 'host')
                host.text = f'chnode{i}'
                port = gfg.SubElement(replica, 'port')
                port.text = '9000'

                i += 1
        return root

    def make(self):
        self.make_keeper_filesystems()
        self.make_chnode_filesystems()

    def get_directory(self):
        return self.directory
    
    def change_shardsN(self, newV: int):
        self.shardsN = newV

    def change_replicasN(self, newV: int):
        self.replicasN = newV

    def change_keepersN(self, newV: int):
        self.keepersN = newV



class ClickHouseDDBMS:
    SRFS = None
    shardsN = None
    replicasN = None
    keepersN = None
    directory = None

    def __init__(self, shardsN: int, replicasN: int, keepersN: int):
        self.shardsN = shardsN
        self.replicasN = replicasN
        self.keepersN = keepersN
        self.SRFS = ShardingReplicationFileSystem(self.shardsN, self.replicasN, self.keepersN)

    def change_shardsN(self, newV: int):
        self.shardsN = newV
        self.SRFS.change_shardsN(self.shardsN)

    def change_replicasN(self, newV: int):
        self.replicasN = newV
        self.SRFS.change_replicasN(self.replicasN)

    def change_keepersN(self, newV: int):
        self.keepersN = newV
        self.SRFS.change_keepersN(self.keepersN)

    def make_docker_compose_yml_file(self):
        yamlFile = {'services':{}, 'volumes': {}}
        directory = self.SRFS.get_directory()
        for i in range(self.shardsN*self.replicasN):
                yamlFile['services'][f'chnode{i}'] = {
                    'image':"clickhouse",
                    'environment' : {
                        'CLICKHOUSE_USER': "user",
                        'CLICKHOUSE_PASSWORD': "password"},
                    'volumes': [
                        f"chnode{i}_data:/var/lib/clickhouse",
                        f"chnode{i}_logs:/var/log/clickhouse",
                        f"{os.path.join(directory, f"chnodes_config_files/chnode{i}/")}:/etc/clickhouse-server/config.d/",]
                }

        for j in range(self.keepersN):
            yamlFile['services'][f'keeper{j}'] = {
                    'image':"clickhouse",
                    'environment' : {
                        'CLICKHOUSE_USER': "user",
                        'CLICKHOUSE_PASSWORD': "password"},
                    'volumes': [
                        f"keeper{j}_data:/var/lib/clickhouse",
                        f"keeper{j}_logs:/var/log/clickhouse",
                        f"{os.path.join(directory, f"keepers_config_files/keeper{j}/")}:/etc/clickhouse-server/config.d/",]
                }
            yamlFile['services'][f'chnode{i}']

        for key in yamlFile['services'].keys():
            yamlFile['volumes'][f'{key}_data'] = {}
            yamlFile['volumes'][f'{key}_logs'] = {}
        
        with open(os.path.join(directory, f"docker-compose.yml"), 'w+') as file:
            file.write(yaml.safe_dump(yamlFile, default_flow_style=False, width=50, indent=4).replace("''",''))

    def make(self):
        self.SRFS.make()
        self.make_docker_compose_yml_file()
        
def is_intstring(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


if __name__ == "__main__":
    if (len(sys.argv) != 4 or all([is_intstring(i) for i in sys.argv[1:]]) == False):
        print("Creates docker-compose YAML file that will generate shardsN x replicasN total clickhouse servers + keepersN keepers to implement a distributed database managment system:", flush=True)
        print(f"\tpython3 ClickHouseDDBMS.py {'shardsN'} {'replicasN'} {'keepersN'}", flush=True)
        print(f"\t\tshardsN:(int) - numbers of shards the database will be partitioned into", flush=True)
        print(f"\t\treplicasN:(int) - numbers of replications the database will have", flush=True)
        print(f"\t\tkeepersN:(int) - numbers of (zoo)keepers database will have", flush=True)
    else:
        ClickHouseDDBMS(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])).make()

# https://clickhouse.com/docs/en/architecture/horizontal-scaling

# CREATE DATABASE db1 ON CLUSTER cluster_{sys.argv[1]}S_{sys.argv[2]}R;
# CREATE TABLE db1.table1 ON CLUSTER cluster_{sys.argv[1]}S_{sys.argv[2]}R
# (
#     `id` UInt64,
#     `column1` String
# )
# ENGINE = ReplicatedMergeTree('/clickhouse/tables/table1/{shard}','{replica}')
# ORDER BY id;
# -- in one shard:
# INSERT INTO db1.table1 (id, column1) VALUES (1, 'abc');
# -- in a different shard:
# INSERT INTO db1.table1 (id, column1) VALUES (2, 'def');
# SELECT * FROM db1.table1;

# CREATE TABLE db1.table1_dist ON CLUSTER cluster_{sys.argv[1]}S_{sys.argv[2]}R
# (
#     `id` UInt64,
#     `column1` String
# )
# ENGINE = Distributed('cluster_{sys.argv[1]}S_{sys.argv[2]}R', 'db1', 'table1', rand())