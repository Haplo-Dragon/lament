from flask import Flask
import lament


def create_app():
    app = Flask(__name__)
    app.config.from_object(__name__)

    app.config['DEBUG'] = False
    app.config['SECRET_KEY'] = 'SuperSecretKeyForRPGDay'

    # Register blueprints
    app.register_blueprint(lament.lamentApp)

    @app.after_request
    def gnu_terry_pratchett(resp):
        resp.headers.add("X-Clacks-Overhead", "GNU Terry Pratchett")
        return resp

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(port=42000)
