import sqlite3
from pandas.io.sql import read_sql


class DbDriver:

    def __init__(self, driver, database, server=None, user=None, password=None, port=None):
        if "SQLite" in driver:
            self._conn = sqlite3.connect(database)

        self.cursor = self._conn.cursor()

    def get_df_from_table(self, table, where=None):
        if where is None:
            return read_sql('SELECT * FROM {}'.format(table), self._conn).replace(r'^\s*$', "nan", regex=True)
        else:
            return read_sql('SELECT * FROM {} WHERE {}'.format(table, where), self._conn).replace(
                r'^\s*$', "nan", regex=True)

    def get_df_from_ljoin(self, left, right, column_name, and_condition=None, select_list=None):
        if select_list is not None:
            select = ""
            for i in range(len(select_list)):
                select += str(select_list[i]) + ("" if i == len(select_list) - 1 else ", ")
            if and_condition is None:
                return read_sql('SELECT {} FROM {} A LEFT JOIN {} B ON A.{}=B.{} WHERE B.{} IS NULL'.format(
                    select, left, right, column_name, column_name, column_name), self._conn).replace(r'^\s*$', "nan",
                                                                                                     regex=True)
            else:
                return read_sql('SELECT {} FROM {} A LEFT JOIN {} B ON A.{}=B.{} WHERE B.{} IS NULL AND ({})'.format(
                    select, left, right, column_name, column_name, column_name, and_condition), self._conn).replace(
                    r'^\s*$', "nan", regex=True)
        else:
            if and_condition is None:
                return read_sql('SELECT * FROM {} A LEFT JOIN {} B ON A.{}=B.{} WHERE B.{} IS NULL'.format(
                    left, right, column_name, column_name, column_name), self._conn).replace(r'^\s*$', "nan",
                                                                                             regex=True)
            else:
                return read_sql('SELECT * FROM {} A LEFT JOIN {} B ON A.{}=B.{} WHERE B.{} IS NULL AND ({})'.format(
                    left, right, column_name, column_name, column_name, and_condition), self._conn).replace(
                    r'^\s*$', "nan", regex=True)

    def get_df_from_query(self, query):
        return read_sql(query, self._conn).replace(r'^\s*$', "nan", regex=True)

    def get_values_from_table(self, column, table, where=None):
        values = []
        if where is None:
            self.cursor.execute("SELECT {} FROM {}".format(column, table))
        else:
            self.cursor.execute("SELECT {} FROM {} WHERE {}".format(column, table, where))

        for row in self.cursor:
            values.append(str(row).strip("(',) "))

        return values

    def update_cell(self, table, column, value, where, commit=True):
        self.cursor.execute("UPDATE {} SET {} = '{}' WHERE {}".format(table, column, value, where))
        if commit:
            self._conn.commit()

    def insert_list(self, table, column_list:  list, values_list: list, commit=True):
        if len(column_list) == len(values_list):
            columns = ""
            values = ""
            for i in range(len(column_list)):
                columns += column_list[i] + ("" if i == len(column_list) - 1 else ", ")
                values += "'{}'".format(values_list[i]) + ("" if i == len(column_list) - 1 else ", ")
            self.cursor.execute("INSERT INTO {} ({}) VALUES ({})".format(table, columns, values))
            if commit:
                self._conn.commit()
        else:
            raise Exception("Columns list and values list had to be equals in length")

    def query(self, query: str):
        result = ""
        self.cursor.execute(query)

        if 'SELECT' in query:
            for row in self.cursor:
                result += "{} ;".format(row)

        return result
