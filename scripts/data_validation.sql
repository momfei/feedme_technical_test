--Sales: Aggregate sum of order items' total.
select ROUND(SUM(total)::NUMERIC, 2)::double precision from feedme.order_items;

--Quantity: Aggregate count of orders.
select count(*) from feedme.orders;

--Item Quantity: Aggregate sum of order items' quantity.
select sum(quantity)
from feedme.order_Items;