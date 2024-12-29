import logging
import sys
from multiprocessing import Process, Queue

import bs4 as bs
from PyQt5.QtCore import QUrl
from PyQt5.QtWebEngineWidgets import QWebEnginePage
from PyQt5.QtWidgets import QApplication

logger = logging.getLogger(__name__)

g_app = None


class Qt5WebPage(QWebEnginePage):
    """
    https://stackoverflow.com/questions/42147601/pyqt4-to-pyqt5-mainframe-deprecated-need-fix-to-load-web-pages
    """

    def __init__(self, url):
        global g_app
        if not g_app:
            g_app = QApplication(sys.argv)
        QWebEnginePage.__init__(self)
        self.html = ""
        self.loadFinished.connect(self.on_load_finished)
        self.load(QUrl(url))
        g_app.exec_()

    def on_load_finished(self):
        self.toHtml(self.marshal_results)
        logger.info("Load finished")

    def marshal_results(self, html_str):
        self.html = html_str
        g_app.quit()


class Qt5RenderedSoup:
    """
    Class to return a soup from web pages where it is necessary to render in a browser before the content is available.
    """

    def __init__(self, url):
        self.url = url

    def get_soup(self):
        page = Qt5WebPage(self.url)
        soup = bs.BeautifulSoup(page.html, "html.parser")
        logger.info(soup)
        return soup
