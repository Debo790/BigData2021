from subprocess import PIPE,Popen
import shlex
import configparser
import sys
import os
import time
sys.path.append(os.getcwd())


def create(host_name,database_name,user_name,database_password, port):
    
    command = 'createdb -h {0} -U {1} -p {2} {3}'\
              .format(host_name,user_name, port,database_name)

    print("Creating Database...")
    print(command)
    command = shlex.split(command)
    p = Popen(command, shell=False,stdin=PIPE,stdout=PIPE,stderr=PIPE, env={'PGPASSWORD':database_password})


def restore_table(host_name,database_name,user_name,database_password, port):

    command = 'pg_restore -h {0} -d {1} -U {2} -p {3} ./tmp/bdt2021_dump'\
              .format(host_name,database_name,user_name, port)

    print("Restoring data...")
    print(command)
    
    command = shlex.split(command)

    p = Popen(command, shell=False,stdin=PIPE,stdout=PIPE,stderr=PIPE, env={'PGPASSWORD':database_password})


def main():
    config = configparser.ConfigParser()
    config.read('conf/config.ini')
    
    create(config['postgresql']['host'],
                    config['postgresql']['database'],
                    config['postgresql']['user'],
                    config['postgresql']['password'],
                    config['postgresql']['port'])
    time.sleep(3)
    restore_table(config['postgresql']['host'],
                    config['postgresql']['database'],
                    config['postgresql']['user'],
                    config['postgresql']['password'],
                    config['postgresql']['port'])


if __name__ == "__main__":
    main()