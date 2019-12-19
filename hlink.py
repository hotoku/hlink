#!/usr/bin/env python

# todo:
# - RepositoryをAppとRepoに分離


import argparse
import os
import sys
import json
import sqlite3
import logging


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
    @staticmethod
    def search_by_key(key):
        return f"""
select * from url
where key like '{key}';
"""


class DB:
    path = None
    con = None

    def __init__(self, path):
        self.path = path
        self.check_db()
        self.con = sqlite3.connect(self.path)
        self.con.row_factory = sqlite3.Row

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
        logging.debug(sql)
        cur = self.con.cursor()
        rows = cur.execute(sql)
        return [row for row in rows]

    def executemany(self, sql, it):
        logging.debug(sql)
        cur = self.con.cursor()
        try:
            ret = cur.executemany(sql, it)
            self.con.commit()
            return ret
        except Exception as e:
            self.con.rollback()
            raise e
        finally:
            cur.close()

    def executescript(self, sql):
        logging.debug(sql)
        cur = self.con.cursor()
        try:
            ret = cur.executescript(sql)
            self.con.commit()
            return ret
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
        return self.db.executemany(SQL.insert_url,
                                   [(key, url)])

    def search(self, keys):
        like = "%" + "%".join(keys) + "%"
        ret = self.db.execute(SQL.search_by_key(like))
        return [dict(id=row["id"],
                     key=row["key"],
                     url=row["url"]) for row in ret]


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
    name = "a"

    def __init__(self, subparsers):
        super(Add, self).__init__(subparsers)

    def register_argument(self):
        self.parser.add_argument("url")

    def handler(self, args, repo):
        keys = input("keys? :")
        url = args.url
        num = repo.add(keys, url)
        print(num)


class Search(Command):
    "search by key"
    name = "s"

    def __init__(self, subparsers):
        super(Search, self).__init__(subparsers)

    def register_argument(self):
        self.parser.add_argument("keys", nargs="*")

    def handler(self, args, repo):
        vals = repo.search(args.keys)
        if len(vals) == 0:
            sys.stderr.write("no match\n")
        elif len(vals) == 1:
            url = vals[0]["url"]
            App.open(url)
        else:
            for v in vals:
                print("{0[id]}: {0[key]}, {0[url]}".format(v))


class App:
    repository = None
    conf_dir = os.path.expanduser("~/.hlink")
    conf_path = os.path.join(conf_dir, "config.json")
    conf = dict(
        db_path=os.path.join(conf_dir, "db.sqlite"),
        log_path="/tmp/hlink.log"
    )

    def __init__(self):
        self.check_conf_dir()
        self.read_config()
        self.repository = Repository(self.db_path())
        self.setup_logger()

    def setup_logger(self):
        logging.basicConfig(
            format="[%(levelname)s]%(asctime)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            level=logging.DEBUG,
            filename=self.log_path()
        )

    def log_path(self):
        return self.conf["log_path"]

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
        commands = [Add, Search]

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

    @staticmethod
    def open(file):
        os.system(f"open {file}")


if __name__ == "__main__":
    App().run()
