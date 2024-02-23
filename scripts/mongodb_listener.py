import os
import csv
import copy
import json
import pymongo
import psycopg2
import tempfile
from psycopg2 import sql

DB_NAME = "ANXJDF"
COLLECTION_NAME = "Orders"
# MongoDB connection settings
mongo_uri = "YOUR_MONGO_URI"
mongo_client = pymongo.MongoClient(mongo_uri)
mongo_db = mongo_client[DB_NAME]
mongo_collection = mongo_db[COLLECTION_NAME]

# PostgreSQL connection settings
pg_conn_params = {
    "host": "localhost",
    "port": 5432,
    "user": "data_lake",
    "password": "data_lake",
    "database": DB_NAME,
}

pg_conn = psycopg2.connect(**pg_conn_params)

def insert_order_to_psql(pg_cursor, doc):
    this_doc = copy.deepcopy(doc)    

    this_order = {
        "id": str(this_doc["id"]),
        "status": this_doc["status"],
        "total": this_doc["total"],
        "timestamp": this_doc["timestamp"],
        "merchant_id": this_doc["merchantId"],
        "v": this_doc["__v"]
    }

    # Insert order data into PostgreSQL
    pg_cursor.execute(
        sql.SQL("""
                    INSERT INTO feedme.orders (id, status, total, timestamp, merchant_id, v) 
                    VALUES ('{}','{}',{},'{}','{}','{}'); 
                """.format(this_order["id"], this_order["status"], this_order["total"], 
                         this_order["timestamp"], this_order["merchant_id"], this_order["v"]
                    )
               )
    )
    
    this_order_items = this_doc["items"]

    for item in this_order_items:
        item["id"] = str(this_doc["id"])
        # Insert order items into PostgreSQL
        pg_cursor.execute(
            sql.SQL("""INSERT INTO feedme.order_items (id, total, name, quantity, price, status) 
                        VALUES ('{}',{},'{}',{},{},'{}'); """.format(item["id"], item["total"], item["name"], 
                                                 item["quantity"], item["price"], item["status"]
                                                )

                   )
        )
        
        
def update_order_to_psql(pg_cursor, doc):
    this_doc = copy.deepcopy(doc)    

    this_order = {
        "id": str(this_doc["id"]),
        "v": this_doc["__v"]
    }

    # Update order data in PostgreSQL
    pg_cursor.execute(
        sql.SQL("""UPDATE feedme.orders SET v = '{}' WHERE id = '{}'; """.format(this_order["v"], this_order["id"]))
    )
    
    this_order_items = this_doc["items"]

    pg_cursor.execute(
        sql.SQL("""DELETE FROM feedme.order_items WHERE id = '{}';""".format(this_order["id"]))
    )

    for item in this_order_items:
        item["id"] = str(this_doc["id"])
        # Insert or update order items in PostgreSQL
        pg_cursor.execute(
            sql.SQL("""
                        INSERT INTO feedme.order_items (id, total, name, quantity, price, status) 
                        VALUES ('{}',{},'{}',{},{},'{}'); """.format(item["id"], item["total"], item["name"], 
                                                 item["quantity"], item["price"], item["status"]
                                                )

                   )
        )


def sync_mongodb_collection():
    print(f'Start sync-ing mongodb collection ...')
    all_documents = mongo_collection.find()

    order_lists = []
    order_items_list = []

    for doc in all_documents:
        order_lists.append([str(doc["_id"]), doc["status"], doc["total"], 
                             doc["timestamp"], doc["merchantId"], doc["__v"]
                           ])

        this_order_items = doc["items"]

        for item in this_order_items:
            order_items_list.append([doc["_id"], item["total"], item["name"], 
                                     item["quantity"], item["price"], item["status"]
                                    ])
    orders_csv_path = ''
    order_items_csv_path = ''
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".csv", newline='', encoding='utf-8') as orders_temp_file:        
        csv_writer = csv.writer(orders_temp_file, delimiter=";")
        csv_writer.writerows(order_lists)
        orders_csv_path = orders_temp_file.name

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".csv", newline='', encoding='utf-8') as order_items_temp_file:
        csv_writer = csv.writer(order_items_temp_file, delimiter=";")
        csv_writer.writerows(order_items_list)
        order_items_csv_path = order_items_temp_file.name

    with pg_conn.cursor() as pg_cursor:
        with open(orders_csv_path, 'r', encoding="UTF-8") as temp_file:
            pg_cursor.copy_expert(f"COPY feedme.orders FROM STDIN DELIMITER ';' ", temp_file)

        with open(order_items_csv_path, 'r', encoding="UTF-8") as temp_file:
            pg_cursor.copy_expert(f"COPY feedme.order_items FROM STDIN DELIMITER ';' ", temp_file) 

        pg_conn.commit()

    os.remove(orders_csv_path)
    os.remove(order_items_csv_path) 
    print(f'Synced mongodb collection. Total {len(order_lists)} orders.  Total {len(order_items_list)} order items.')    

#Initial mongodb collection sync
sync_mongodb_collection()

# Change Stream settings
pipeline = [
    {"$match": {"operationType": {"$in": ["insert", "update", "delete"]}}}
]

with mongo_collection.watch(pipeline) as stream:
    print("Watching for changes in MongoDB...")

    for change in stream:
        # Handle the change event
        operation_type = change["operationType"]
                
        with pg_conn.cursor() as pg_cursor:
            #Insert change logs into raw table
            pg_cursor.execute(
                sql.SQL("""INSERT INTO feedme.changelogs_raw (log_text) 
                            VALUES ('{}');""".format(json.dumps(change, default=str)))
            )

            if operation_type == "insert" or operation_type == "update":
                # Update / Insert order data into PostgreSQL
                if operation_type == "insert":
                    document = change.get("fullDocument", {})
                    document["id"] = str(change["documentKey"]["_id"])
                    insert_order_to_psql(pg_cursor, document) 
                else:
                    document = change.get("updateDescription", {})
                    document = document['updatedFields']
                    document["id"] = str(change["documentKey"]["_id"])
                    update_order_to_psql(pg_cursor, document)
            elif operation_type == "delete":                
                # Delete order data in PostgreSQL
                pg_cursor.execute(
                    sql.SQL("""DELETE FROM feedme.orders WHERE id = '{}';""".format(str(change["documentKey"]["_id"])))
                )

                # Delete order items in PostgreSQL
                pg_cursor.execute(
                    sql.SQL("""DELETE FROM feedme.order_items WHERE id = '{}';""".format(str(change["documentKey"]["_id"])))
                )
                
            pg_conn.commit()

# Close connections
pg_conn.close()
mongo_client.close()
