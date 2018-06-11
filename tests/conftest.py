import pytest
import ethan_portfolio


@pytest.fixture
def app():
    """Create a new app for each test."""
    app = ethan_portfolio.create_app()
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'TestingKey'
    return app


@pytest.fixture
def client(app):
    """Test client for the created app."""
    return app.test_client()
