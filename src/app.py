__version__ = 1.2
import sys
import logging

from api import Api


def setup_log():
    file_handler = logging.FileHandler(filename="log.log",
                                       mode='w',
                                       encoding='utf-8')
    
    stdout_handler = logging.StreamHandler(sys.stdout)

    logging.basicConfig(handlers=[file_handler, stdout_handler],
                        level=logging.DEBUG,
                        format='%(name)s - %(levelname)s - %(message)s')
    logging.debug("Setup was initialized")


if __name__ == "__main__":
    setup_log()

    try:
        # Initializing application and serving in host
        app = Api()
        app.serve()

    except Exception as globalEx:
        logging.error(globalEx)
        print(globalEx)
