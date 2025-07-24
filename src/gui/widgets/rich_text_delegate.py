from PyQt5.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem
from PyQt5.QtGui import QTextDocument, QPainter
from PyQt5.QtCore import QSize, Qt, QRectF, QModelIndex


class RichTextDelegate(QStyledItemDelegate):
    """A delegate to render HTML content inside table cells."""

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionViewItem,
        index: QModelIndex,
    ) -> None:
        """Paint HTML content for a given index."""
        text = index.data(Qt.DisplayRole) or ""
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

    def sizeHint(
        self, option: QStyleOptionViewItem, index: QModelIndex
    ) -> QSize:
        """Return size of rendered HTML content."""
        text = index.data(Qt.DisplayRole) or ""
        doc = QTextDocument()
        doc.setHtml(text)
        doc.setTextWidth(option.rect.width())  # ensures wrapping calculation
        return QSize(int(doc.idealWidth()), int(doc.size().height()))
