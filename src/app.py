__version__ = 0.2
import logging

from src.api import Api


def setup_log():
    logging.basicConfig(filename="log.log",
                        level=logging.DEBUG,
                        filemode='w',
                        format='%(name)s - %(levelname)s - %(message)s')
    logging.debug("Setup was initialized")


if __name__ == "__main__":
    setup_log()

    try:
        # Initializing application and serving
        app = Api()
        app.serve()

    except Exception as globalEx:
        logging.error(globalEx)
        print(globalEx)
