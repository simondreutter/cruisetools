from pathlib import Path

from qgis.PyQt.QtCore import *

from qgis.PyQt.QtWidgets import QWidget
from qgis.PyQt.QtWidgets import QGridLayout
from qgis.PyQt.QtWidgets import QLabel
from qgis.PyQt.QtWidgets import QToolBox
from qgis.PyQt.QtWidgets import QTextEdit

from qgis.PyQt.QtGui import QFont
from qgis.PyQt.QtGui import QIcon


class ReadmeWindow(QWidget):
    """README GUI."""

    def __init__(self, readme_text):
        """Initialize ReadmeWindow."""
        super().__init__()
        # icon path
        self.icon_path = Path(__file__).resolve().parent.parent / 'icons'

        # set window size
        self.resize(600, 570)

        # set window icon
        icon = QIcon(str(self.icon_path / 'icon.png'))
        self.setWindowIcon(icon)

        # set windows title
        self.setWindowTitle('Readme')

        # create layout
        layout = QGridLayout()

        # create title, big font, centered
        title = QLabel()
        title.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        title_font = QFont('Default', 14, QFont.Weight.Bold)
        title.setFont(title_font)

        # add title to layout
        layout.addWidget(title, 0, 0)

        # create version text, centered under title
        version = QLabel()
        version.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        version_font = QFont('Default', 10)
        version.setFont(version_font)

        # add version to layout
        layout.addWidget(version, 1, 0)

        # create toolbox
        toolbox = QToolBox()

        # toolbox styleSheet
        toolbox_style = '''
                            QToolBox::tab {
                                border: 1px solid #C4C4C3;
                                font-size: 9pt;
                            }
                            QToolBox::tab:selected {
                                background-color: RGB(200, 0, 200);
                            }
                        '''

        # set toolbox style
        toolbox.setStyleSheet(toolbox_style)

        # add toolbox to layout
        layout.addWidget(toolbox, 2, 0)

        # plot readme text in text blocks
        blocks = readme_text.split('\n## ')

        # handle title and version block
        for line in blocks[0].splitlines():
            line = line.strip()
            if line.startswith('# '):
                title_text = line.replace('# ', '')
            elif line.startswith('*v'):
                version_text = line.replace('*', '')

        # set version and title text
        title.setText(title_text)
        version.setText(version_text)

        # create toolbox content from text blocks
        # idx = 0
        for idx, block in enumerate(blocks[1:]):
            # get block title and content
            block_title, markdown = block.split('\n', 1)

            # create text field
            text = QTextEdit()

            # make text field read only
            text.setReadOnly(True)

            # add content
            # html = self.markdown(markdown) # DEPRECATED
            # text.setHtml(html) # DEPRECATED
            text.setMarkdown(markdown)

            # add text to toolbox
            toolbox.addItem(text, block_title)

            # get block icon
            icon = self.get_icon(block_title)

            # set block icon
            toolbox.setItemIcon(idx, icon)

            # idx = idx + 1

        # set window layout
        self.setLayout(layout)

    def get_icon(self, title):
        """Get Icon for Readme Dialog.

        Parameters
        ----------
        title : str
            menu title

        Returns
        -------
        icon : QIcon
            icon to be displayed in the toolbox

        """
        title = title.lower()
        if title == 'bathymetry':
            icon = QIcon(str(self.icon_path / 'bathymetry_menu.png'))
        elif title == 'contour':
            icon = QIcon(str(self.icon_path / 'create_contours.png'))
        elif title == 'vector':
            icon = QIcon(str(self.icon_path / 'vector_menu.png'))
        elif title == 'planning':
            icon = QIcon(str(self.icon_path / 'planning_menu.png'))
        elif title == 'logging':
            icon = QIcon(str(self.icon_path / 'log_position.png'))
        else:
            icon = QIcon(str(self.icon_path / 'icon_grey.png'))

        return icon
