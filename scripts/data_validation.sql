select ROUND(SUM(total)::NUMERIC, 2)::double precision from feedme.order_items;

select count(*) from feedme.orders;

select sum(quantity)
from feedme.order_Items;