from functools import lru_cache
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from ..log import get_logger
from ..settings import (MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE,
                        MYSQL_CONTAINER_NAME)


class DatabaseManager:
    def __init__(self):
        mysql_connector_str = 'mysql+mysqlconnector'
        mysql_port = '3306'
        engine_credential = "{}://{}:{}@{}:{}/{}".format(mysql_connector_str,
                                                         MYSQL_USER,
                                                         MYSQL_PASSWORD,
                                                         MYSQL_CONTAINER_NAME,
                                                         mysql_port,
                                                         MYSQL_DATABASE)
        self.engine = create_engine(engine_credential,
                                    pool_recycle=3600)

        self.session_factory = sessionmaker(bind=self.engine)
        self.logger = get_logger(__name__)

    def get_session(self):
        return self.session_factory()

    # pylint: disable=broad-except
    def safe_commit(self, session):
        try:
            session.commit()
            self.logger.debug("session committed")
        except Exception:
            session.rollback()
            self.logger.debug("session rolled back")
        finally:
            session.close()
            self.logger.debug("session closed")

    def close_engine(self):
        self.logger.debug("engine closed")
        self.engine.dispose()


@lru_cache(maxsize=1)
def get_database_manager():
    return DatabaseManager()