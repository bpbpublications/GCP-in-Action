from google.cloud import spanner
from talentvoting.common.interfaces.servicelocations import SPANNER_INSTANCE, SPANNER_DATABASE

def get_database():
    "Create a database connection."
    spanner_client = spanner.Client()
    instance = spanner_client.instance(SPANNER_INSTANCE)
    database = instance.database(SPANNER_DATABASE)
    print("Created database connection")
    return database
