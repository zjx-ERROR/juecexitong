from celery import Celery
from instance import config
from celery.result import AsyncResult
from utils.celery_sqlalchemy_scheduler.session import SessionManager

celery = Celery('tasks', broker=config.BROKER_URL)
celery.config_from_object('instance.config')
celery.conf.update({'beat_dburi':config.beat_dburi})


class CeleryResult(AsyncResult):
    
    def __init__(self, id, backend=None,task_name=None,app=celery, parent=None):
        super(CeleryResult, self).__init__(id=id,backend=backend,task_name=task_name,app=app,parent=parent)


session_manager = SessionManager()
engine, Session = session_manager.create_session(config.beat_dburi)
beat_session = Session()