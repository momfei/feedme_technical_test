CREATE SCHEMA IF NOT EXISTS feedme;

CREATE TYPE feedme.ENUM_ITEM_STATUS AS ENUM ('draft', 'served', 'canceled');
CREATE TYPE feedme.ENUM_ORDER_STATUS AS ENUM ('draft', 'completed', 'voided');

CREATE TABLE IF NOT EXISTS feedme.changelogs_raw (
	received_at timestamp DEFAULT CURRENT_TIMESTAMP, 
	log_text TEXT
);

CREATE TABLE IF NOT EXISTS feedme.orders (
	id TEXT, 
	status feedme.ENUM_ORDER_STATUS, 
	total DOUBLE PRECISION, 
	"timestamp" TIMESTAMP, 
	merchant_id BIGINT, 
	v BIGINT
);

CREATE TABLE IF NOT EXISTS feedme.order_items (
	id TEXT, 
	total DOUBLE PRECISION, 
	name TEXT, 
	quantity INT, 
	price DOUBLE PRECISION, 
	status feedme.ENUM_ITEM_STATUS
);


ALTER TABLE feedme.orders 
ADD PRIMARY KEY (id);
