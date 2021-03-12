import os
import pytest
import tempfile
import app as app

# import db classes
from app import User, Conv

# import IntegrityError
from sqlalchemy.exc import IntegrityError


# from course material

@pytest.fixture
def db_handle():
    db_fd, db_fname = tempfile.mkstemp()
    app.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_fname
    app.app.config["TESTING"] = True

    with app.app.app_context():
        app.db.create_all()

    yield app.db

    app.db.session.remove()
    os.close(db_fd)
    os.unlink(db_fname)


def test_user(db_handle):
    """
    class User(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(256), nullable=False)
        email = db.Column(db.String(256), nullable=False)
        pw_hash = db.Column(db.String(256), nullable=False)

        conversations = db.relationship("Conv", back_populates="user")
    """

    ### Test creating
    user = User(username='username',
                email='test@email.com',
                pw_hash='12345')
    db_handle.session.add(user)
    db_handle.session.commit()
    assert User.query.count() == 1

    ### Check the username
    user = User.query.filter_by(username='username').first()
    assert user.username == 'username'

    ### Test that having no username gives an error
    user = User(email='test@email.com',
                pw_hash='12345')
    db_handle.session.add(user)

    # committing now should raise an error
    with pytest.raises(IntegrityError):
        db_handle.session.commit()

    # rollback after error
    db_handle.session.rollback()

    ### Test unique username
    user = User(username='username',
                email='test@email.com',
                pw_hash='12345')
    db_handle.session.add(user)

    # committing now should raise an IntegrityError: UNIQUE constraint failed
    with pytest.raises(IntegrityError):
        db_handle.session.commit()

    # rollback after error
    db_handle.session.rollback()

    ### Test deleting
    # add one more
    user = User(username='username2',
                email='test@email.com',
                pw_hash='12345')
    db_handle.session.add(user)
    db_handle.session.commit()

    # Count should be 2 now
    assert user.query.count() == 2

    # delete
    user = User.query.filter_by(username='username').first()
    db_handle.session.delete(user)
    db_handle.session.commit()

    # deleted?
    assert user.query.count() == 1

def test_conv(db_handle):
    """
    class Conv(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        conv_name = db.Column(db.String(256), unique=True, nullable=False)
        pw_hash = db.Column(db.String(256), nullable=False)

        user = db.relationship("User", back_populates="conversation")
    """
    user = User(username='convUser',
                email='test2@email.com',
                pw_hash='12345')
    db_handle.session.add(user)
    db_handle.session.commit()

    user = User.query.filter_by().first()
    ### Test creating
    conv = Conv(conv_name='conversation',
                pw_hash='12345',
                user=user)
    db_handle.session.add(conv)
    db_handle.session.commit()
    assert Conv.query.count() == 1

    ### Check the username
    conv = Conv.query.filter_by(conv_name='conversation').first()
    assert conv.conv_name == 'conversation'

    ### Check the created_by
    conv = Conv.query.filter_by(created_by=1).first()
    assert conv.created_by == 1

    ### Test that having no conv_name gives an error
    conv = Conv(pw_hash='12345',
                user=user)
    db_handle.session.add(conv)

    # committing now should raise an error
    with pytest.raises(IntegrityError):
        db_handle.session.commit()

    # rollback after error
    db_handle.session.rollback()

    ### Test unique conv_name
    conv = Conv(conv_name='conversation',
                pw_hash='12345',
                user=user)
    db_handle.session.add(conv)

    # committing now should raise an IntegrityError: UNIQUE constraint failed
    with pytest.raises(IntegrityError):
        db_handle.session.commit()

    # rollback after error
    db_handle.session.rollback()

    ### Test deleting
    # add one more
    conv = Conv(conv_name='conversation2',
                pw_hash='12345',
                user=user)
    db_handle.session.add(conv)
    db_handle.session.commit()

    # Count should be 2 now
    assert Conv.query.count() == 2

    # delete
    conv = Conv.query.filter_by(conv_name='conversation2').first()
    db_handle.session.delete(conv)
    db_handle.session.commit()

    # deleted?
    assert Conv.query.count() == 1
