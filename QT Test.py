import sys

import bs4 as bs
from PyQt5.QtCore import QUrl
from PyQt5.QtWebEngineWidgets import QWebEnginePage
from PyQt5.QtWidgets import QApplication


class Page(QWebEnginePage):
    def __init__(self, url):
        self.app = QApplication(sys.argv)
        QWebEnginePage.__init__(self)
        self.html = ""
        self.loadFinished.connect(self._on_load_finished)
        self.load(QUrl(url))
        self.app.exec_()

    def _on_load_finished(self):
        self.html = self.toHtml(self.Callable)
        print("Load finished")

    def Callable(self, html_str):
        self.html = html_str
        self.app.quit()


def main():
    page = Page(
        "https://www.carnegiehall.org/calendar/2022/09/29/Carnegie-Halls-Opening-Night-Gala-The-Philadelphia-Orchestra-0700PM"
    )
    soup = bs.BeautifulSoup(page.html, "html.parser")
    print(soup)


if __name__ == "__main__":
    main()
