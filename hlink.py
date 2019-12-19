#!/usr/bin/env python

# todo:
# - RepositoryをAppとRepoに分離


import argparse
import os
import sys
import json
import sqlite3


class SQL:
    create = """
create table url (
  id int primary key,
  key text,
  url text
);
"""


class Repository:
    db_path = None
    connection = None
    cursor = None

    def __init__(self, db_path):
        self.db_path = db_path
        self.check_db()
        self.connect_db()

    def check_db(self):
        if not os.path.exists(self.db_path):
            sys.stderr.write(f"""\
db file {self.db_path} does not exist.
create one ? [y/n]
> """)
            if input() == "y":
                self.create()
            else:
                raise Exception(
                    f"db file {self.db_path} does not exist and choosed not create")

    def connect_db(self):
        self.connection = sqlite3.connect(self.db_path)
        self.cursor = self.connection.cursor()

    def execute(self, sql):
        return self.curosor.execute(self, sql)

    def executemany(self, sql, it):
        return self.curosor.executemany(self, sql, it)

    def executescript(self, sql):
        return self.cursor.executescript(self, sql)

    def create(self):
        with sqlite3.connect(self.db_path) as con:
            cur = con.cursor()
            cur.executescript(SQL.create)
            con.commit()

    def add(self, keys, url):
        pass


class Command:
    repository = None

    def __init__(self, subparsers, repository):
        self.parser = subparsers.add_parser(self.name,
                                            help=self.__doc__)
        self.register_argument()
        self.parser.set_defaults(handler=self.handler)

        self.repository = repository

    def register_argument(self): pass

    def handler(self, args): pass


class Add(Command):
    "add url"
    name = "add"

    def __init__(self, subparsers):
        super(CommandA, self).__init__(subparsers)

    def register_argument(self):
        self.parser.add_argument("url",  type="str", required=True)

    def handler(self, args, repo):
        keys = input("keys? :")
        num = repo.add(keys, url)
        print(num)


class App:
    repository = None
    conf_dir = os.path.expanduser("~/.hlink")
    conf_path = os.path.join(conf_dir, "config.json")
    conf = dict(
        db_path=os.path.join(conf_dir, "db.sqlite")
    )

    def __init__(self):
        self.check_conf_dir()
        self.read_config()
        self.repository = Repository(self.db_path())

    def db_path(self):
        return self.conf["db_path"]

    def check_conf_dir(self):
        if os.path.exists(self.conf_dir):
            return
        sys.stderr.write(f"""\
config directory {self.conf_dir} does not exists.
create one ? [y/n]
> """)
        if input() == "y":
            self.create_config_dir()
        else:
            raise Exception(
                "config directory does not exits and choosed not create")

    def create_config_dir(self):
        os.mkdir(self.conf_dir)

    def run():
        commands = [CommandA, CommandB]

        parser = argparse.ArgumentParser(description="sample")
        subparsers = parser.add_subparsers()
        for c in commands:
            c(subparsers)

        args = parser.parse_args()
        if hasattr(args, "handler"):
            args.handler(args)
        else:
            parser.print_help()

    def read_config(self):
        if os.path.exists(self.conf_path):
            with open(self.conf_path) as f:
                conf = json.load(f)
            self.conf = dict(self.conf, **conf)
        else:
            with open(self.conf_path, "w") as fp:
                json.dump(self.conf, fp)


if __name__ == "__main__":
    App().run()
