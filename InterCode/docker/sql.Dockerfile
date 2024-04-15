FROM mysql

ENV MYSQL_ROOT_PASSWORD="password"

ADD ./data/sql/spider/ic_spider_dbs.sql /docker-entrypoint-initdb.d
# ADD ./data/sql/wikisql/ic_wikisql_dev.sql ./data/sql/bird/ic_bird_dbs.sql ./data/sql/spider/ic_spider_dbs.sql /docker-entrypoint-initdb.d