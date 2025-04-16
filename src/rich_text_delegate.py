from PyQt5.QtWidgets import QStyledItemDelegate
from PyQt5.QtGui import QTextDocument
from PyQt5.QtCore import QSize, Qt, QRectF


class RichTextDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        text = index.data(Qt.DisplayRole)
        doc = QTextDocument()
        doc.setHtml(text)
        doc.setTextWidth(option.rect.width())  # constrain width

        # Clip painting to cell bounds
        painter.save()
        painter.setClipRect(option.rect)
        painter.translate(option.rect.topLeft())
        doc.drawContents(
            painter, QRectF(0, 0, option.rect.width(), option.rect.height())
        )
        painter.restore()

    def sizeHint(self, option, index):
        text = index.data(Qt.DisplayRole)
        doc = QTextDocument()
        doc.setHtml(text)
        doc.setTextWidth(option.rect.width())  # ensures wrapping calculation
        return QSize(int(doc.idealWidth()), int(doc.size().height()))
