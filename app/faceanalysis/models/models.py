# pylint: disable=too-few-public-methods
import os
from passlib.apps import custom_app_context as pwd_context
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.schema import ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (Column, String, Float, Text,
                        Integer, DateTime, UniqueConstraint)
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)
from .database_manager import get_database_manager

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(32), unique=True, index=True)
    password_hash = Column(String(128))

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def generate_auth_token(self, expiration=None):
        token = os.environ['TOKEN_SECRET_KEY']
        expiration = expiration or int(
            os.environ['DEFAULT_TOKEN_EXPIRATION_SECS'])
        serializer = Serializer(token, expires_in=expiration)
        return serializer.dumps({'id': self.id})

    @staticmethod
    def verify_auth_token(token):
        serializer = Serializer(os.environ['TOKEN_SECRET_KEY'])
        try:
            data = serializer.loads(token)
        except SignatureExpired:
            return None
        except BadSignature:
            return None
        db = get_database_manager()
        session = db.get_session()
        user = session.query(User).filter(User.id == data['id']).first()
        session.close()
        return user


class ImageStatus(Base):
    __tablename__ = 'imagestatuses'

    id = Column(Integer, primary_key=True)
    img_id = Column(String(50), unique=True)
    status = Column(String(50))
    error_msg = Column(String(50), default=None)


class Image(Base):
    __tablename__ = 'images'

    id = Column(Integer, primary_key=True)
    img_id = Column(String(50), unique=True)
    feature_mappings = relationship('FeatureMapping', back_populates='img')
    time_created = Column(DateTime(timezone=True), server_default=func.now())


class FeatureMapping(Base):
    __tablename__ = 'featuremappings'

    id = Column(Integer, primary_key=True)
    img_id = Column(String(50), ForeignKey('images.img_id'))
    features = Column(Text)
    time_created = Column(DateTime(timezone=True), server_default=func.now())
    img = relationship('Image', back_populates='feature_mappings')


class Match(Base):
    __tablename__ = 'matches'

    id = Column(Integer, primary_key=True)
    this_img_id = Column(String(50), ForeignKey('images.img_id'))
    that_img_id = Column(String(50), ForeignKey('images.img_id'))
    distance_score = Column(Float)
    time_created = Column(DateTime(timezone=True), server_default=func.now())
    this_img = relationship('Image', foreign_keys=[this_img_id])
    that_img = relationship('Image', foreign_keys=[that_img_id])
    __table_args__ = (UniqueConstraint(
        'this_img_id', 'that_img_id', name='_this_that_uc'),)


def init_models(database_engine):
    Base.metadata.create_all(database_engine)


def delete_models(database_engine):
    Base.metadata.drop_all(database_engine)

# pylint: enable=too-few-public-methods
