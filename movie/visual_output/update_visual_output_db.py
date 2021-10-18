import json
import base64
import subprocess
from subprocess import PIPE, STDOUT

import couchdb

NAMESPACE = "gusXXXXXX"
DB_PORT = "5984"
EXPECTED_INPUT_DB_NAME = "expected_input"
VISUAL_OUTPUT_DB_NAME = "visual_output"


class Database:
    def __init__(self, db_name):
        couchdb_server = couchdb.Server(f"http://localhost:{DB_PORT}/")
        self.configure_couchdb_credentials(couchdb_server)
        self.potentially_create_db(couchdb_server, db_name)
        self._db_name = db_name
        self._db = couchdb_server[db_name]

    def configure_couchdb_credentials(self, couchdb_server):
        couchdb_user = "admin"
        command = [
            "kubectl", "get", "secret", "db-couchdb", '-o',
            'jsonpath="{.data.adminPassword}"'
        ]
        get_password = subprocess.Popen(command, stdout=PIPE, stderr=STDOUT)
        couchdb_password, stderr = get_password.communicate()
        couchdb_password = base64.b64decode(couchdb_password)
        couchdb_server.resource.credentials = (
            couchdb_user, couchdb_password.decode("utf-8"))

    def potentially_create_db(self, couchdb_server, db_name):
        if db_name not in couchdb_server:
            couchdb_server.create(db_name)

    def cleanup_docs(self):
        for doc_id in self._db:
            self._db.delete(self._db[doc_id])

    def bulk_update_docs(self):
        pass


class ExpectedInputDatabase(Database):
    def bulk_update_docs(self):
        filename = f"{self._db_name}.json"
        with open(filename, "r") as json_file:
            visual_outputs = json.load(json_file)
            for visual_output in visual_outputs:
                visual_output["_id"] = f'{visual_output["current_plan_item"]}:{visual_output["semantic_expression"]}'
            print(
                f"Replacing data in the '{self._db_name}' database with contents in '{filename}'"
            )
            self._db.update(visual_outputs)


class VisualOutputDatabase(Database):
    def bulk_update_docs(self):
        filename = f"{self._db_name}.json"
        with open(filename, "r") as json_file:
            visual_outputs = json.load(json_file)
            for visual_output in visual_outputs:
                visual_output["_id"] = visual_output["semantic_expression"]
            print(
                f"Replacing data in the '{self._db_name}' database with contents in '{filename}'"
            )
            self._db.update(visual_outputs)


def main():
    try:
        expected_input_db = ExpectedInputDatabase(EXPECTED_INPUT_DB_NAME)
        expected_input_db.cleanup_docs()
        expected_input_db.bulk_update_docs()
        visual_output_db = VisualOutputDatabase(VISUAL_OUTPUT_DB_NAME)
        visual_output_db.cleanup_docs()
        visual_output_db.bulk_update_docs()
    except ConnectionRefusedError as e:
        print(
            f"ConnectionRefusedError: {e}"
            f"\n    Make sure that you have forwarded the CouchDB port ({DB_PORT}) of the namespace"
            f"\n    '{NAMESPACE}' before running this script."
            f"\n    To forward the port {DB_PORT}, you can e.g. run the following command:"
            f"\n    kubectl port-forward svc/db-svc-couchdb {DB_PORT} -n {NAMESPACE} &"
        )


if __name__ == "__main__":
    main()
