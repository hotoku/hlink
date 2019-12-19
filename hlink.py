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
drop table if exists url;
create table url (
  id integer primary key autoincrement,
  key text,
  url text
);
"""
    insert_url = """
insert into url(key, url) values (
  ?, ?
);
"""


class DB:
    path = None
    con = None

    def __init__(self, path):
        self.path = path
        self.check_db()
        self.con = sqlite3.connect(self.path)

    def check_db(self):
        if not os.path.exists(self.path):
            sys.stderr.write(f"""\
db file {self.path} does not exist.
create one ? [y/n]
> """)
            if input() == "y":
                self.create()
            else:
                raise Exception(
                    f"db file {self.path} does not exist and choosed not create")

    def create(self):
        with sqlite3.connect(self.path) as con:
            cur = con.cursor()
            cur.executescript(SQL.create)
            con.commit()

    def execute(self, sql):
        cur = self.con.cursor()
        try:
            cur.execute(sql)
            self.con.commit()
        except Exception as e:
            self.con.rollback()
            raise e
        finally:
            cur.close()

    def executemany(self, sql, it):
        cur = self.con.cursor()
        try:
            cur.executemany(sql, it)
            self.con.commit()
        except Exception as e:
            self.con.rollback()
            raise e
        finally:
            cur.close()

    def executescript(self, sql):
        cur = self.con.cursor()
        try:
            cur.executescript(sql)
            self.con.commit()
        except Exception as e:
            self.con.rollback()
            raise e
        finally:
            cur.close()


class Repository:
    db = None

    def __init__(self, db_path):
        self.db = DB(db_path)

    def add(self, key, url):
        self.db.executemany(SQL.insert_url,
                            [(key, url)])


class Command:
    def __init__(self, subparsers):
        self.parser = subparsers.add_parser(self.name,
                                            help=self.__doc__)
        self.register_argument()
        self.parser.set_defaults(handler=self.handler)

    def register_argument(self): pass

    def handler(self, args, repo): pass


class Add(Command):
    "add url"
    name = "add"

    def __init__(self, subparsers):
        super(Add, self).__init__(subparsers)

    def register_argument(self):
        self.parser.add_argument("url")

    def handler(self, args, repo):
        keys = input("keys? :")
        url = args.url
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

    def run(self):
        commands = [Add]

        parser = argparse.ArgumentParser(description="sample")
        subparsers = parser.add_subparsers()
        for c in commands:
            c(subparsers)

        args = parser.parse_args()
        if hasattr(args, "handler"):
            args.handler(args, self.repository)
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
